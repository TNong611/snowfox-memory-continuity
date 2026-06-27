#!/usr/bin/env python3
"""L2 → L3: 合并中期摘要到长期记忆"""
import os, shutil
from datetime import datetime

HERMES_HOME = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "hermes")
SUMMARY_DIR = os.path.join(HERMES_HOME, "memories", "summary")
LONG_TERM_DIR = os.path.join(HERMES_HOME, "memories", "long_term")

L2_MAX_KB = 100
L2_OVERFLOW_KB = 10  # 固定溢出量：超MAX后恰好移出10KB

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

def consolidate_l2_to_l3():
    size = get_dir_size(SUMMARY_DIR)
    if size <= L2_MAX_KB:
        print(f"  L2: {size:.1f}KB/{L2_MAX_KB}KB ✅")
        return
    to_remove = int(L2_OVERFLOW_KB * 1024)
    removed = 0
    for fp, fsize, fname in get_files(SUMMARY_DIR):
        if removed >= to_remove: break
        dst = os.path.join(LONG_TERM_DIR, f"l3_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
        shutil.move(fp, dst)
        removed += fsize
        print(f"  🔄 L2→L3: {fname} ({fsize/1024:.1f}KB)")
    print(f"  ✅ L2合并: 移出 {removed/1024:.1f}KB, 剩余 {get_dir_size(SUMMARY_DIR):.1f}KB")

if __name__ == "__main__":
    consolidate_l2_to_l3()
