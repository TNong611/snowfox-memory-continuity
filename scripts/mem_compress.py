"""L1->L2: trim oldest sections from recent.md head, write to summary.md."""
import os
from datetime import datetime
HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L1 = HH + "/memories/recent.md"
SUM = HH + "/memories/summary.md"
MAX_KB = 50; OVER_KB = 5

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

def compress():
    if not os.path.exists(L1):
        print("  L1: not found"); return
    sz = os.path.getsize(L1) / 1024
    if sz <= MAX_KB:
        print(f"  L1: {sz:.1f}KB/{MAX_KB}KB OK"); return
    content = open(L1, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs: print("  L1: no sections"); return
    target = int(OVER_KB * 1024)
    removed = 0; keep = list(secs); taken = []
    for sec in secs:
        if removed >= target: break
        taken.append(sec); removed += len(sec.encode("utf-8"))
        keep.pop(0)
    open(L1, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    # Append to summary.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUM, "a", encoding="utf-8") as sf:
        sf.write(f"\n## {now} | compressed-from-L1\n\n")
        for s in taken: sf.write(s + "\n")
        sf.write("---\n")
    ns = os.path.getsize(L1) / 1024
    print(f"  L1->L2: removed {len(taken)} entries ({removed/1024:.1f}KB), remaining {ns:.1f}KB")
    print("  OK L1 compression")

if __name__ == "__main__":
    compress()