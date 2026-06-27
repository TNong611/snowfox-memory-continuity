# SnowFox 五级记忆连续性

> **会话框仅用于显示，输入 = 组装记忆 + 当前消息** — 一个零成本无限聊天框的设计

---

[📖 文章](文章.md) · [🤖 SKILL.md](SKILL.md) · [🔌 插件](plugins/snowfox-memory/) · [📜 维护脚本](scripts/)

## 是什么

SnowFox 的五级记忆架构让 AI 不用把整段历史对话都塞进上下文窗口，而是通过 `F0 → L1 → L2 → L3 → L4` 的层级记忆压缩管道，只保留最关键的信息。**会话框可以无限膨胀而不消耗 token。**

## 核心组件

| 层级 | 容量 | 超限后 | 内容 |
|------|------|--------|------|
| **F0** 固定记忆 | 10KB | 永不压缩 | 用户嘱咐的待办/要记住的事 |
| **L1** 近期流 | 50KB | 移最旧 5KB → L2 | 最近几轮完整对话 |
| **L2** 中期摘要 | 100KB | 移最旧 10KB → L3 | 压缩后的对话摘要 |
| **L3** 长期记忆 | 50KB | 移最旧 5KB → L4 | 跨会话的核心知识 |
| **USER** 自我认知 | 独立 | 不压缩不退役 | 你是谁（用户身份/偏好/环境） |
| **L4** 退役记忆 | 无限 | 已归档，不载入 | 不再活跃的历史记录 |

## 目录结构

```
snowfox-memory-continuity/
├── SKILL.md                         ← 面向 AI Agent 的一键部署 skill（v3.0.0）
├── README.md                        ← 本文档
├── 文章.md                           ← 面向人类的通俗讲解
├── plugins/
│   └── snowfox-memory/              ← L1 写入插件（post_llm_call 钩子）
│       ├── plugin.yaml              ← 插件定义
│       └── __init__.py              ← 每一轮自动写入 L1 存储
└── scripts/
    ├── mem_compress.py              ← L1→L2 压缩
    ├── mem_consolidate.py           ← L2→L3 合并
    ├── mem_retire.py                ← L3→L4 退役 + 索引
    └── memory_maintenance.py        ← 三合一 + 组装上下文（cron 入口）
```

## 快速部署

在 Hermes Agent 中加载 SKILL.md 即可一键部署：

```
skill_view(name='memory-continuity')
```

加载后自动检查部署状态，缺失组件自动创建补齐。

---

*作者：tnong & 雪狐 🦊 · 2026*
