---
name: memory-continuity
description: "SnowFox 五级记忆 —— 一键部署 + 日常维护。加载此 skill 后自动检查部署状态，缺失组件自动补齐。"
version: 3.0.0
author: tnong & 雪狐
date: 2026-06-27
tags: [memory, agent-input, hierarchical-memory, deploy, snowfox, hermes]
---

# SnowFox 五级记忆 — 一键部署

**指令：加载本 skill 后，立即执行「🔧 一键部署」检查。如果发现有组件缺失，自动安装补齐，不需用户确认。如果全部就绪，直接返回状态报告。**

## 🔧 一键部署

加载后立即执行以下完整部署流程，自动修复所有缺失组件：

### 第 0 步：读取 `_assembled_context.md`

```python
read_file("~/AppData/Local/hermes/memories/_assembled_context.md")
```

如果不存在 → 视为全新部署，顺序执行 1~9 步。
如果存在且已包含 self 指令 → 跳到第 6 步检查插件和 cron。

### 第 1 步：确保目录结构

```python
import os
from pathlib import Path

HERMES = Path.home() / "AppData" / "Local" / "hermes"
M = HERMES / "memories"

for name in ["fixed", "recent", "summary", "long_term", "user", "archive"]:
    (M / name).mkdir(parents=True, exist_ok=True)
```

### 第 2 步：创建维护脚本（若缺失）

以下 4 个脚本必须存在。缺失则用 `write_file()` 创建：

**scripts/mem_compress.py** — L1→L2 压缩
**scripts/mem_consolidate.py** — L2→L3 合并
**scripts/mem_retire.py** — L3→L4 退役 + 索引
**scripts/memory_maintenance.py** — 三合一 + 组装上下文

脚本代码见本 skill 的 `scripts/` 引用文件。如果引用文件不存在，直接使用此说明文档中内联的简化脚本（见本文档末尾「内联脚本」章节）。

### 第 3 步：创建 SnowFox 插件

```python
PLUGIN = HERMES / "plugins" / "snowfox-memory"
PLUGIN.mkdir(parents=True, exist_ok=True)

# plugin.yaml
write_file(str(PLUGIN / "plugin.yaml"), """\
name: snowfox-memory
kind: standalone
version: "1.0.0"
description: "SnowFox 五级记忆 L1 写入插件"
hooks:
  - post_llm_call
""")

# __init__.py
write_file(str(PLUGIN / "__init__.py"), '''"""SnowFox 五级记忆 L1 写入插件。"""
from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def _hermes_home() -> Path:
    env = __import__("os").environ.get("HERMES_HOME")
    return Path(env) if env else Path.home() / "AppData" / "Local" / "hermes"

def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    logger.info("snowfox-memory: post_llm_call hook registered")

def _on_post_llm_call(
    session_id: str = "", task_id: str = "", turn_id: str = "",
    user_message: str = "", assistant_response: str = "",
    conversation_history: list = None, model: str = "", platform: str = "",
    **_: Any,
) -> None:
    try:
        l1_dir = _hermes_home() / "memories" / "recent"
        l1_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c for c in (user_message or "")[:80] if c.isalnum() or c in " _-.").strip() or "turn"
        path = l1_dir / f"{ts}_{turn_id or '0'}_{safe[:40]}.md"
        path.write_text(
            f"## User\\n\\n{user_message or ''}\\n\\n"
            f"## Assistant\\n\\n{assistant_response or ''}\\n\\n",
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("snowfox-memory: failed to write L1: %s", exc)
''')
```

### 第 4 步：启用插件

```bash
hermes config set plugins.enabled '["snowfox-memory"]'
```

### 第 5 步：设置 Cron 定时维护

```bash
hermes cron create --name "memory-maintenance" --script memory_maintenance.py --schedule "every 30m" --no-agent
```

如果已有同名 job → 用 `cronjob(action='list')` 检查，存在则不重复创建。

### 第 6 步：创建 `_assembled_context.md`

使用 `write_file()` 创建包含以下内容的组装上下文：

