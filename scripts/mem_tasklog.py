"""任务日志模块 — 管理每日任务记录 & F0 7KB 压缩策略。

- worklog: 记录当天任务(doing/done/todo)
- next-day compress: 将昨天任务日志压缩到 F0，保留≤7KB
- workspace: 管理当天工作区目录
"""

import os, json, shutil, subprocess, sys
from datetime import datetime, timedelta
from mem_config import get_config

HH = os.environ.get("USERPROFILE", "C:\\Users\\tnong") + "/AppData/Local/hermes"
MEM = HH + "/memories"
WORK = HH + "/workspace"

# ── Task Log ──

TASKLOG_PATH = MEM + "/tasklog.md"

def today_tag() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def init_tasklog():
    """Ensure today's tasklog section exists."""
    if not os.path.exists(TASKLOG_PATH):
        with open(TASKLOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"# 任务日志\n_自动管理，当日记录，次日压缩到 F0_\n\n---\n\n## {today_tag()}\n\n")
        print(f"  tasklog: created with today tag {today_tag()}")
        return
    content = open(TASKLOG_PATH, "r", encoding="utf-8").read()
    if f"## {today_tag()}" not in content:
        with open(TASKLOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n## {today_tag()}\n\n")

def write_tasklog_entry(status: str, content: str):
    """Write a task entry under today's section. status: doing/done/todo."""
    init_tasklog()
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"- **{ts}** [{status}] {content}\n"
    lines = open(TASKLOG_PATH, "r", encoding="utf-8").read().split("\n")
    # find today's section and insert after it
    for i, line in enumerate(lines):
        if line.strip() == f"## {today_tag()}":
            # find the next section or end
            insert_at = i + 1
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    insert_at = j
                    break
                insert_at = j + 1
            lines.insert(insert_at, entry)
            break
    open(TASKLOG_PATH, "w", encoding="utf-8").write("\n".join(lines))
    print(f"  tasklog: added [{status}] {content}")

def compress_yesterday_to_fixed():
    """Compress yesterday's tasklog section into F0, keeping ≤7KB."""
    tasklog = TASKLOG_PATH
    fixed = MEM + "/fixed.md"
    if not os.path.exists(tasklog):
        print("  tasklog: not found, nothing to compress")
        return

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    content = open(tasklog, "r", encoding="utf-8").read()
    sections = content.split("\n## ")
    
    yday_section = None
    remaining = []
    for sec in sections:
        if sec.startswith(yesterday):
            yday_section = "## " + sec
        else:
            remaining.append(sec)

    if not yday_section:
        print(f"  tasklog: no section for {yesterday}, nothing to compress")
        return

    # Build the compressed entry
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = yday_section.strip().split("\n")
    # Take first 40 meaningful lines as summary (≈7KB if ~175 chars/line)
    summary_lines = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("_")]
    compressed = "\n".join(summary_lines[:40])
    compressed_bytes = len(compressed.encode("utf-8"))
    
    # If still > 7KB, truncate further
    if compressed_bytes > 7 * 1024:
        compressed = compressed[:7000] + "\n…[truncated to ~7KB]"

    entry = f"\n## {now} | tasklog-{yesterday}\n\n{compressed}\n\n---\n"

    # Write to F0, then trim F0 to 7KB
    os.makedirs(os.path.dirname(fixed), exist_ok=True)
    with open(fixed, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # Trim F0 to ≤7KB
    _trim_fixed_to_7kb(fixed)
    
    # Remove yesterday's section from tasklog
    with open(tasklog, "w", encoding="utf-8") as f:
        f.write("\n## ".join(remaining))
    
    print(f"  tasklog: {yesterday} compressed → F0 ({compressed_bytes}B)")

def _trim_fixed_to_7kb(path: str):
    """Keep F0 ≤7KB by removing oldest entries if needed."""
    if not os.path.exists(path):
        return
    sz = os.path.getsize(path)
    if sz <= 7 * 1024:
        print(f"  F0: {sz/1024:.1f}KB ≤ 7KB, no trim needed")
        return
    content = open(path, "r", encoding="utf-8").read()
    secs = content.split("\n## ")
    kept = [secs[0]]  # always keep header
    total = len(secs[0].encode("utf-8"))
    for sec in reversed(secs[1:]):
        bs = len(("## " + sec).encode("utf-8"))
        if total + bs > 7 * 1024:
            break
        kept.insert(1, "## " + sec)
        total += bs
    open(path, "w", encoding="utf-8").write("\n".join(kept))
    print(f"  F0: trimmed from {sz/1024:.1f}KB to {total/1024:.1f}KB (target ≤7KB)")

# ── Workspace ──

def init_workspace():
    """Ensure today's workspace directory exists, clean up yesterday's."""
    today = today_tag()
    today_dir = f"{WORK}/{today}"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_dir = f"{WORK}/{yesterday}"
    
    # Clean yesterday's workspace
    if os.path.exists(yesterday_dir):
        shutil.rmtree(yesterday_dir)
        print(f"  workspace: cleaned {yesterday}")
    
    # Create today's
    os.makedirs(today_dir, exist_ok=True)
    print(f"  workspace: ready → {today_dir}")
    return today_dir

def save_to_workspace(filename: str, content: bytes | str):
    """Save a file to today's workspace."""
    today_dir = init_workspace()
    path = f"{today_dir}/{filename}"
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(path, mode) as f:
        f.write(content)
    print(f"  workspace: saved {filename}")
    return path

def list_workspace() -> list[str]:
    """List files in today's workspace."""
    today_dir = f"{WORK}/{today_tag()}"
    if not os.path.exists(today_dir):
        return []
    return os.listdir(today_dir)

# ── CLI ──

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "init":
        init_tasklog()
        init_workspace()
    elif action == "compress":
        compress_yesterday_to_fixed()
    elif action == "add":
        status = sys.argv[2] if len(sys.argv) > 2 else "todo"
        text = sys.argv[3] if len(sys.argv) > 3 else "(no detail)"
        write_tasklog_entry(status, text)
    elif action == "workspace-list":
        for f in list_workspace():
            print(f)
    elif action == "status":
        init_tasklog()
        init_workspace()
        print(f"  workspace files: {len(list_workspace())}")
        print(f"  tasklog exists: {os.path.exists(TASKLOG_PATH)}")
    else:
        print(f"Unknown action: {action}")
        print("Usage: mem_tasklog.py [init|compress|add <status> <text>|workspace-list|status]")
