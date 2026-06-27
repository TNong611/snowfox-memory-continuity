"""Run memory maintenance and assemble context.
Pure Python - no batch, no bash, no external deps.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime

HERMES = Path(os.environ.get('HERMES_HOME', Path.home() / 'AppData' / 'Local' / 'hermes'))
SCRIPTS = HERMES / 'scripts'

def run_script(name):
    """Run a memory maintenance script and capture output/errors."""
    script = SCRIPTS / name
    if not script.exists():
        print(f"WARN: {script} not found, skipping")
        return
    result = os.popen(f'"{sys.executable}" "{script}" 2>&1').read()
    print(f"[{name}] {result[:200].strip()}")

def assemble_context():
    """Assemble _assembled_context.md from SOUL + F0 + L3 + USER + L2 + L1."""
    parts = []
    
    # SOUL
    soul = HERMES / 'SOUL.md'
    if soul.exists():
        parts.append(f'## self\n{soul.read_text(encoding="utf-8")}')
    
    # F0 fixed memory
    fixed_dir = HERMES / 'memories' / 'fixed'
    if fixed_dir.exists():
        f0_files = sorted(fixed_dir.glob('*.md'), key=lambda f: f.stat().st_mtime)
        if f0_files:
            total = sum(f.stat().st_size for f in f0_files)
            content = '\n'.join(f.read_text(encoding='utf-8') for f in f0_files)
            parts.append(f'## F0 [{total//1024}KB/10KB]\n{content}')
    
    # L3 long-term (all .md in long_term/, full content; MEMORY.md already moved there)
    l3_dir = HERMES / 'memories' / 'long_term'
    if l3_dir.exists():
        l3_files = sorted(l3_dir.glob('*.md'), key=lambda f: f.stat().st_mtime)
        if l3_files:
            l3_content = '\n---\n'.join(f.read_text(encoding='utf-8') for f in l3_files)
            parts.append(f'## L3\n{l3_content}')
    
    # USER profile
    user_file = HERMES / 'memories' / 'user' / 'profile.md'
    if user_file.exists():
        parts.append(f'## USER\n{user_file.read_text(encoding="utf-8")}')
    
    # L2 summary (last 10 files, 300 chars each)
    l2_dir = HERMES / 'memories' / 'summary'
    if l2_dir.exists():
        l2_files = sorted(l2_dir.glob('*.md'), key=lambda f: f.stat().st_mtime)[-10:]
        if l2_files:
            l2_content = '\n---\n'.join(f.read_text(encoding='utf-8')[:300] for f in l2_files)
            parts.append(f'## L2\n{l2_content}')
    
    # L1 recent (last 6 files, full content)
    l1_dir = HERMES / 'memories' / 'recent'
    if l1_dir.exists():
        l1_files = sorted(l1_dir.glob('*.md'), key=lambda f: f.stat().st_mtime)[-6:]
        if l1_files:
            l1_content = '\n'.join(f.read_text(encoding='utf-8') for f in l1_files)
            parts.append(f'## L1\n{l1_content}')
    
    # Write assembled context
    out = HERMES / 'memories' / '_assembled_context.md'
    text = '\n\n'.join(parts)
    out.write_text(text, encoding='utf-8')
    print(f'OK: {out.name} {len(text)}B')

if __name__ == '__main__':
    # Step 1-3: compression
    run_script('mem_compress.py')
    run_script('mem_consolidate.py')
    run_script('mem_retire.py')
    # Step 4: assemble
    assemble_context()
