---
name: memory-continuity
description: "SnowFox 五级记忆Agent输入模式：F0+L1+L2+L3+L4层级记忆替换默认会话上下文。会话框仅用于显示，输入=组装记忆+当前消息。支持容量调节、F0固定记忆管理。"
version: 2.1.0
author: tnong & 雪狐
date: 2026-06-27
tags: [memory, agent-input, hierarchical-memory, continuity, snowfox, hermes]
---

# SnowFox 五级记忆连续性

**指令：加载本 skill 后，立即执行「🔍 部署状态自检」并返回结果给用户。**

## 🔍 部署状态自检（入口点）

加载本 skill 后，**立即**执行以下检查，并以标准格式返回完整的部署状态报告。

### 检查步骤

执行这段代码（或等效的终端命令）：

```python
import os, json
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME",
    Path.home() / "AppData" / "Local" / "hermes"))
M = HOME / "memories"
SCRIPTS = HOME / "scripts"
PLUGINS = HOME / "plugins" / "snowfox-memory"

def kb(d):
    return sum(f.stat().st_size for f in d.glob("*.md")) / 1024 if d.exists() else 0

def nfiles(d):
    return len(list(d.glob("*.md"))) if d.exists() else 0

checks = {}

# 1. 目录结构
dirs = {
    "F0 fixed":    M / "fixed",
    "L1 recent":   M / "recent",
    "L2 summary":  M / "summary",
    "L3 long_term": M / "long_term",
    "L4 archive":  M / "archive",
    "user":        M / "user",
}
for name, d in dirs.items():
    exists = d.exists()
    checks[f"dir_{name.replace(' ','_')}"] = {
        "ok": exists,
        "label": f"目录 {name}",
        "detail": f"{nfiles(d)} 文件, {kb(d):.0f}KB" if exists else "不存在"
    }

# 2. 组装文件
asm = M / "_assembled_context.md"
if asm.exists():
    sz = asm.stat().st_size
    checks["assembled_context"] = {
        "ok": sz > 500,
        "label": "组装上下文 _assembled_context.md",
        "detail": f"{sz}B" if sz > 0 else "空文件"
    }
else:
    checks["assembled_context"] = {"ok": False, "label": "组装上下文", "detail": "文件不存在"}

# 3. 维护脚本
scripts_found = {
    "mem_compress.py": (SCRIPTS / "mem_compress.py").exists(),
    "mem_consolidate.py": (SCRIPTS / "mem_consolidate.py").exists(),
    "mem_retire.py": (SCRIPTS / "mem_retire.py").exists(),
    "memory_maintenance.py": (SCRIPTS / "memory_maintenance.py").exists(),
}
scripts_ok = all(scripts_found.values())
checks["maintenance_scripts"] = {
    "ok": scripts_ok,
    "label": "维护脚本 (压缩/合并/退役/汇编)",
    "detail": "全部就绪" if scripts_ok
        else f"缺失: {', '.join(n for n,ok in scripts_found.items() if not ok)}"
}

# 4. 插件（post_llm_call 钩子）
plugin_exists = PLUGINS.exists()
checks["plugin"] = {
    "ok": plugin_exists,
    "label": "Plugin snowfox-memory (post_llm_call 写入钩子)",
    "detail": "就绪" if plugin_exists else "不存在"
}

# 5. user/profile.md（自我认知）
up = M / "user" / "profile.md"
if up.exists():
    ux = up.stat().st_size
    checks["user_profile"] = {
        "ok": ux > 50,
        "label": "USER 自我认知 (user/profile.md)",
        "detail": f"{ux}B" if ux > 0 else "空文件"
    }
else:
    checks["user_profile"] = {"ok": False, "label": "USER 自我认知", "detail": "文件不存在"}

# 综合结论
oks = sum(1 for c in checks.values() if c["ok"])
total = len(checks)
status = "✅ ACTIVE" if oks == total else "⚠️ PARTIAL" if oks > 0 else "❌ INACTIVE"

report = {
    "status": status,
    "summary": f"{oks}/{total} 检查通过",
    "checks": checks
}
print(json.dumps(report, indent=2, ensure_ascii=False))
```

### 返回格式

无论成功失败，Agent **必须**向用户输出以下格式的状态报告：

```
🧠 SnowFox 五级记忆 — 部署状态

状态：✅ ACTIVE（或 ⚠️ PARTIAL / ❌ INACTIVE）
通过：5/8 检查

├─ ✅ 目录 F0 fixed       → 3 文件, 2KB
├─ ✅ 目录 L1 recent      → 12 文件, 48KB
├─ ⚠️ 目录 L2 summary     → 不存在
├─ ❌ ... 
│
└─ 🧩 插件 snowfox-memory → ✅ 就绪 / ❌ 不存在

操作建议：
- [PARTIAL] 运行部署脚本：xxx
- [INACTIVE] 参考下方「安装」章节
```

---

## 概述

将 Agent 的输入模式从 `[System Prompt] + [完整会话历史]` 改为 `[System Prompt] + [组装记忆] + [当前用户消息]`。

**核心原则：会话框仅用于显示，不作为输入来源。**

组装顺序：**self→F0→L3→USER→L2→L1**（`user/` 独立于五级记忆，不参与压缩循环）

## 目录结构

