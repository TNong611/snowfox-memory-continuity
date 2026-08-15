# SnowFox Memory 统一包

记忆组件 + 记忆文件放一起，便于维护与移植。

## 目录结构

```
snowfox-memory/
├── SKILL.md                    # memory-continuity 技能（一键部署+维护）
├── scripts/                    # 工具链（mem_*.py 级联压缩、l4_*.py 语义索引）
│   ├── mem_config.py           # 容量参数集中配置（L1:50→45KB, L2:100→90KB, L3:50→45KB）
│   ├── mem_compress.py         # L1→L2（LLM 摘要）
│   ├── mem_consolidate.py      # L2→L3（LLM 二次蒸馏，去空去重去时间戳）
│   ├── mem_retire.py           # L3→L4（纯搬运）
│   ├── mem_maintain.py         # 级联维护 wrapper
│   ├── memory_maintenance.py   # 手动维护 + 组装上下文
│   ├── mem_tasklog.py          # 任务日志模块
│   ├── l4_index.py / l4_search.py  # L4 TF-IDF 语义索引
│   └── ...（含 .sh/.ps1 辅助脚本）
├── plugins-snowfox-memory/     # Hermes 插件（pre/post/session_end 三钩子，写入即触发压缩）
├── dsh-plugin/                 # DSH → Hermes 记忆桥接插件（snowfox-sync.mjs）
└── memories/                   # 记忆文件快照
    ├── fixed.md                # F0 固定记忆（永不压缩）
    ├── recent.md               # L1 完整近期对话
    ├── summary.md              # L2 中期摘要
    ├── long_term.md            # L3 长期记忆
    ├── archive.md              # L4 归档
    ├── user.md / USER.md       # 用户画像
    ├── tasklog.md              # 任务日志
    └── _assembled_context.md   # 组装上下文快照
```

## 同步到 Hermes

```bash
# 工具链 → 运行目录
cp -r scripts/* ~/AppData/Local/hermes/scripts/
# 插件
cp -r plugins-snowfox-memory ~/AppData/Local/hermes/plugins/snowfox-memory
```

## 默认位置：DeepSeek Harness

记忆组件默认位于 `D:\AI\deepseek-harness\snowfox-memory`（git 跟踪，随仓库版本化）。
`D:\AI\snowfox-memory` 为运行时工作副本（junction 真源指向其 `memories/`）。

```bash
cd /d/AI/deepseek-harness
git add snowfox-memory
git commit -m "chore: sync snowfox-memory"
```

## 记忆文件唯一真源（junction）

Hermes 的 `~/AppData/Local/hermes/memories` 是指向 `D:\AI\snowfox-memory\memories` 的 **junction**，
运行中的 Hermes（内置 memory 工具、snowfox-memory 插件、mem_*.py 脚本）全部读写本目录。

```powershell
# 重建 junction（如丢失）
Remove-Item "C:\Users\tnong\AppData\Local\hermes\memories" -Force
New-Item -ItemType Junction -Path "C:\Users\tnong\AppData\Local\hermes\memories" -Target "D:\AI\snowfox-memory\memories"
```

harness 侧为组件默认位置；`memories/` 是运行时快照，随提交更新，如需单独备份用 `cp -r memories/` 复制即可。
