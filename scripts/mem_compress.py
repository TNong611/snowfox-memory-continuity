#!/usr/bin/env python3
"""L1 → L2: 压缩近期流到摘要层（过滤工具输出噪声，保留对话摘要）"""
import os, shutil, re
from datetime import datetime

HERMES_HOME = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "hermes")
RECENT_DIR = os.path.join(HERMES_HOME, "memories", "recent")
SUMMARY_DIR = os.path.join(HERMES_HOME, "memories", "summary")

L1_MAX_KB = 50
L1_OVERFLOW_KB = 5   # 固定溢出量：超MAX后恰好移出5KB

def get_dir_size(path):
    if not os.path.isdir(path): return 0
    return sum(os.path.getsize(os.path.join(path,f)) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))) / 1024

def get_files(path):
    files = []
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            files.append((fp, os.path.getsize(fp), f))
    files.sort(key=lambda x: os.path.getmtime(x[0]))
    return files

def strip_tool_noise(content):
    """Strip tool output blocks and keep only user/assistant conversational turns."""
    lines = content.split('\n')
    clean = []
    skip = False
    for line in lines:
        # Skip raw tool output blocks (tool sections)
        if line.strip().startswith('### tool') or line.strip().startswith('|'):
            skip = True
            continue
        # Skip JSON tool result lines
        if re.match(r'^\s*\{\s*"', line) or re.match(r'^\s*\{\s*\'', line):
            skip = True
            continue
        # Stop skipping at the next user or assistant marker
        if line.strip().startswith('### user') or line.strip().startswith('## 用户') or line.strip().startswith('## 雪狐') or line.strip().startswith('### assistant'):
            skip = False
        if not skip:
            # Trim very long tool output lines that slipped through
            if len(line) > 500:
                line = line[:500] + '...[truncated]'
            clean.append(line)
    return '\n'.join(clean)

def compress_l1_to_l2():
    size = get_dir_size(RECENT_DIR)
    if size <= L1_MAX_KB:
        print(f"  L1: {size:.1f}KB/{L1_MAX_KB}KB ✅")
        return
    to_remove = int(L1_OVERFLOW_KB * 1024)
    removed = 0
    for fp, fsize, fname in get_files(RECENT_DIR):
        if removed >= to_remove: break
        # Read, strip tool noise, write compact version to L2
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                raw = f.read()
            clean = strip_tool_noise(raw)
            if not clean.strip():
                # Empty after stripping - just keep a note
                clean = f"# 会话 {fname}\n(无可用摘要)\n"
        except Exception as e:
            clean = f"# 会话 {fname}\n(读取失败: {e})\n"
        dst = os.path.join(SUMMARY_DIR, f"sum_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(clean)
        os.remove(fp)
        removed += fsize
        print(f"  🔽 L1→L2: {fname} ({fsize/1024:.1f}KB → {len(clean)//1024:.1f}KB clean)")
    print(f"  ✅ L1压缩: 移出 {removed/1024:.1f}KB, 剩余 {get_dir_size(RECENT_DIR):.1f}KB")

if __name__ == "__main__":
    compress_l1_to_l2()
