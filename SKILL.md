---
name: memory-continuity
description: "SnowFox 五级记忆 - 单文件架构。禁止 read_file 循环。"
version: 4.0.0
author: tnong & 雪狐
date: 2026-06-28
tags: [memory, agent-input, hierarchical-memory, single-file, snowfox, hermes]
---

# SnowFox 五级记忆 - 单文件架构

**指令：加载后立即执行部署状态自检。**

## 架构概述

输入模式：[SOUL.md] + [组装记忆] + [当前消息]
会话框仅用于显示，不作为输入来源。

| 层级 | 文件 | 上限 |
|------|------|------|
| SOUL | SOUL.md | - |
| USER | user.md | 独立 |
| L4 | archive.md | 不限 |
| F0 | fixed.md | 10KB |
| L3 | long_term.md | 50KB |
| L2 | summary.md | 100KB |
| L1 | recent.md | 50KB |

### 组装顺序
SOUL.md + USER + L4 + F0 + L3 + L2 + L1 + 当前消息

## 核心改动 (v3->v4)

| 方面 | v3 (目录版) | v4 (单文件版) |
|------|------------|---------------|
| 存储 | 每级目录 + 散文件 | 每级一个 .md 单文件 |
| 写入 | post_llm_call 写 recent/*.md | post_llm_call 追加 recent.md |
| 组装 | 调外部 Python 脚本 | 插件内联组装 |
| 指纹 | re.sub(正则) | str.isalnum() 支持中文 |
| 去重 | 内容相同被拦截 | 每轮时间戳不同 |
| 钩子 | post_llm_call | pre + post + session_end |
| SOUL | 让 agent read_file | 禁止 read_file |

## 插件行为
### pre_llm_call
- 提取上轮对话，追加到 recent.md
- str.isalnum() 指纹防重（保留中文）
- 调用 _rebuild_assembly() 内联组装

### post_llm_call
- 回复生成后立即写入 recent.md

### _rebuild_assembly()
- 不加 subprocess，全部内联
- 写入时间戳头 (built: ...)
- 写入 _assembly_version.txt 版本指纹
- 顺序：USER + L4 + F0 + L3 + L2 + L1
- L2 截断至 90KB，每段 150 字

## SOUL.md 规范
- 会话框只显示，不作为输入
- **禁止调用 read_file 读取任何记忆文件**
- 所有信息已在输入中，不需要验证

## 容量管理
| 层级 | 上限 | 超限行为 |
|------|------|---------|
| F0 | 10KB | 不压缩 |
| L1 | 50KB | 截断最旧段至 L2 |
| L2 | 100KB | 截断最旧段至 L3 |
| L3 | 50KB | 截断最旧段至 L4 |
| L4 | 不限 | 不进上下文 |
| USER | 独立 | 不压缩 |

## 常见陷阱

1. **read_file 死循环**：SOUL 禁止 read_file，插件每轮重建写入不同时间戳。

2. **中文指纹**：str.isalnum() 代替 re.sub，支持中文。

3. **f-string 引号冲突**：条件表达式提取为变量再拼 f-string。

4. **重启生效**：修改后 /new + hermes gateway restart。

5. **路径正确**：memories/recent.md 而非 memories/recent/。

6. **F0 手动管理**：永不自动清理。
