#!/usr/bin/env python3
"""L3 → L4: 退役长期记忆到归档区"""
import os, shutil
from datetime import datetime

HERMES_HOME = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "hermes")
LONG_TERM_DIR = os.path.join(HERMES_HOME, "memories", "long_term")
ARCHIVE_DIR = os.path.join(HERMES_HOME, "memories", "archive")
INDEX_PATH = os.path.join(ARCHIVE_DIR, "index.md")

L3_MAX_KB = 50
L3_KEEP_KB = 45

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

def update_index(fname, summary=""):
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(f"| {date} | {fname} | {summary[:30]}... |\n")

def retire_l3_to_l4():
    size = get_dir_size(LONG_TERM_DIR)
    if size <= L3_MAX_KB:
        print(f"  L3: {size:.1f}KB/{L3_MAX_KB}KB ✅")
        return
    to_remove = int((size - L3_KEEP_KB) * 1024)
    removed = 0
    for fp, fsize, fname in get_files(LONG_TERM_DIR):
        if removed >= to_remove: break
        try:
            with open(fp, "r") as f: summary = f.read()[:50]
        except: summary = ""
        dst = os.path.join(ARCHIVE_DIR, f"archived_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fname}")
        shutil.move(fp, dst)
        update_index(fname, summary)
        removed += fsize
        print(f"  📦 L3→L4: {fname} ({fsize/1024:.1f}KB)")
    print(f"  ✅ L3退役: 移出 {removed/1024:.1f}KB, 剩余 {get_dir_size(LONG_TERM_DIR):.1f}KB")

if __name__ == "__main__":
    retire_l3_to_l4()
