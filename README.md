# SnowFox 五级记忆连续性

> **会话框仅用于显示，输入 = 组装记忆 + 当前消息** — 一个零成本无限聊天框的设计

---

[📖 文章](文章.md) · [🤖 SKILL.md](SKILL.md) · [🔌 插件](plugins/snowfox-memory/) · [📜 维护脚本](scripts/)

## 是什么

SnowFox 的五级记忆架构让 AI 不用把整段历史对话都塞进上下文窗口，而是通过 `F0 → L1 → L2 → L3 → L4` 的层级记忆压缩管道，只保留最关键的信息。**会话框可以无限膨胀而不消耗 token。**

## 核心组件

| 层级 | 文件 | 容量 | 超限后 | 内容 |
|------|------|------|--------|------|
| **SOUL** | SOUL.md | — | — | 系统行为规范（含"禁止 read_file"） |
| **USER** | user.md | 独立 | 不压缩 | 用户身份/偏好/环境 |
| **L4** | archive.md | 无限 | 不载入 | 退役历史归档 |
| **F0** | fixed.md | 10KB | 永不压缩 | 待办/重要指令 |
| **L3** | long_term.md | 50KB | 移最旧 5KB → L4 | 跨会话核心知识 |
| **L2** | summary.md | 100KB | 移最旧 10KB → L3 | 压缩后摘要 |
| **L1** | recent.md | 50KB | 移最旧 5KB → L2 | 最近完整对话 |

## 目录结构

```
snowfox-memory-continuity/
├── SKILL.md                         ← 面向 AI Agent 的一键部署 skill（v4.8.0）
├── README.md                        ← 本文档
├── 文章.md                           ← 面向人类的通俗讲解
├── plugins/
│   └── snowfox-memory/              ← L1 写入 + 内联组装插件（pre/post/session_end 三钩子）
│       ├── plugin.yaml              ← 插件定义（声明三钩子）
│       └── __init__.py              ← 内联组装 + 写入 + CJK 防重
├── scripts/
│   ├── mem_compress.py              ← L1→L2 压缩（recent.md → summary.md）
│   ├── mem_consolidate.py           ← L2→L3 合并（summary.md → long_term.md）
│   ├── mem_retire.py                ← L3→L4 退役（long_term.md → archive.md）
│   ├── memory_maintenance.py        ← 三合一入口（cron 调用）
│   ├── mem_config.py                ← 容量参数集中配置（MAX/KEEP_KB）
│   ├── mem_tasklog.py               ← 任务日志模块
│   ├── l4_index.py / l4_search.py   ← L4 语义索引（TF-IDF）构建与检索
│   ├── daily_tasklog_cleanup.sh     ← 每日 tasklog 压缩 cron
│   ├── gateway_watchdog.sh          ← 网关看门狗
│   ├── update_starfire.sh / patch_starfire.py ← 星火云端部署
│   └── ocr_image.ps1                ← 图片 OCR（Windows）
├── memories/                        ← 记忆文件快照（备份/移植源，运行时读写仍在 ~/AppData/Local/hermes/memories/）
│   ├── fixed.md / recent.md / summary.md / long_term.md / archive.md / user.md / tasklog.md
│   └── historical/                  ← 历史版本记忆快照归档
└── hermes-fork/                     ← Hermes fork 源码副本（已废弃，gitignore 排除，可删）
```

## 快速部署

在 Hermes Agent 中加载 SKILL.md 即可一键部署：

```
skill_view(name='memory-continuity')
```

加载后自动检查部署状态，缺失组件自动创建补齐。

---

*作者：tnong & 雪狐 🦊 · 2026*