```
~/AppData/Local/hermes/memories/
├── fixed/              ← F0 固定记忆（10KB，永不压缩）
├── recent/             ← L1 近期流（50KB，超限压缩5KB→L2）
├── summary/            ← L2 中期摘要（100KB，超限合并10KB→L3）
├── long_term/          ← L3 长期记忆（50KB，超限退役5KB→L4）
├── user/               ← USER 自我认知（独立模块，不参与压缩）
│   └── profile.md
├── archive/            ← L4 归档区（不限，索引可查）
└── _assembled_context.md  ← 组装后的上下文（每轮加载）
```

## 使用方式

### 加载完整上下文

```python
read_file("~/AppData/Local/hermes/memories/_assembled_context.md")
```

### 查看当前容量

```python
import os
from pathlib import Path
HOME = Path(os.environ.get("HERMES_HOME", 
    Path.home() / "AppData" / "Local" / "hermes"))
M = HOME / "memories"
def kb(p): 
    d = Path(p)
    return sum(f.stat().st_size for f in d.glob("*.md")) / 1024 if d.exists() else 0
print(f"F0: {kb(M/'fixed'):.0f}KB  L1: {kb(M/'recent'):.0f}KB  L2: {kb(M/'summary'):.0f}KB  L3: {kb(M/'long_term'):.0f}KB  L4: {kb(M/'archive'):.0f}KB")
```

### F0 固定记忆操作

```python
# 写入（记住/待执行指令）
write_file("~/AppData/Local/hermes/memories/fixed/{名称}.md", "内容")

# 读取
read_file("~/AppData/Local/hermes/memories/fixed/{名称}.md")

# 删除（执行完/用户说忘了）
import os
os.remove(os.path.expanduser(
    "~/AppData/Local/hermes/memories/fixed/{名称}.md"))
```

## 输入架构

```
输入层                          存储层

[System Prompt] ──────────→ 系统提示（固定指令）
                                
[F0 固定记忆] ──────────→ memories/fixed/    10KB，永不压缩
                                
[USER 自我认知] ────────→ memories/user/     独立模块，不压缩不退役
                                
[L3 长期记忆] ──────────→ memories/long_term/ 50KB，超限退役5KB
         ↑
[L2 中期摘要] ──────────→ memories/summary/   100KB，超限合并10KB
         ↑
[L1 近期流] ───────────→ memories/recent/    50KB，超限压缩5KB
         ↑
[当前用户消息] ────────→ 本轮最新输入
                                
[L4 归档] ═══════════→ memories/archive/ 不限，索引可查

会话框历史 ──────────→ ❌ 不输入模型（仅显示）
```

## 写入机制

SnowFox 的 `plugins/snowfox-memory/` 插件在 `post_llm_call` 钩子中自动执行：

```python
_l1_path.write_text(
    f"## User\n\n{user_message or ''}\n\n"
    f"## Assistant\n\n{assistant_response or ''}\n\n",
    encoding="utf-8",
)
```

每轮对话的**用户输入 + 助手回复**完整写入 `memories/recent/`。

## 容量参数

| 层级 | 代号 | 上限 | 超限行为 | 每次释放 |
|------|------|------|---------|---------|
| 固定记忆 | F0 | 10KB | 永不压缩 | — |
| 近期流 | L1 | 50KB | 移最旧文件→L2 | 5KB |
| 中期摘要 | L2 | 100KB | LLM 压缩最旧→L3 摘要 | 10KB |
| 长期记忆 | L3 | 50KB | LLM 压缩最旧→L4 归档 | 5KB |
| 归档区 | L4 | 不限 | 不进上下文，索引检索 | — |
| 自我认知 | USER | 独立 | 不压缩不退役 | — |

通过 `.env` 调节（零代码）：

```bash
MEMORY_RECENT_KEEP_KB=45     # L1 超限保留量
MEMORY_SUMMARY_KEEP_KB=90    # L2 超限保留量
MEMORY_LONG_TERM_KEEP_KB=45  # L3 超限保留量
```

## 与传统方案对比

| 对比项 | 默认 Agent | SnowFox 五级记忆 |
|--------|-----------|-----------------|
| 输入上下文 | 完整会话历史（100-500KB） | 组装记忆（~50-100KB）+ 当前消息 |
| 跨会话连续性 | 无（新会话从零开始） | 有（L3+L2+L1 继承上下文） |
| 遗忘机制 | 上下文溢出时全丢 | 分层降级，逐级压缩 |
| 历史检索 | 只能当前会话搜索 | L4 归档索引可查所有历史 |
| 固定指令 | 需要每次都重复 | F0 固定记忆，永不丢失 |
| 容量控制 | 被动（被模型限制） | 主动（用户可调每级阈值） |
| 会话框增长 | 烧 token | 不影响（不输入模型） |
| 回复持久化 | 不自动保存 | 每轮自动写入 L1 |

## 常见陷阱

1. **路径错误**：记忆路径是 `~/AppData/Local/hermes/memories/`，**不是** `~/.hermes/memories/`
2. **read_file 路径**：要用绝对/展开路径 `read_file("~/AppData/Local/hermes/memories/_assembled_context.md")`，不是相对路径
3. **会话框已满不用重建**：会话框无限膨胀不影响 token——它压根不进模型
4. **F0 永不自动清理**：执行完指令或用户说忘后，必须手动删除 `fixed/` 下的文件
5. **压缩是容量驱动的**：不是时间驱动的——只有超过上限才会触发压缩
6. **SKILL.md 不是安装程序**：skill 是说明书，不是安装器。状态自检非 ✅ ACTIVE 时，需要跑部署脚本才能启用
