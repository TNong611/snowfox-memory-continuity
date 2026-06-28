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
    """Build _assembled_context.md with version header.
    The build timestamp ensures every rebuild produces unique content,
    preventing the Hermes read_file dedup loop."""
    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f'<!-- SnowFox Memory Assembly | built: {build_ts} -->')
    parts.append("")
    s = read_md("../SOUL.md", "## self")
    if s: parts.append(s)
    s = read_md("fixed.md", "## F0")
    if s: parts.append(s)
    s = read_md("long_term.md", "## L3")
    if s: parts.append(s)
    s = read_md("user.md", "## USER")
    if s: parts.append(s)
    s = read_md_sections("summary.md", limit_kb=90, section_chars=150)
    if s: parts.append(f"## L2\n{s}")
    s = read_md("recent.md", "## L1")
    if s: parts.append(s)
    out = M / "_assembled_context.md"
    text = "\n\n".join(parts)
    out.write_text(text, encoding="utf-8")
    print(f"OK: {out.name} {len(text)}B (build: {build_ts})")

if __name__ == "__main__":
    run_script("mem_compress.py")
    run_script("mem_consolidate.py")
    run_script("mem_retire.py")
    assemble_context()