"""SnowFox 五级记忆插件（自包含组装 + post_llm_call 写入 + 超限即压缩）。
组装顺序：USER → F0 → L3 → L2 → L1（不含 L4，L4 使用语义索引检索）。
post_llm_call 在每次回复后立即写入 recent.md。
写入后检查大小，超 50KB 当场触发 L1→L2 压缩。
"""
import logging, re, time, traceback, subprocess, sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Ensure mem_config is importable regardless of plugin loader's CWD
_SCRIPTS_DIR = Path.home() / "AppData/Local/hermes/scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from mem_config import L1_MAX_KB as MAX_L1_KB, L2_MAX_KB as MAX_L2_KB, L3_MAX_KB as MAX_L3_KB, ASSEMBLY_BUDGET_KB
from mem_assembly import assemble_budgeted, clip

logger = logging.getLogger("snowfox-memory")

# 纪要化截断上限：User 保留前 300 字符，Assistant 保留前 600 字符
_USER_LIMIT = 300
_ASST_LIMIT = 600

def _h(): return Path.home() / "AppData/Local/hermes"
def _m(): return _h() / "memories"

def _on_plugin_load():
    logger.info("[snowfox] loaded (order: USER-F0-L3-L2-L1, post_llm, inline+startup compress, L4=semantic)")

def _run_script(name: str) -> str | None:
    """Run a memory script by name (mem_compress/consolidate/retire), return stdout first line."""
    script = _h() / f"scripts/{name}.py"
    if not script.exists():
        logger.warning(f"[snowfox] script not found: {script}")
        return None
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip()
        if r.returncode != 0:
            logger.error(f"[snowfox] {name} failed: {(r.stderr or '')[:200]}")
            return None
        return out.split("\n")[0] if out else "OK"
    except Exception as e:
        logger.error(f"[snowfox] {name} exception: {e}")
        return None

def _startup_check():
    """On plugin load, check all levels and compress any over-limit files."""
    # L3 check first (deepest first — so cascade chain runs top-down)
    lp = _m() / "long_term.md"
    if lp.exists() and lp.stat().st_size / 1024 > MAX_L3_KB:
        logger.info(f"[snowfox] startup: L3 over {MAX_L3_KB}KB, running retire...")
        r = _run_script("mem_retire")
        if r: logger.info(f"[snowfox] startup: L3 retire → {r}")

    # L2 check
    sp = _m() / "summary.md"
    if sp.exists() and sp.stat().st_size / 1024 > MAX_L2_KB:
        logger.info(f"[snowfox] startup: L2 over {MAX_L2_KB}KB, running consolidate...")
        r = _run_script("mem_consolidate")
        if r: logger.info(f"[snowfox] startup: L2 consolidate → {r}")

    # L1 check (does cascade too)
    rp = _m() / "recent.md"
    if rp.exists() and rp.stat().st_size / 1024 > MAX_L1_KB:
        logger.info(f"[snowfox] startup: L1 over {MAX_L1_KB}KB, running compress...")
        r = _run_script("mem_compress")
        if r: logger.info(f"[snowfox] startup: L1 compress → {r}")

_LAST_SESSION_END_ID: str = ""

