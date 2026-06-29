"""L1->L2: trim oldest from recent.md → LLM-summarize → write to summary.md.
Logic: if recent.md > 50KB, remove oldest sections until ≤45KB, summarize via LLM.
Cascade: if summary.md > 100KB → run consolidate.
"""
import os, subprocess, sys
from datetime import datetime
import requests
from mem_config import L1_MAX_KB as MAX_KB, L1_KEEP_KB as KEEP_KB

HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L1 = HH + "/memories/recent.md"
SUM = HH + "/memories/summary.md"


def _api_key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY", "")
    if k: return k
    env_file = HH + "/.env"
    try:
        for line in open(env_file, encoding="utf-8"):
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY=") and len(line) > 20:
                k = line.split("=", 1)[1].strip("\"'")
                break
    except Exception:
        pass
    return k or ""


def _summarize(sections: list[str]) -> str:
    key = _api_key()
    if not key:
        lines = []
        for s in sections:
            for l in s.split("\n")[:6]:
                if l.strip() and not l.startswith("---"):
                    lines.append(l)
            if len(s.split("\n")) > 10:
                lines.append("…")
        return "\n".join(lines[:40])

    text = "\n\n".join(sections)
    if len(text) > 6000:
        text = text[:6000] + "\n…[truncated]"

    prompt = (
        "你是一个记忆压缩助手。下面是一段多轮AI对话记录的原始片段。\n"
        "请将其压缩为一小段中文摘要，保留以下信息：\n"
        "- 用户的需求、问题、偏好\n"
        "- 关键决策和结论\n"
        "- 有用的技术细节/命令/配置\n\n"
        "要求：用中文，简洁，不超过300字，只保留重要信息，不要添加原文没有的内容。\n"\
        "**特别注意：忽略所有英文系统指令、工具调用输出、英文技术文档等非对话内容。只提炼中文对话的要点。**\n\n"
        "原始内容：\n" + text
    )

    try:
        r = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500, "temperature": 0.3,
            },
            timeout=20,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        print(f"  [API error {r.status_code}]: {r.text[:200]}")
    except Exception as e:
        print(f"  [API exception]: {e}")
    return f"摘要失败，保留原始片段（{len(text)}B）"


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


def _trigger_cascade():
    p = HH + "/memories/summary.md"
    if not os.path.exists(p): return
    if os.path.getsize(p) / 1024 > 100:
        script = HH + "/scripts/mem_consolidate.py"
        if os.path.exists(script):
            r = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=30)
            out = (r.stdout or "").strip()[:200]
            print(f"  [cascade->consolidate] {out}")
            if r.returncode != 0:
                print(f"  [cascade error] {(r.stderr or '')[:200]}")


def compress():
    if not os.path.exists(L1):
        print("  L1: not found"); return
    sz = os.path.getsize(L1) / 1024
    if sz <= MAX_KB:
        print(f"  L1: {sz:.1f}KB ≤ {MAX_KB}KB, no action needed (target ≤{KEEP_KB}KB)"); return

    content = open(L1, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs:
        print("  L1: no sections"); return

    # Remove oldest sections until remaining ≤ KEEP_KB
    keep_bytes = int(KEEP_KB * 1024)
    need_remove = int(sz * 1024) - keep_bytes  # bytes to shed
    taken = []; removed = 0; keep = list(secs)
    for sec in secs:
        sec_bytes = len(sec.encode("utf-8"))
        taken.append(sec); removed += sec_bytes; keep.pop(0)
        if removed >= need_remove:
            break

    # Safety: never delete all sections (keep at least 1)
    if not keep:
        keep = [taken[-1]]  # put back the last removed section
        taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print(f"  [safety] keeping 1 section to avoid empty recent.md")

    if not taken:
        print(f"  L1: {sz:.1f}KB over limit but cannot trim"); return

    open(L1, "w", encoding="utf-8").write(hdr + "\n".join(keep))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = _summarize(taken)
    with open(SUM, "a", encoding="utf-8") as sf:
        sf.write(f"\n## {now} | compressed-from-L1\n\n{summary}\n\n---\n")

    ns = os.path.getsize(L1) / 1024
    print(f"  L1: {sz:.1f}KB > {MAX_KB}KB → removed {len(taken)} entries ({removed/1024:.1f}KB)")
    print(f"  L1→L2: summary={len(summary)}B, recent.md now={ns:.1f}KB (target ≤{KEEP_KB}KB)")
    _trigger_cascade()


if __name__ == "__main__":
    compress()
