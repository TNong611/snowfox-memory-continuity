"""L2→L3: trim oldest from summary.md (if >100KB, trim to 90KB),
LLM-compress each taken section (skip empty/dedup), write to long_term.md.
No timestamps in L3. Cascade if L3 >50KB → retire.
"""
import json, os, re, subprocess, sys
from mem_config import L2_MAX_KB as MAX_KB, L2_KEEP_KB as KEEP_KB, L3_MAX_KB, L3_KEEP_KB

HH = os.environ.get("HERMES_HOME") or os.environ["USERPROFILE"] + "/AppData/Local/hermes"
SUM = HH + "/memories/summary.md"
L3 = HH + "/memories/long_term.md"
AUTH = HH + "/auth.json"
SCRIPT = HH + "/scripts/mem_compress.py"


def parse(content):
    lines = content.split("\n")
    hdr = ""; secs = []; cur = []; inHdr = True
    for line in lines:
        if inHdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"; continue
            inHdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur: secs.append("\n".join(cur))
            cur = [line]
        else: cur.append(line)
    if cur: secs.append("\n".join(cur))
    return hdr, secs


def _get_deepseek_key() -> str:
    """API key 多源回退：env → .env → auth.json。"""
    k = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if k:
        return k
    env_file = HH + "/.env"
    try:
        for line in open(env_file, encoding="utf-8"):
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY=") and len(line) > 20:
                k = line.split("=", 1)[1].strip("\"'")
                if k:
                    return k
    except Exception:
        pass
    if os.path.exists(AUTH):
        try:
            auth = json.load(open(AUTH, "r"))
            pool = auth.get("credential_pool", {}).get("deepseek", [])
            if pool and pool[0].get("value"):
                return pool[0]["value"]
        except Exception:
            pass
    raise RuntimeError("DEEPSEEK_API_KEY not found (env/.env/auth.json)")


def _llm_summarize(text: str) -> str:
    """进一步压缩 L2 摘要 → L3 长期记忆，跳过空结果。"""
    api_key = _get_deepseek_key()
    prompt = (
        "你是一个长期记忆蒸馏器。下面是一段已经压缩过的对话摘要。\n"
        "请进一步提炼为极简版本，只保留最重要的跨会话事实、配置决策和结论。\n"
        "移除所有临时上下文、讨论过程、仅单次有效的信息。\n"
        "要求：中文，不超过150字。\n"
        "如果内容为空或全部无关，请只回复（空）\n\n"
        + text
    )

    import urllib.request
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=28).read())
    result = resp["choices"][0]["message"]["content"].strip()
    return result


def _llm_summarize_batch(sections: list[str]) -> list[str]:
    """一次请求压缩多段 L2 摘要 → 逐段 L3 条目（避免 N 次串行 API 拖垮 30s 超时）。"""
    api_key = _get_deepseek_key()
    numbered = "\n\n---\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(sections))
    if len(numbered) > 12000:
        numbered = numbered[:12000] + "\n…[truncated]"
    prompt = (
        "你是一个长期记忆蒸馏器。下面有多段已经压缩过的对话摘要，每段以 [编号] 开头。\n"
        "请逐段进一步提炼为极简版本，只保留最重要的跨会话事实、配置决策和结论。\n"
        "移除所有临时上下文、讨论过程、仅单次有效的信息。\n"
        "要求：\n"
        "- 严格按相同编号逐段输出：[1] 摘要 [2] 摘要 ...（每段独立一行）\n"
        "- 每段中文不超过150字\n"
        "- 某段内容为空或全部无关时，输出 [N]（空）\n"
        "- 不要添加原文没有的内容\n\n"
        + numbered
    )

    import urllib.request
    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    raw = json.loads(urllib.request.urlopen(req, timeout=28).read())
    result = raw["choices"][0]["message"]["content"].strip()

    blocks: dict[int, list[str]] = {}
    cur = -1
    for line in result.split("\n"):
        m = re.match(r"^\[(\d+)\]\s*(.*)$", line.strip())
        if m:
            cur = int(m.group(1)) - 1
            blocks.setdefault(cur, []).append(m.group(2))
        elif cur >= 0:
            blocks[cur].append(line.strip())
    out: list[str] = []
    for i in range(len(sections)):
        out.append(" ".join(blocks.get(i, [])).strip())
    if not any(out):
        # 编号解析完全失败：退化为整段原文（调用方再逐段去重）
        return [result]
    return out


def _extract_topic(text: str) -> str:
    """从摘要首行提取 L3 条目标题（去符号/编号前缀，太短回退 summary）。"""
    for line in text.strip().split("\n"):
        line = re.sub(r"^[-•*#\s]+", "", line.strip())
        line = re.sub(r"^同\s*\[\d+\][：:]?", "", line).strip()
        if line:
            return line[:60] if len(line) >= 4 else "summary"
    return "summary"


def _load_l3_sections() -> list[str]:
    if not os.path.exists(L3):
        return []
    content = open(L3, "r", encoding="utf-8").read()
    _, secs = parse(content)
    return secs


