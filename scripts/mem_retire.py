"""L3->L4: retire oldest sections from long_term.md to archive.md."""
import os
from datetime import datetime
HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L3 = HH + "/memories/long_term.md"
L4 = HH + "/memories/archive.md"
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

def retire():
    if not os.path.exists(L3):
        print("  L3: not found"); return
    sz = os.path.getsize(L3) / 1024
    if sz <= MAX_KB:
        print(f"  L3: {sz:.1f}KB/{MAX_KB}KB OK"); return
    content = open(L3, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs: print("  L3: no sections"); return
    target = int(OVER_KB * 1024)
    removed = 0; keep = list(secs); taken = []
    for sec in secs:
        if removed >= target: break
        taken.append(sec); removed += len(sec.encode("utf-8"))
        keep.pop(0)
    open(L3, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    # Append to archive.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(L4):
        with open(L4, "w", encoding="utf-8") as f:
            f.write("# L4 Archive — 退役记忆归档\n\n---\n\n")
    with open(L4, "a", encoding="utf-8") as f:
        for s in taken:
            f.write(f"\n## {now} | retired-from-L3\n\n{s}\n\n---\n")
    ns = os.path.getsize(L3) / 1024
    print(f"  L3->L4: retired {len(taken)} entries ({removed/1024:.1f}KB), remaining {ns:.1f}KB")
    print("  OK L3 retirement")

if __name__ == "__main__":
    retire()