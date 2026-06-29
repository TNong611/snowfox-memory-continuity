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
    if not os.path.exists(AUTH):
        raise RuntimeError("auth.json not found")
    auth = json.load(open(AUTH, "r"))
    return auth["credential_pool"]["deepseek"][0]["value"]


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
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    result = resp["choices"][0]["message"]["content"].strip()
    return result


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
        # strip timestamp prefix
        body = re.sub(r"^## .+\n", "", sec, count=1).strip()
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
    if os.path.getsize(L3) / 1024 > 50:
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

    for s in taken:
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

        # Skip duplicate
        if _is_duplicate(cleaned, existing_l3):
            skipped_dup += 1
            continue

        # Append without timestamp — just topic header
        # Derive topic from first line or use a simple prefix
        topic = "consolidated"
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
