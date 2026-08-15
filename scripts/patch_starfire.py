"""Patch memory_manager.py on 星火: update thresholds + trim-to-target."""
import re, sys

path = '/root/.hermes/plugins/snowfox-memory/memory_manager.py'
with open(path) as f:
    c = f.read()

# 1. DEFAULT_CAP values
c = c.replace('"L1": 50 * 1024', '"L1": 45 * 1024')
c = c.replace('"L2": 100 * 1024', '"L2": 90 * 1024')
c = c.replace('"L3": 50 * 1024', '"L3": 45 * 1024')

# 2. COMPRESS_AMOUNT -> TRIM_TARGET
c = c.replace(
    'COMPRESS_AMOUNT = {\n    "L1": 5 * 1024,\n    "L2": 10 * 1024,\n    "L3": 5 * 1024,\n}',
    'TRIM_TARGET = {\n    "L1": 45 * 1024,\n    "L2": 90 * 1024,\n    "L3": 45 * 1024,\n}'
)

# 3. Fix _compress_l1_to_l2: fixed-amount -> trim-to-target
old_l1 = '''    target_kb = COMPRESS_AMOUNT["L1"]
    removed_kb = 0
    summaries = []

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if removed_kb >= target_kb:
            break
        size = f.stat().st_size
        content = f.read_text(encoding="utf-8")'''

new_l1 = '''    target = TRIM_TARGET["L1"]
    total = sum(f.stat().st_size for f in files)
    removed = 0
    summaries = []

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if total - removed <= target:
            break
        size = f.stat().st_size
        content = f.read_text(encoding="utf-8")'''

c = c.replace(old_l1, new_l1)

# 4. Fix _compress_l2_to_l3
old_l2 = '''    target_kb = COMPRESS_AMOUNT["L2"]
    removed_kb = 0
    merged = []

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if removed_kb >= target_kb:
            break
        size = f.stat().st_size'''

new_l2 = '''    target = TRIM_TARGET["L2"]
    total = sum(f.stat().st_size for f in files)
    removed = 0
    merged = []

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if total - removed <= target:
            break
        size = f.stat().st_size'''

c = c.replace(old_l2, new_l2)

# 5. Fix _compress_l3_to_l4
old_l3 = '''    target_kb = COMPRESS_AMOUNT["L3"]
    removed_kb = 0

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if removed_kb >= target_kb:
            break
        size = f.stat().st_size'''

new_l3 = '''    target = TRIM_TARGET["L3"]
    total = sum(f.stat().st_size for f in files)
    removed = 0

    for f in sorted(files, key=lambda p: p.stat().st_mtime):
        if total - removed <= target:
            break
        size = f.stat().st_size'''

c = c.replace(old_l3, new_l3)

# 6. Update remaining variable names
c = c.replace('removed_kb += size', 'removed += size')
c = c.replace('removed_kb >= target', 'removed >= target')

# 7. Comments
c = c.replace('L1近期流（50KB，超限压缩5KB→L2）', 'L1近期流（45KB，超限截断至45KB→L2）')
c = c.replace('L2中期摘要（100KB，超限合并10KB→L3）', 'L2中期摘要（90KB，超限截断至90KB→L3）')
c = c.replace('L3长期记忆（50KB，超限退役5KB→L4）', 'L3长期记忆（45KB，超限截断至45KB→L4）')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('OK - memory_manager.py patched successfully')
