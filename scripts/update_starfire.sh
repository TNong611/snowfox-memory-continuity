patch -u ~/.hermes/plugins/snowfox-memory/memory_manager.py << 'PATCH'
--- a/memory_manager.py
+++ b/memory_manager.py
@@ -1,4 +1,4 @@
 """
 SnowFox 五级记忆管理器
 
@@ -13,16 +13,16 @@
 # ── 常量 ──────────────────────────────────────────────────────────
 DEFAULT_CAP = {
-    "F0": 10 * 1024,       # 10KB
-    "L1": 50 * 1024,       # 50KB
-    "L2": 100 * 1024,      # 100KB
-    "L3": 50 * 1024,       # 50KB
+    "F0": 10 * 1024,       # 10KB, unchanged
+    "L1": 45 * 1024,       # 45KB (was 50KB)
+    "L2": 90 * 1024,       # 90KB (was 100KB)
+    "L3": 45 * 1024,       # 45KB (was 50KB)
 }
 
-COMPRESS_AMOUNT = {
-    "L1": 5 * 1024,        # 每次压缩5KB→L2
-    "L2": 10 * 1024,       # 每次合并10KB→L3
-    "L3": 5 * 1024,        # 每次退役5KB→L4
+TRIM_TARGET = {
+    "L1": 45 * 1024,       # 截断至45KB，旧段→L2
+    "L2": 90 * 1024,       # 截断至90KB，旧段→L3
+    "L3": 45 * 1024,       # 截断至45KB，旧段→L4
 }

 _HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
PATCH
# Then replace COMPRESS_AMOUNT with TRIM_TARGET in the capacity check function
sed -i 's/COMPRESS_AMOUNT\[/TRIM_TARGET[/g' ~/.hermes/plugins/snowfox-memory/memory_manager.py
# Change compress_amount usage to trim-to-target logic
python3 -c "
import re
path = '/root/.hermes/plugins/snowfox-memory/memory_manager.py'
with open(path) as f:
    c = f.read()
# Replace the fixed-amount removal with target-based trim
old = '''        moved = 0
        for fname in sorted(md_files, key=lambda f: f.stat().st_mtime):
            if moved >= amount:
                break
            size = fname.stat().st_size
            ...'''
# Actually, let me just read the compress function first
print('need to see the function first')
" 2>&1
