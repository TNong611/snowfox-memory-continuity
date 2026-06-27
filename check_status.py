"""检查五级记忆当前容量状态"""
import os
from pathlib import Path

HERMES = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "hermes"

def kb(path):
    return sum(f.stat().st_size for f in Path(path).glob("*.md")) / 1024 if Path(path).exists() else 0

# 各层级路径
paths = {
    "F0": HERMES / "memories" / "fixed",
    "L1": HERMES / "memories" / "recent",
    "L2": HERMES / "memories" / "summary",
    "L3": HERMES / "memories" / "long_term",
    "L4": HERMES / "memories" / "archive",
}

# 上限
limits = {"F0": 10, "L1": 50, "L2": 100, "L3": 50, "L4": "不限"}
icons = {"F0": "⚪", "L1": "🟢", "L2": "🟡", "L3": "🔴", "L4": "📦"}

print("=" * 40)
print("📊 五级记忆容量状态")
print("=" * 40)
print(f"输入模式: [SOUL] + [F0] + [L3] + [L2] + [L1]")
print()

for name in ["F0", "L1", "L2", "L3", "L4"]:
    size = kb(paths[name])
    limit = limits[name]
    icon = icons[name]
    files = len(list(paths[name].glob("*.md")))
    
    if isinstance(limit, int):
        pct = size / limit * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {icon} {name}: {size:.0f}KB/{limit}KB [{bar}] {pct:.0f}% ({files}条)")
    else:
        print(f"  {icon} {name}: {size:.0f}KB ({limit}) ({files}条)")

print()
print("调节方式: 修改 ~/.hermes/.env 中的 MEMORY_*_KEEP_KB")
print("=" * 40)
