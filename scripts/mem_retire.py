"""L3->L4: trim oldest from long_term.md (if >50KB, trim to 45KB), write to archive.md.
No further cascade (L4 is unlimited).
"""
import os
from datetime import datetime
from mem_config import L3_MAX_KB as MAX_KB, L3_KEEP_KB as KEEP_KB

HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L3 = HH + "/memories/long_term.md"
ARC = HH + "/memories/archive.md"


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


def retire():
    if not os.path.exists(L3):
        print("  L3: not found"); return
    sz = os.path.getsize(L3) / 1024
    if sz <= MAX_KB:
        print(f"  L3: {sz:.1f}KB ≤ {MAX_KB}KB, no action needed (target ≤{KEEP_KB}KB)"); return

    content = open(L3, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs:
        print("  L3: no sections"); return

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
        print(f"  L3: {sz:.1f}KB over limit but no single section fits removal target"); return

    # Write remaining back
    open(L3, "w", encoding="utf-8").write(hdr + "\n".join(keep))

    # Append taken to archive.md
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    removed_bytes = sum(len(s.encode("utf-8")) for s in taken)
    if not os.path.exists(ARC):
        with open(ARC, "w", encoding="utf-8") as f:
            f.write("# L4 Archive — 归档仓库\n\n---\n\n")
    with open(ARC, "a", encoding="utf-8") as f:
        for s in taken:
            f.write(f"\n## {now} | retired-from-L3\n\n{s}\n\n---\n")

    ns = os.path.getsize(L3) / 1024
    print(f"  L3: {sz:.1f}KB > {MAX_KB}KB → trimmed {len(taken)} entries ({removed_bytes/1024:.1f}KB)")
    print(f"  L3→L4: moved {len(taken)} entries, long_term.md now={ns:.1f}KB (target ≤{KEEP_KB}KB)")

    # 重建 L4 语义索引
    try:
        import subprocess, sys
        subprocess.run([sys.executable, HH + "/scripts/l4_index.py"],
                       cwd=HH, capture_output=True, text=True, timeout=30)
    except Exception as e:
        print(f"  [l4_index auto-rebuild]: {e}")


if __name__ == "__main__":
    retire()
