"""L2->L3: trim oldest from summary.md (if >100KB, trim to 90KB), write to long_term.md.
Cascade: if long_term.md >50KB -> run retire.
"""
import os, subprocess, sys
from datetime import datetime
from mem_config import L2_MAX_KB as MAX_KB, L2_KEEP_KB as KEEP_KB

HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
SUM = HH + "/memories/summary.md"
L3 = HH + "/memories/long_term.md"


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


def _trigger_retire():
    p = HH + "/memories/long_term.md"
    if not os.path.exists(p): return
    if os.path.getsize(p) / 1024 > 50:
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

    # Write remaining back
    open(SUM, "w", encoding="utf-8").write(hdr + "\n".join(keep))

    # Append taken to long_term.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    removed_bytes = sum(len(s.encode("utf-8")) for s in taken)
    if not os.path.exists(L3):
        with open(L3, "w", encoding="utf-8") as f:
            f.write("# L3 Long-term — 长期记忆\n\n---\n\n")
    with open(L3, "a", encoding="utf-8") as f:
        for s in taken:
            f.write(f"\n## {now} | consolidated-from-L2\n\n{s}\n\n---\n")

    ns = os.path.getsize(SUM) / 1024
    print(f"  L2: {sz:.1f}KB > {MAX_KB}KB → trimmed {len(taken)} entries ({removed_bytes/1024:.1f}KB)")
    print(f"  L2→L3: moved {len(taken)} entries, summary.md now={ns:.1f}KB (target ≤{KEEP_KB}KB)")
    _trigger_retire()


if __name__ == "__main__":
    consolidate()