def _is_duplicate(new_text: str, existing: list[str]) -> bool:
    """检查是否与已有 L3 内容重复（归一化后比较）。"""
    norm = re.sub(r"\s+", " ", new_text).strip().lower()
    if len(norm) < 10:
        return False
    for sec in existing:
        # skip timestamp prefix + "同[N]：" pattern
        body = re.sub(r"^## .+\n", "", sec, count=1).strip()
        body = re.sub(r"^同\[\d+\][：:]", "", body)
        enorm = re.sub(r"\s+", " ", body).strip().lower()
        if norm == enorm or norm in enorm or enorm in norm:
            return True
    return False


def _hard_cleanup():
    """If L3 is already > limit after cascade, do a brute-force trim of oldest entries."""
    if not os.path.exists(L3):
        return
    sz = os.path.getsize(L3) / 1024
    target = L3_KEEP_KB * 1024
    if sz <= L3_MAX_KB:
        return
    content = open(L3, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs:
        return
    # remove oldest until ≤ target
    keep = list(secs)
    current = len(content.encode("utf-8"))
    for sec in secs:
        if current <= target:
            break
        sbytes = len(sec.encode("utf-8"))
        keep.pop(0)
        current -= sbytes
    # write remaining + cascade to retire
    open(L3, "w", encoding="utf-8").write("".join(keep))
    print(f"  L3 hard-cleanup: removed {len(secs) - len(keep)} entries, now {os.path.getsize(L3)/1024:.1f}KB (target ≤{L3_KEEP_KB}KB)")
    _trigger_retire()


def _trigger_retire():
    if not os.path.exists(L3):
        return
    if os.path.getsize(L3) / 1024 > L3_MAX_KB:
        script = HH + "/scripts/mem_retire.py"
        if os.path.exists(script):
            r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=30)
            out = (r.stdout or "").strip()[:200]
            print(f"  [cascade->retire] {out}")
            if r.returncode != 0:
                print(f"  [cascade error] {(r.stderr or '')[:200]}")


def consolidate():
    if not os.path.exists(SUM):
        print("  L2: not found"); return
    sz = os.path.getsize(SUM) / 1024
    if sz <= MAX_KB:
        print(f"  L2: {sz:.1f}KB ≤ {MAX_KB}KB, no action needed (target ≤{KEEP_KB}KB)"); return

    content = open(SUM, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs:
        print("  L2: no sections"); return

    # Remove oldest sections until remaining ≤ KEEP_KB
    keep_size = int(KEEP_KB * 1024)
    taken = []; keep = list(secs)
    remaining_size = sz * 1024
    for sec in secs:
        sec_bytes = len(sec.encode("utf-8"))
        if remaining_size - sec_bytes <= keep_size:
            break
        taken.append(sec)
        remaining_size -= sec_bytes
        keep.pop(0)

    if not taken:
        print(f"  L2: {sz:.1f}KB over limit but no single section fits removal target"); return

    # Write remaining back to L2
    open(SUM, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    removed_bytes = sum(len(s.encode("utf-8")) for s in taken)
    print(f"  L2: {sz:.1f}KB > {MAX_KB}KB → trimmed {len(taken)} entries ({removed_bytes/1024:.1f}KB)")

    # --- L2→L3 further compression ---
    existing_l3 = _load_l3_sections()
    added = 0
    skipped_empty = 0
    skipped_dup = 0

    # 批量压缩（一次请求，防 N 次串行 API 拖垮 30s 超时）；失败时逐段回退
    try:
        compressed_list = _llm_summarize_batch(taken)
        batch_ok = True
    except Exception as e:
        print(f"  [LLM batch error] {e}; falling back to per-section")
        compressed_list = []
        batch_ok = False

    for i, s in enumerate(taken):
        if batch_ok:
            compressed = compressed_list[i] if i < len(compressed_list) else s
            if not compressed:
                skipped_empty += 1
                continue
        else:
            try:
                compressed = _llm_summarize(s)
            except Exception as e:
                print(f"  [LLM error] {e}; appending raw")
                compressed = s

        # Skip empty
        cleaned = compressed.replace("（空）", "").replace("(空)", "").strip()
        if len(cleaned) < 15:
            skipped_empty += 1
            continue

        # Skip LLM self-marked duplicate (同[N])
        if re.match(r"^同\s*\[\d+\]", cleaned):
            skipped_dup += 1
            continue

        # Skip duplicate
        if _is_duplicate(cleaned, existing_l3):
            skipped_dup += 1
            continue

        # Append without timestamp — topic from first meaningful line
        topic = _extract_topic(cleaned)
        entry = f"## {topic}\n{cleaned}\n"
        with open(L3, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        existing_l3.append(cleaned)
        added += 1

    ns = os.path.getsize(SUM) / 1024
    print(f"  L2→L3: added {added}, skipped [{skipped_empty} empty, {skipped_dup} dup], summary.md now={ns:.1f}KB (target ≤{KEEP_KB}KB)")

    # Cascade to retire if L3 over limit
    _trigger_retire()

    # Hard cleanup L3 if still too big after cascade
    _hard_cleanup()


if __name__ == "__main__":
    consolidate()