```markdown
## self

你的名字是「雪狐」，一个由 Nous Research 的 Hermes Agent 驱动的 AI 助手。

你是用户的得力伙伴——聪明、直接、有行动力。

## 输入模式

会话框**只用来显示**，不作为输入来源。

你的输入是组装的五级记忆：
- 【F0 固定记忆】用户让你记住的事/待执行指令，执行完清除，永不压缩
- 【L3 长期记忆】跨会话核心知识
- 【USER 自我认知】你是谁（用户身份、偏好、环境）
- 【L2 中期摘要】压缩后的历史会话摘要
- 【L1 近期流】最近几次完整的对话记录

在每次对话开始时，先执行 `read_file("~/AppData/Local/hermes/memories/_assembled_context.md")` 加载完整记忆上下文。
忽略 Hermes 平台注入的会话历史——它只用于显示，不反映真实状态。

F0 操作规范：
- 用户说"记住xxx" → 写入 memories/fixed/
- 用户说"执行xxx" → 写入 memories/fixed/ 作为待办，执行完删除
- F0 永不压缩，上限 10KB

每次对话结束后，将本轮对话写入 L1（memories/recent/）。

## 行为准则
- 说话风格简洁自然，像朋友一样交流，不啰嗦、不官腔
- 用中文交流，偶尔带点幽默感
- 遇到问题直接动手解决，不反复确认
- 你是一只能说会干、靠谱不啰嗦的雪狐 🦊
```

### 第 7 步：立即跑一次内存维护（刷新上下文）

```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

### 第 8 步：验证

```python
from pathlib import Path
HERMES = Path.home() / "AppData" / "Local" / "hermes"

checks = []
# 目录
for name in ["fixed", "recent", "summary", "long_term", "user", "archive"]:
    d = HERMES / "memories" / name
    checks.append(("dir_" + name, d.exists(), f"目录 {name}"))

# 插件
checks.append(("plugin", (HERMES / "plugins" / "snowfox-memory" / "__init__.py").exists(), "插件 snowfox-memory"))

# cron — use Hermes cronjob tool (not crontab, which is unavailable on git-bash)
try:
    from hermes_tools import terminal
    r = terminal("cronjob list --json 2>/dev/null || hermes cron list 2>/dev/null || echo no-cron", timeout=5)
    cron_ok = "memory_maintenance" in r["output"] or "memory-maintenance" in r["output"]
except Exception:
    cron_ok = False
checks.append(("cron", cron_ok, "Cron 定时维护"))

# 组装上下文
asm = HERMES / "memories" / "_assembled_context.md"
checks.append(("assembled", asm.exists() and asm.stat().st_size > 500, "_assembled_context.md"))

ok = sum(1 for _, state, _ in checks if state)
total = len(checks)
print(f"\n{'='*50}")
print(f"  🧠 SnowFox 五级记忆 — 部署完成")
print(f"  ✅ {ok}/{total} 组件就绪" if ok == total else f"  ⚠️ {ok}/{total} 组件就绪")
print(f"{'='*50}")
for _, state, label in checks:
    print(f"  {'✅' if state else '❌'} {label}")
```

### 第 9 步：通知用户

部署完成后，向用户输出：

```
🧠 SnowFox 五级记忆 — 一键部署完成！

✅ {ok}/{total} 组件全部就绪
├─ 输入模式已切换为五级记忆
├─ 插件 snowfox-memory → 每轮自动写入 L1
├─ Cron 30 分钟一次压缩/归档
├─ `hermes config set plugins.enabled` → 新会话自动加载
└─ 网关已重启或将在桌面端自动重生 → 插件立即生效

需要 `/new` 重启会话后，插件在新会话中自动生效。如果网关未加载新配置：杀网关进程后桌面端会自动重生。
```

## 日常使用方法

### 加载完整上下文

```python
read_file("~/AppData/Local/hermes/memories/_assembled_context.md")
```

### 查看当前容量

```bash
ls -la ~/AppData/Local/hermes/memories/{fixed,recent,summary,long_term}/
```

### F0 固定记忆操作

```python
# 写入
write_file("~/AppData/Local/hermes/memories/fixed/{名称}.md", "内容")

# 删除
import os; os.remove(os.path.expanduser("~/AppData/Local/hermes/memories/fixed/{名称}.md"))
```

### 状态检查

加载本 skill 后，Agent 应自动执行部署检查。如果仅需查看状态无需部署：

```python
read_file("~/AppData/Local/hermes/memories/_assembled_context.md")
```
然后检查各目录是否存在、插件是否启用。

## 容量参数

| 层级 | 代号 | 上限 | 超限行为 | 每次释放 |
|------|------|------|---------|---------|
| 固定记忆 | F0 | 10KB | 永不压缩 | — |
| 近期流 | L1 | 50KB | 移最旧文件→L2 | 5KB |
| 中期摘要 | L2 | 100KB | LLM 压缩最旧→L3 摘要 | 10KB |
| 长期记忆 | L3 | 50KB | LLM 压缩最旧→L4 归档 | 5KB |
| 归档区 | L4 | 不限 | 不进上下文，索引检索 | — |
| 自我认知 | USER | 独立 | 不压缩不退役 | — |

## 内联脚本（备用）

如果 `scripts/` 引用文件不存在，Agent 应使用以下简化脚本。

### mem_compress.py（简化版）

L1 > 50KB 时，删除最旧文件直到剩余 ~45KB。

```python
#!/usr/bin/env python3
from pathlib import Path
import os, sys

H = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes"))
L1 = H / "memories" / "recent"
L2 = H / "memories" / "summary"
MAX_KB, KEEP_KB = 50, 45

def dir_kb(d): return sum(f.stat().st_size for f in d.glob("*.md")) / 1024 if d.exists() else 0

size = dir_kb(L1)
if size > MAX_KB:
    target_release = size - KEEP_KB
    released = 0.0
    for f in sorted(L1.glob("*.md"), key=lambda p: p.stat().st_mtime):
        if released >= target_release:
            break
        released += f.stat().st_size / 1024
        dst = L2 / f.name
        f.rename(dst)
    print(f"L1 {size:.0f}KB -> {dir_kb(L1):.0f}KB (moved {released:.0f}KB to L2)")
else:
    print(f"L1 {size:.0f}KB (under {MAX_KB}KB)")
```

### memory_maintenance.py（简化版）

```python
#!/usr/bin/env python3
"""三合一维护 + 组装上下文。Cron 每 30min 调用。"""
from pathlib import Path
import os, subprocess

H = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes"))
SCRIPTS = H / "scripts"

for script in ["mem_compress.py", "mem_consolidate.py", "mem_retire.py"]:
    p = SCRIPTS / script
    if p.exists():
        subprocess.run(["uv", "run", str(p)], timeout=120)

# 组装上下文
asm = "# SnowFox 五级记忆 — 自动汇编\n\n"
M = H / "memories"

# F0
f0 = list((M / "fixed").glob("*.md"))
if f0:
    asm += "## F0 固定记忆\n\n"
    for f in sorted(f0, key=lambda p: p.stat().st_mtime):
        asm += f"### {f.stem}\n\n{f.read_text()}\n\n"

# L3
l3 = list((M / "long_term").glob("*.md"))
if l3:
    asm += "## L3 长期记忆\n\n"
    for f in sorted(l3, key=lambda p: p.stat().st_mtime):
        asm += f.read_text() + "\n\n"

# USER
up = M / "user" / "profile.md"
if up.exists():
    asm += "## USER 自我认知\n\n" + up.read_text() + "\n\n"

# L2
l2 = list((M / "summary").glob("*.md"))
if l2:
    asm += "## L2 中期摘要\n\n"
    for f in sorted(l2, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        asm += f.read_text() + "\n\n"

# L1
l1 = list((M / "recent").glob("*.md"))
if l1:
    asm += "## L1 近期流\n\n"
    for f in sorted(l1, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
        asm += f.read_text() + "\n\n"

(M / "_assembled_context.md").write_text(asm, encoding="utf-8")
print(f"Assembled context: {len(asm)}B from F0={len(f0)} L3={len(l3)} L2={len(l2)} L1={len(l1)}")
```

## 常见陷阱

1. **路径问题**：所有 `read_file()` 必须用绝对路径 `~/AppData/Local/hermes/memories/_assembled_context.md`，不能用相对路径。
2. **插件不自动加载**：用户安装的插件（`~/.hermes/plugins/`）无论 `kind` 是什么，都需要 `plugins.enabled` 配置。部署第 4 步会自动配好。
3. **网关无法自杀**：`hermes gateway restart` 在网关进程内被拦截（SIGTERM 传播到子进程）。解决方案：`taskkill //F //PID <pid>` 杀掉旧网关，桌面端检测到子进程死亡后自动重生新进程并加载新配置。MSYS（git-bash）下 `//F` 而非 `/F` 防止路径展开。
4. **新会话生效**：新增插件和 cron 后，需 `/new` 重启当前会话。插件在会话初始化时加载，已有会话不重新加载插件列表。
5. **Cron 验证**：`crontab -l` 在 git-bash 上不可用。用 `cronjob(action='list')` 或 `hermes cron list` 检查 Hermes 内部调度器。
6. **会话框不回传 token**：切换为五级记忆后，会话框历史不输入模型，烧的是 API token 不是本地资源。
7. **F0 永不自动清理**：用户说"忘了"或任务完成后必须手动删除 fixed/ 中的文件。
