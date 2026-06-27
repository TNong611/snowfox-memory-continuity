#!/usr/bin/env python3
"""L1 → L2: 压缩近期流到摘要层"""
import os, shutil
from datetime import datetime

HERMES_HOME = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "hermes")
RECENT_DIR = os.path.join(HERMES_HOME, "memories", "recent")
SUMMARY_DIR = os.path.join(HERMES_HOME, "memories", "summary")

L1_MAX_KB = 50
L1_KEEP_KB = 45

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

def compress_l1_to_l2():
    size = get_dir_size(RECENT_DIR)
    if size <= L1_MAX_KB:
        print(f"  L1: {size:.1f}KB/{L1_MAX_KB}KB ✅")
        return
    to_remove = int((size - L1_KEEP_KB) * 1024)
    removed = 0
    for fp, fsize, fname in get_files(RECENT_DIR):
        if removed >= to_remove: break
        dst = os.path.join(SUMMARY_DIR, f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
        shutil.move(fp, dst)
        removed += fsize
        print(f"  🔽 L1→L2: {fname} ({fsize/1024:.1f}KB)")
    print(f"  ✅ L1压缩: 移出 {removed/1024:.1f}KB, 剩余 {get_dir_size(RECENT_DIR):.1f}KB")

if __name__ == "__main__":
    compress_l1_to_l2()
