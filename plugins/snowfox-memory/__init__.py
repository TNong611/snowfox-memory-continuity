"""SnowFox 五级记忆插件（自包含组装 + post_llm_call 写入）。
组装顺序：USER → L4 → F0 → L3 → L2 → L1（不含 SOUL，SOUL 已是系统提示）。
post_llm_call 在每次回复后立即写入 recent.md。
"""
import logging, re, time, traceback
from pathlib import Path
from datetime import datetime
from typing import Any

logger = logging.getLogger("snowfox-memory")

def _h(): return Path.home() / "AppData/Local/hermes"
def _m(): return _h() / "memories"

def _on_plugin_load():
    logger.info("[snowfox] loaded (order: USER-L4-F0-L3-L2-L1, post_llm)")

_LAST_SESSION_END_ID: str = ""

def _read_or(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def _rebuild_assembly():
    base = _h(); m = _m()
    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f"<!-- SnowFox Memory Assembly | built: {build_ts} -->")
    parts.append("")
    # 组装顺序：USER → L4 → F0 → L3 → L2 → L1
    s = _read_or(m / "user.md")
    if s: parts.append(f"## USER\n{s}")
    s = _read_or(m / "archive.md")
    if s: parts.append(f"## L4\n{s}")
    s = _read_or(m / "fixed.md")
    if s: parts.append(f"## F0\n{s}")
    s = _read_or(m / "long_term.md")
    if s: parts.append(f"## L3\n{s}")
    l2c = _read_or(m / "summary.md")
    if l2c:
        secs = l2c.split("\n## ")
        kept = []; total = 0; limit = 90 * 1024
        for sec in reversed(secs):
            st = (secs[0] if sec is secs[0] else "## " + sec)[:150]
            bs = len(st.encode("utf-8"))
            if total + bs > limit and total > 0: break
            kept.insert(0, st); total += bs
        if kept: parts.append("## L2\n" + "\n".join(kept))
    s = _read_or(m / "recent.md")
    if s: parts.append(f"## L1\n{s}")
    text = "\n\n".join(parts)
    try:
        (m / "_assembled_context.md").write_text(text, encoding="utf-8")
        (m / "_assembly_version.txt").write_text(build_ts, encoding="utf-8")
        logger.info(f"[snowfox] assembly rebuilt: {len(text)}B")
    except Exception as e:
        logger.error(f"[snowfox] assembly write failed: {e}")

def _fingerprint(text: str) -> str:
    # Use isalnum() to support CJK + alphanumeric (vs re.sub that strips Chinese)
    return ''.join(c for c in text.strip() if c.isalnum())[:40].lower()

def _last_entry_fp(p: Path) -> str:
    if not p.exists(): return ""
    secs = p.read_text(encoding="utf-8", errors="replace").split("\n## ")
    if len(secs) < 2: return ""
    fp = _fingerprint(secs[-1])
    if fp: return fp
    # Fallback: if fingerprint is empty (e.g. pure emoji), hash first 100 chars of the entry
    return str(hash(secs[-1][:100]))

def _build_entry(user_msg: str, asst_msg: str, session_id: str, pending: bool = False) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    status = " | pending" if pending else ""
    asst = "_等待回复..._" if pending else asst_msg
    pending_suffix = " | pending_" if pending else ""
    return f"## {ts} | session={session_id}{status}\n\n### User\n\n{user_msg}\n\n### Assistant\n\n{asst}\n\n---\n_雪狐记录 | session={session_id}{pending_suffix}\n"

def _write_recent(user_msg: str, asst_msg: str, session_id: str):
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg):
        logger.debug("[snowfox] skipped duplicate write to recent.md")
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, asst_msg, session_id))
    logger.info("[snowfox] wrote to recent.md")

def _write_pending(user_msg: str, session_id: str):
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg): return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, "", session_id, pending=True))

def _cleanup_pending(user_msg: str):
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    fp = _fingerprint(user_msg)
    content = p.read_text(encoding="utf-8", errors="replace")
    secs = content.split("\n## ")
    kept = [secs[0]]; changed = False
    for sec in secs[1:]:
        if "pending" in sec and fp in _fingerprint(sec):
            changed = True; continue
        kept.append(sec)
    if changed:
        p.write_text("\n## ".join(kept), encoding="utf-8")

def _last_turn_from_db(session_id: str) -> tuple[str, str] | None:
    dbp = _h() / "state.db"
    if not dbp.exists(): return None
    try:
        import sqlite3
        db = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
        msgs = db.execute("SELECT id, role, content FROM messages WHERE session_id=? AND role IN (?,?) ORDER BY id", (session_id, "user", "assistant")).fetchall()
        db.close()
    except Exception: return None
    lu = None; la = None
    for _, r, c in msgs:
        if r == "user" and c: lu = c; la = None
        elif r == "assistant" and c and lu is not None: la = c
    return (lu, la) if lu and la else None

def _on_pre_llm_call(session_id="", task_id="", turn_id="", conversation_history=None, **kw):
    if not session_id or not conversation_history: return
    lu = None; la = None; pu = None
    for msg in conversation_history:
        r = msg.get("role", ""); c = msg.get("content", "")
        if c is None: continue
        if isinstance(c, list):
            c = "\n".join(p.get("text","") for p in c if isinstance(p,dict) and p.get("type")=="text")
        sc = str(c).strip()
        if r == "user" and sc:
            if lu is not None: la = None
            lu = sc; pu = sc
        elif r == "assistant" and sc and lu is not None:
            la = sc; pu = None
    if lu and la:
        _cleanup_pending(lu); _write_recent(lu, la, session_id)
    if pu:
        _write_pending(pu, session_id)
    _rebuild_assembly()

def _on_post_llm_call(response_text="", session_id="", **kw):
    """回复生成后立即写入 recent.md + 重建 assembly。"""
    if not session_id or not response_text: return
    # 从 pre_llm_call 已保存的 user 消息中找待完成的 pair
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    content = p.read_text(encoding="utf-8", errors="replace")
    if "pending" in content:
        # 替换 pending 为完整对话
        secs = content.split("\n## ")
        for i, sec in enumerate(secs):
            if "pending" in sec:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                secs[i] = sec.replace("_等待回复..._", response_text).replace(" | pending", "").replace("_雪狐记录 | session=", f" | assistant_at={ts}\n\n---\n_雪狐记录 | session=")
                break
        p.write_text("\n## ".join(secs), encoding="utf-8")
        _rebuild_assembly()
        logger.info("[snowfox] post_llm: updated pending -> complete")

def _on_session_end(session_id="", completed=False, **kw):
    global _LAST_SESSION_END_ID
    if not session_id or not completed or session_id == _LAST_SESSION_END_ID: return
    result = _last_turn_from_db(session_id)
    if result:
        _write_recent(result[0], result[1], session_id)
        _LAST_SESSION_END_ID = session_id
        _rebuild_assembly()

def register(ctx):
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)
    logger.info("[snowfox] hooks: pre_llm, post_llm, session_end")
    _rebuild_assembly()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("snowfox-memory: USER-L4-F0-L3-L2-L1 assembly + post_llm")