"""SnowFox 全级内存维护 — 按 L1→L2→L3→L4 依次检查并压缩。"""
import os, subprocess, sys

HH = os.environ.get("HERMES_HOME") or (os.environ.get("USERPROFILE","") + "/AppData/Local/hermes")

scripts = [
    ("L1→L2 compress", "mem_compress.py"),
    ("L2→L3 consolidate", "mem_consolidate.py"),
    ("L3→L4 retire", "mem_retire.py"),
    ("L3/L4 dedupe", "mem_dedupe.py --apply"),
]

results = []
for label, name in scripts:
    parts = name.split()
    sp = f"{HH}/scripts/{parts[0]}"
    if not os.path.exists(sp):
        results.append(f"{label}: script not found")
        continue
    r = subprocess.run([sys.executable, sp] + parts[1:], capture_output=True, text=True, timeout=60)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if r.returncode == 0:
        results.append(f"{label}: {out.split(chr(10))[0] if out else 'OK'}")
    else:
        results.append(f"{label}: error {r.returncode} — {(err or out)[:200]}")

print("\n".join(results))