def _read_or(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def _rebuild_assembly(l4_hits=None):
    """预算制组装：F0/USER 全量，L1/L2/L3 按预算裁剪，L4 检索结果预算内注入。
    曾因全量注入 154KB（≈5万 token）导致 DeepSeek 240s 断流，预算制限制注入量。"""
    m = _m()
    text = assemble_budgeted(m, budget_kb=ASSEMBLY_BUDGET_KB, l4_hits=l4_hits)
    try:
        (m / "_assembled_context.md").write_text(text, encoding="utf-8")
        (m / "_assembly_version.txt").write_text(datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"), encoding="utf-8")
        logger.info(f"[snowfox] assembly rebuilt (budget): {len(text)}B = {len(text)/1024:.1f}KB")
    except Exception as e:
        logger.error(f"[snowfox] assembly write failed: {e}")

def _compress_l1_if_overflow():
    """Check recent.md size; if > MAX_L1_KB, run mem_compress.py immediately."""
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    sz_kb = p.stat().st_size / 1024
    if sz_kb <= MAX_L1_KB:
        return
    script = _h() / "scripts/mem_compress.py"
    if not script.exists():
        logger.warning(f"[snowfox] compress script not found: {script}")
        return
    logger.info(f"[snowfox] L1 overflow: {sz_kb:.1f}KB > {MAX_L1_KB}KB, compressing...")
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            ns = p.stat().st_size / 1024 if p.exists() else 0
            logger.info(f"[snowfox] L1 compressed: {sz_kb:.1f}KB -> {ns:.1f}KB")
        else:
            logger.error(f"[snowfox] L1 compress failed: {r.stderr[:200]}")
    except Exception as e:
        logger.error(f"[snowfox] L1 compress exception: {e}")

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

# 系统注入黑名单：Hermes 平台生成的英文合成消息，不属于真实用户输入
_SYSTEM_INJECT_MARKERS = (
    "review the conversation above and update the skill library",
    "consider saving to memory if appropriate",
    "a pass that does nothing is a missed learning opportunity",
    "target shape of the library",
    "has the user revealed things about themselves",
    "be active — most sessions",
)

def _is_system_inject(text: str) -> bool:
    """判断消息是否为平台系统注入（skill 复盘/记忆保存提示等）。"""
    t = text.strip()
    if not t:
        return True
    tl = t.lower()
    for marker in _SYSTEM_INJECT_MARKERS:
        if marker in tl:
            return True
    return False

def _l4_search(query: str) -> list:
    """L4 语义检索：以 query 检索 archive.md（TF-IDF），失败静默返回空。"""
    if not query:
        return []
    try:
        sys.path.insert(0, str(_h() / "scripts"))
        from l4_search import search as _search
        return _search(query, top_k=5)
    except Exception as e:
        logger.debug(f"[snowfox] l4 search skipped: {e}")
        return []

def _cleanup_stale_pending(max_age_h: float = 24.0):
    """删除超过 max_age_h 仍未补全的 pending 条目（无效记录，不占预算）。"""
    p = _m() / "recent.md"
    if not p.exists(): return
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        secs = content.split("\n## ")
        kept = [secs[0]]; removed = 0; now = time.time()
        for sec in secs[1:]:
            if "| pending" not in sec:
                kept.append(sec); continue
            m = re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", sec)
            if not m:
                kept.append(sec); continue
            try:
                ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                kept.append(sec); continue
            if now - ts > max_age_h * 3600:
                removed += 1
                continue
            kept.append(sec)
        if removed:
            p.write_text("\n## ".join(kept), encoding="utf-8")
            logger.info(f"[snowfox] cleaned {removed} stale pending entries")
    except Exception as e:
        logger.error(f"[snowfox] stale pending cleanup failed: {e}")

def _build_entry(user_msg: str, asst_msg: str, session_id: str, pending: bool = False) -> str:
    """纪要化条目：User/Assistant 全文截断后写入（stock Hermes 会话历史自带全文，
    L1 只存结构化纪要，避免双份冗余占窗口）。"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    status = " | pending" if pending else ""
    asst = "_等待回复..._" if pending else clip(asst_msg, _ASST_LIMIT)
    pending_suffix = " | pending_" if pending else ""
    u = clip(user_msg, _USER_LIMIT)
    return f"## {ts} | session={session_id}{status} | 纪要\n\n**User**: {u}\n\n**Assistant**: {asst}\n\n---\n_雪狐记录 | session={session_id}{pending_suffix}\n"

def _write_recent(user_msg: str, asst_msg: str, session_id: str):
    if _is_system_inject(user_msg): return
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg):
        logger.debug("[snowfox] skipped duplicate write to recent.md")
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, asst_msg, session_id))
    logger.info("[snowfox] wrote to recent.md")
    _compress_l1_if_overflow()

def _write_pending(user_msg: str, session_id: str):
    if _is_system_inject(user_msg): return
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg): return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, "", session_id, pending=True))
    _compress_l1_if_overflow()

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
    _cleanup_stale_pending()
    lu = None; la = None; pu = None
    for msg in conversation_history:
        r = msg.get("role", ""); c = msg.get("content", "")
        if c is None: continue
        src = msg.get("source") or {}
        if isinstance(src, dict) and src.get("kind") and src["kind"] != "user":
            continue  # 平台合成消息（skill 注入/cron 提醒等）不记入纪要
        if isinstance(c, list):
            c = "\n".join(p.get("text","") for p in c if isinstance(p,dict) and p.get("type")=="text")
        sc = str(c).strip()
        if r == "user" and sc:
            if _is_system_inject(sc):
                continue  # 系统注入指令（如 skill 复盘提示）不记入纪要
            if lu is not None: la = None
            lu = sc; pu = sc
        elif r == "assistant" and sc and lu is not None:
            la = sc; pu = None
    if lu and la:
        _cleanup_pending(lu); _write_recent(lu, la, session_id)
    if pu:
        _write_pending(pu, session_id)
    # L4 语义检索：以本 turn 用户消息为 query，预算内注入组装
    l4_hits = _l4_search(lu) if lu else []
    _rebuild_assembly(l4_hits=l4_hits)
    _compress_l1_if_overflow()  # pre_llm 返回 override 后 post_llm/session_end 不触发，这里兜底

    # Return override_messages to replace session DB history with assembled memory.
    # Strip SnowFox internal markers before sending to LLM.
    asm = _m() / "_assembled_context.md"
    if asm.exists():
        assembled_content = asm.read_text(encoding="utf-8", errors="replace")
        # 剥离首行 built 时间戳注释：每次重建都变，保留会让 prompt 前缀全失效
        # （与 DSH snowfox-inject.mjs 一致），缓存命中率被拖到 0~65%。
        assembled_content = re.sub(r'^<!-- SnowFox Memory Assembly \| built: [^\n]* -->\r?\n?', '', assembled_content)
        # Remove _雪狐记录 lines and leading --- that separate entries
        cleaned = re.sub(r'\n?---\n_雪狐记录[^\n]*\n?', '\n', assembled_content)
        cleaned = re.sub(r'\n?---\n_雪狐记录[^\n]*_\n?', '\n', cleaned)
        # Also clean up any orphaned empty lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        combined = (
            f"{cleaned}\n\n"
            f"---\n\n"
            f"## Current Turn\n\n"
            f"{kw.get('user_message', '')}"
        )
        return {"override_messages": [{"role": "user", "content": combined}]}
    return None

def _on_post_llm_call(response_text="", session_id="", **kw):
    """回复生成后立即写入 recent.md + 重建 assembly + 超限压缩。"""
    if not session_id or not response_text: return
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    content = p.read_text(encoding="utf-8", errors="replace")
    if "pending" in content:
        secs = content.split("\n## ")
        for i, sec in enumerate(secs):
            if "pending" in sec and session_id in sec:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                secs[i] = sec.replace("_等待回复..._", response_text).replace(" | pending", "").replace("_雪狐记录 | session=", f" | assistant_at={ts}\n\n---\n_雪狐记录 | session=")
                break
        p.write_text("\n## ".join(secs), encoding="utf-8")
        _rebuild_assembly()
        _compress_l1_if_overflow()
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
    _startup_check()  # catch any over-limit files from previous session

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("snowfox-memory: USER-L4-F0-L3-L2-L1 assembly + post_llm + inline-compress")
