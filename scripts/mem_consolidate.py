"""L2->L3: consolidate oldest sections from summary.md to long_term.md."""
import os
from datetime import datetime
HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
SUM = HH + "/memories/summary.md"
L3 = HH + "/memories/long_term.md"
MAX_KB = 100; OVER_KB = 10

def parse(content):
    lines = content.split("\n")
    hdr = ""; secs = []; cur = []; inHdr = True
    for line in lines:
        if inHdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"; continue
            else: inHdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur: secs.append("\n".join(cur))
            cur = [line]
        else: cur.append(line)
    if cur: secs.append("\n".join(cur))
    return hdr, secs

def consolidate():
    if not os.path.exists(SUM):
        print("  L2: not found"); return
    sz = os.path.getsize(SUM) / 1024
    if sz <= MAX_KB:
        print(f"  L2: {sz:.1f}KB/{MAX_KB}KB OK"); return
    content = open(SUM, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs: print("  L2: no sections"); return
    target = int(OVER_KB * 1024)
    removed = 0; keep = list(secs); taken = []
    for sec in secs:
        if removed >= target: break
        taken.append(sec); removed += len(sec.encode("utf-8"))
        keep.pop(0)
    open(SUM, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    # Append to long_term.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(L3):
        with open(L3, "w", encoding="utf-8") as f:
            f.write("# L3 Long-term — 长期记忆\n\n---\n\n")
    with open(L3, "a", encoding="utf-8") as f:
        for s in taken:
            f.write(f"\n## {now} | consolidated-from-L2\n\n{s}\n\n---\n")
    ns = os.path.getsize(SUM) / 1024
    print(f"  L2->L3: moved {len(taken)} entries ({removed/1024:.1f}KB), remaining {ns:.1f}KB")
    print("  OK L2 consolidation")

if __name__ == "__main__":
    consolidate()