"""Run memory maintenance and assemble context.
Single-file memory hierarchy with unique build timestamps.
Solves the Hermes read_file dedup loop: every rebuild has a different
build timestamp in the header, so read_file always returns fresh content."""
import os, sys
from pathlib import Path
from datetime import datetime

M = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "memories"
SCRIPTS = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "scripts"

def run_script(name):
    s = SCRIPTS / name
    if not s.exists():
        print(f"WARN: {s} not found"); return
    r = os.popen(f'"{sys.executable}" "{s}" 2>&1').read()
    print(f"[{name}] {r[:200].strip()}")

def read_md(filepath, heading=""):
    p = M / filepath
    if not p.exists(): return ""
    c = p.read_text(encoding="utf-8")
    return f"{heading}\n{c}" if heading else c

def read_md_sections(filepath, limit_kb=0, section_chars=0):
    p = M / filepath
    if not p.exists(): return ""
    content = p.read_text(encoding="utf-8")
    if content.strip().startswith("# "):
        parts = content.split("\n## ", 1)
        header = parts[0] if len(parts) > 1 else ""
        body = ("## " + parts[1]) if len(parts) > 1 else content
    else:
        header = ""
        body = content
    sections = body.split("\n## ")
    if section_chars > 0:
        sections = [s[:section_chars] for s in sections]
    if limit_kb > 0:
        target = int(limit_kb * 1024)
        kept = []; total = 0
        for s in reversed(sections):
            if total + len(s.encode("utf-8")) > target: break
            kept.insert(0, s)
            total += len(s.encode("utf-8"))
        sections = kept
    return "\n".join(sections)

def assemble_context():
    """Build _assembled_context.md with version header under injection budget.
    The build timestamp ensures every rebuild produces unique content,
    preventing the Hermes read_file dedup loop. Budget caps total injected
    size (was 154KB ≈ 50K tokens → DeepSeek 240s stall)."""
    import mem_assembly
    from mem_config import ASSEMBLY_BUDGET_KB
    text = mem_assembly.assemble_budgeted(M, budget_kb=ASSEMBLY_BUDGET_KB)
    out = M / "_assembled_context.md"
    out.write_text(text, encoding="utf-8")
    print(f"OK: {out.name} {len(text)}B = {len(text)/1024:.1f}KB (budget {ASSEMBLY_BUDGET_KB}KB, build: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')})")

if __name__ == "__main__":
    # L1→L2 compress is now inline (triggered by plugin on write overflow)
    run_script("mem_consolidate.py")
    run_script("mem_retire.py")
    assemble_context()