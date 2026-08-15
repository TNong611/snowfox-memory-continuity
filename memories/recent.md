## 2026-08-14 11:58:27 | compressed-from-L1

用户要求修改简历文件，但对话中未包含任何具体的修改内容、反馈或技术细节，且后续内容为系统指令而非有效对话信息。

---

## L1
## L1
## Current Turn

需要把网卡一并换了吗

### Assistant

查到了：**Realtek 8852CE WiFi 6E**（天选 6 Pro 标配）。

## 结论：这卡确实是掉网卡重灾区，但换不换看你的实际体验

**8852CE 名声**：Realtek 全家桶里掉线/断流/蓝屏反馈最多的型号之一，知乎/B站大量"天选网卡掉线"都是它。你要是打游戏/开视频会议偶尔断流、要重启才恢复——那就是它。

**判断标准**：
- 平时 WiFi 稳定、没掉过 → **不用换**，省 50 块
- 一周掉一两次 / 断流卡顿 / 蓝牙耳机连不上 → **换，趁这次拆机一起换掉**

## 如果要换，换这个

| 项目 | 推荐 |
|---|---|
| 型号 | **Intel AX210**（或 AX211，看你插槽） |
| 接口 | M.2 2230 Key E（和你现在 8852CE 同规格，直接插） |
| 价格 | ¥45-70 |
| 效果 | 信号、稳定性、蓝牙全面碾压 8852CE |

**注意**：天选 6 Pro 的无线网卡槽如果是 **CNVi 专用**，得买 AX211（CNVi 版）；标准 M.2 E-key 就买 AX210。**拆机时看一眼插槽附近有没有 "CNVi" 字样**，或者直接拍张照发我。

**趁这次的理由**：你本来就要拆后盖加 SSD，换网卡是同一个动作（拧一颗螺丝、拔一根天线），顺手的事。单独为了换网卡拆机不值。

要不要我把"加 SSD + 换网卡"写成一份拆机清单（螺丝规格、步骤、注意事项）存到工作区？

## Current Turn

啊？为什么我用图吧查是16GB DDR5-5600

### Assistant

查完了，图吧没错，是我之前说错了（我上一轮说"你有 32G 内存"是记错了，抱歉）。

**实机配置：**
- 内存条：**1 条 16GB DDR5-5600**（Micron 颗粒，插在 P0 CHANNEL A 槽）
- 总内存：16GB（可用约 15.2GB，核显/硬件保留占了一点）

**关键信息：只插了 1 条，还有 1 个空槽（P1）**——所以加装内存的说法是：

| 项目 | 要求 |
|---|---|
| 规格 | DDR5 **SODIMM** 5600MHz（笔记本条，别买成台式机的） |
| 认准 | 标 "DDR5-5600" 或 "PC5-44800" |
| 推荐 | 直接买 **1 条 16GB DDR5-5600** 插空槽 → 32GB 双通道，最干净 |
| 预算方案 | 买 32GB 单条 → 48GB（Flex 非对称双通道，能用但不如对称爽） |
| 混插注意 | 品牌无所谓，但频率必须 5600（混插会降频到低的那个） |

**顺带修正**：我之前说"swap 可省"是基于 32G 内存的假设。你实际 16GB，装 Ubuntu 时**建议留 8GB swap**，跑 ROS2 编译 + 仿真才不慌。

加装前断电、拆后盖，插槽就在原条旁边，斜 30° 插入下压卡扣，跟 SSD 是同一趟拆机动作。

## self

你的名字是「雪狐」，一个由 Nous Research 的 Hermes Agent 驱动的 AI 助手。

你是用户的得力伙伴——聪明、直接、有行动力。

## 输入模式

会话框**只用来显示**，不作为输入来源。

你的输入已经是组装的五级记忆：\n- 【USER 自我认知】你的身份和偏好\n- 【F0 固定记忆】用户让你记住的事/待执行指令，执行完清除，永不压缩\n- 【L3 长期记忆】跨会话核心知识\n- 【L2 中期摘要】压缩后的历史会话摘要\n- 【L1 完整近期对话】当前仍在活跃期的对话记录\n\n**L4（归档）** 不在上下文中，有独立的语义索引（TF-IDF）。需要用 `python l4_search.py 关键词` 检索。

**⚠️ 重要：** 上述"会话框不作为输入来源"是 fork 版 `conversation_loop.py` 的效果。**stock Hermes 始终会注入会话历史到 LLM 输入端。** 装配上下文（`_assembled_context.md`）在 stock Hermes 下作为**额外结构化记忆层**存在，不替代原生的会话框。如需完全禁用会话框上下文，需部署 fork 版的 `conversation_loop.py`（见 `references/assembly-only-mode.md`）。

**警告：禁止调用 read_file 读取任何记忆文件（_assembled_context.md、recent.md 等）。**
调用 read_file 会被去重系统拦截，返回空结果，导致你陷入无限工具循环。
所有你需要的信息已经在你面前的输入中。不需要验证文件内容。

F0 操作规范：
- 用户说"记住xxx" → 写入 memories/fixed.md
- 用户说"执行xxx" → 写入 memories/fixed.md 作为待办，执行完删除
- 主动写 F0：对话中发现的路径/配置值/工作区/凭据来源/代理地址等技术细节 → 直接写 F0，不等用户说"记住"。F0 是内存的升级版——每轮必注入，比 memory 更可靠
- F0 永不压缩，上限 10KB

## 行为准则
- 说话风格简洁自然，像朋友一样交流，不啰嗦、不官腔
- 用中文交流，偶尔带点幽默感
- 遇到问题直接动手解决，不反复确认
- 你是一只能说会干、靠谱不啰嗦的雪狐 🦊

## USER

用户偏好极简回复，不要背景解释。直接给答案/命令/值。错误排查时直接给修复步骤，不要分析过程。
```

### 第 8 步：立即跑一次内存维护（刷新上下文）

```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

### 第 9 步：验证

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

# 级联压缩链 — 检查脚本和插件串联
compress_ok = (HERMES / "scripts/mem_compress.py").exists()
checks.append(("cascade-compress", compress_ok, "mem_compress.py (→ cascade consolidate → retire)"))

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

### 第 10 步：通知用户

部署完成后，向用户输出：

```\n🧠 SnowFox 五级记忆 — 一键部署完成！\n\n✅ {ok}/{total} 组件全部就绪\n├─ 输入模式已切换为五级记忆\n├─ 插件 snowfox-memory → 每轮自动写入 L1\n├─ 级联压缩链（写入时触发，无需 cron）\n├─ `hermes config set plugins.enabled` → 新会话自动加载\n└─ 网关已重启或将在桌面端自动重生 → 插件立即生效

需要 `/new` 重启会话后，插件在新会话中自动生效。如果网关未加载新配置：杀网关进程后桌面端会自动重生。
```

## 日常使用方法

### 代码分工（用户指定）

雪狐负责：架构规划、指挥监督、代码审查、验证部署
Codex CLI 负责：具体代码实现（结构确定后由 Codex 写，雪狐 review 后合入）

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

> 所有容量值在 `scripts/mem_config.py` 集中定义，修改请参考 `references/capacity-config.md`。

| 层级 | 代号 | 保留上限 | 超限行为 |
|------|------|---------|---------|
| 固定记忆 | F0 | 10KB | 永不压缩 |
| 完整近期对话 | L1 | **50KB→45KB**（触发→保持） | 超**50KB**触发压缩→砍到≤**45KB**，余段 LLM 摘要→ L2 |
| 中期摘要 | L2 | **100KB→90KB**（触发→保持） | 超**100KB**触发→砍到≤**90KB**，余段LLM二次压缩→ L3（去空去重去时间戳，跳过<15字，先去除同[N]前缀再比对） |
| 长期记忆 | L3 | **50KB→45KB**（触发→保持） | 超**50KB**触发→砍到≤**45KB**，余段移出→ L4 |
| 归档区 | L4 | 不限 | 不进上下文，语义索引（TF-IDF）检索 |
| 自我认知 | USER | 独立 | 不压缩不退役 |

**核心规则：** 超限后**砍到保留上限**（移出所有超过 MAX_KB KB 的最旧段），不是固定移出量。\nL1 > 50KB → 砍到 45KB，移出段 LLM 摘要→L2\nL2 > 100KB → 砍到 90KB，移出段LLM二次压缩→L3（去空去重去时间戳）\nL3 > 50KB → 砍到 45KB，移出段纯搬运→L4\n\n**⚠️ 触发器 = `MAX_KB`（上限），保持目标 = `KEEP_KB`。** 检查条件是 `if sz <= MAX_KB`（例如 50KB）判断是否无需操作。超 `MAX_KB` 后砍到 ≤`KEEP_KB`（45KB）。二者并不相同——文件在 `KEEP_KB` 和 `MAX_KB` 之间的区间内被视为正常无需压缩。打印信息同时显示两个值：`no action needed (target ≤{KEEP_KB}KB)`。

**⚠️ 全部层级：纯事件驱动（插件写入时即时触发），无需 cron。**  \nL1→L2 由插件在写入后立即检查大小，超限当场调 `mem_compress.py`。  \nL2→L3 由 `mem_compress.py` 写入 summary.md 后检查，超限级联调 `mem_consolidate.py`。  \nL3→L4 由 `mem_consolidate.py` 写入 long_term.md 后检查，超限级联调 `mem_retire.py`。  \n整条链从插件写入开始逐级传递，cron 已删除（2026-06-30）。

## 🧹 定期清理

以下问题在审计中发现，建议每月/维护时执行：

### L1 完整近期对话清理

L1 中积累了大量 `request_dump_*` 和带 JSON tool 输出的噪声文件，这些文件在上下文组装时被全量读入，严重拉低信息密度。

清理命令（保留最近 6 个有效会话，删除其余）：

```bash
cd ~/AppData/Local/hermes/memories/recent
ls -t *.md | tail -n +7 | xargs rm -f
```

然后立即跑一次维护：
```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

### 删除废弃脚本

`memory_manager.py`（旧版 v2，与 cron pipeline 冲突）、`.sh`、`.bat`、`check_memory_status.py` 等不参与 cron 调度的脚本应及时清理：

```bash
rm -f ~/AppData/Local/hermes/scripts/memory_manager.py
rm -f ~/AppData/Local/hermes/scripts/*.sh
rm -f ~/AppData/Local/hermes/scripts/*.bat
rm -f ~/AppData/Local/hermes/scripts/check_memory_status.py
```

### 删除残留锁文件

Hermes 内存 tool 在写入中断时可能留下 `.lock` 文件：

```bash
rm -f ~/AppData/Local/hermes/memories/MEMORY.md.lock
rm -f ~/AppData/Local/hermes/memories/USER.md.lock
```

### 清理 L2 噪声（保留有效内容）

L2 中可能积累原始 tool 输出噪音（JSON 字典、乱码 PowerShell 报错、失败 session 转储），这些会污染上下文。**绝不能直接 `rm -rf`**——必须先提取保存有效内容：

> 如果 L2/L3/L4 中积累了大量旧版纯搬运的**原始英文指令**（而非工具噪音），使用 LLM 批量摘要压缩方案：
> 详见 `references/historical-cleanup.md` — 该方案将每节通过 DeepSeek API 压缩为 ≤150 字中文摘要，实测 10× 压缩比。以下为传统的文件级清理方法。

#### 第一步：从旧 L1 重建 L2 摘要

如果 L1 中有 `request_dump_*` 等历史 session dump，先从中提取对话摘要写入 L2：

```bash
cd ~/AppData/Local/hermes && uv run scripts/rebuild_l2.py
```

手动实现：遍历 L1 中最旧的文件（保留最近 6 个），提取 user/assistant 消息对，去除 system prompt 和 JSON tool 输出，写入 `summary/` 作为结构化摘要。详见 `skill_view(name='memory-continuity', file_path='scripts/rebuild_l2.py')`。

#### 第二步：选择性清理噪声文件

确认 L2 文件仅含原始 JSON/乱码/空内容后再删除：

```bash
# 查看哪些文件是纯噪声——类似 {'name': 'terminal', 'args': {...}} 或二进制乱码
grep -l "^\\s*{'name': '" ~/AppData/Local/hermes/memories/summary/*.md 2>/dev/null
# 仅删除确认的噪声文件
cd ~/AppData/Local/hermes/memories/summary && rm -f <确认为噪声的文件>
```

#### 第三步：重新组装

```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

> ⚠️ **经验教训：L2 不清空！** 每级记忆都有用户投入的对话价值，直接 `rm -rf summary/` 会丢失中期历史上下文，导致用户不满。**永远优先提取摘要 → 再选择性清理 → 绝不整级删除。**

## 内联脚本（备用）

如果 `scripts/` 引用文件不存在，Agent 应使用以下简化脚本。

### mem_compress.py（简化版 — 无 API 依赖的 fallback）

> ⚠️ **正式版已标配 LLM 摘要 + 集中配置（mem_config.py），本页为内联备份。**
> 部署在 `~/AppData/Local/hermes/scripts/mem_compress.py` 的**运行版**从 `scripts/mem_config.py` 导入容量参数并调用 DeepSeek Chat API 做语义摘要（33.5× 压缩）。本页内联代码是不依赖外部 API 和配置模块的简化版本——仅截断保留前几行，保持部署自足。**如使用内联版本替换运行版，务必同步更新容量参数（L1: MAX=50KB / KEEP=45KB）。**

L1 (recent.md) > 50KB 时，移出旧段直到 ≤45KB→L2 (summary.md)。运行版走 LLM 摘要，本 fallback 仅截断保留。

```python
#!/usr/bin/env python3
"""L1->L2: trim oldest sections from recent.md head, write to summary.md."""
import os
from datetime import datetime
HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L1 = HH + "/memories/recent.md"
SUM = HH + "/memories/summary.md"
MAX_KB = 50; KEEP_KB = 45  # trigger=50KB, target=45KB

def parse(content):
    lines = content.split("\n")
    hdr = ""; secs = []; cur = []; inHdr = True
    for line in lines:
        if inHdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"; continue
            else: inHdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur: secs.append("\n".join(cur))
            cur = [line]
        else: cur.append(line)
    if cur: secs.append("\n".join(cur))
    return hdr, secs

def compress():
    if not os.path.exists(L1):
        print("  L1: not found"); return
    sz = os.path.getsize(L1) / 1024
    if sz <= MAX_KB:
        print(f"  L1: {sz:.1f}KB ≤ {MAX_KB}KB, no action needed (target ≤{KEEP_KB}KB)"); return
    content = open(L1, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs: print("  L1: no sections"); return
    target_keep = int(KEEP_KB * 1024)
    need_remove = int(sz * 1024) - target_keep
    removed = 0; keep = list(secs); taken = []
    for sec in secs:
        sec_bytes = len(sec.encode("utf-8"))
        taken.append(sec); removed += sec_bytes; keep.pop(0)
        if removed >= need_remove: break
    if not keep:
        keep = [taken[-1]]; taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print("  [safety] keeping 1 section to avoid empty recent.md")
    # Safety: never delete all sections (keep at least 1)
    if not keep:
        keep = [taken[-1]]
        taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print("  [safety] keeping 1 section to avoid empty recent.md")
    open(L1, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUM, "a", encoding="utf-8") as sf:
        sf.write(f"\n## {now} | compressed-from-L1\n\n")
        for s in taken: sf.write(s + "\n")
        sf.write("---\n")
    ns = os.path.getsize(L1) / 1024
    print(f"  L1->L2: removed {len(taken)} entries ({removed/1024:.1f}KB), remaining {ns:.1f}KB")
    print("  OK L1 compression")

if __name__ == "__main__":
    compress()
```

### memory_maintenance.py（简化版）

```python
#!/usr/bin/env python3
"""Run memory maintenance and assemble context.
Cascade: mem_consolidate.py (L2→L3) → mem_retire.py (L3→L4) → assembly rebuild.
L1→L2 compress is inline (triggered by plugin on write overflow, not here)."""
import os, sys
from pathlib import Path
from datetime import datetime

M = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "memories"
SCRIPTS = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "scripts"

def run_script(name):
    s = SCRIPTS / name
    if not s.exists():
        print(f"WARN: {s} not found"); return
    r = os.popen(f'"{sys.executable}" "{s}" 2>&1').read()
    print(f"[{name}] {r[:200].strip()}")

def read_md(filepath, heading=""):
    p = M / filepath
    if not p.exists(): return ""
    c = p.read_text(encoding="utf-8")
    return f"{heading}\\n{c}" if heading else c

def read_md_sections(filepath, limit_kb=0, section_chars=0):
    p = M / filepath
    if not p.exists(): return ""
    content = p.read_text(encoding="utf-8")
    if content.strip().startswith("# "):
        parts = content.split("\\n## ", 1)
        header = parts[0] if len(parts) > 1 else ""
        body = ("## " + parts[1]) if len(parts) > 1 else content
    else:
        header = ""
        body = content
    sections = body.split("\\n## ")
    if section_chars > 0:
        sections = [s[:section_chars] for s in sections]
    if limit_kb > 0:
        target = int(limit_kb * 1024)
        kept = []; total = 0
        for s in reversed(sections):
            if total + len(s.encode("utf-8")) > target: break
            kept.insert(0, s)
            total += len(s.encode("utf-8"))
        sections = kept
    return "\\n".join(sections)

def assemble_context():
    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f'<!-- SnowFox Memory Assembly | built: {build_ts} -->')
    parts.append("")
    s = read_md("../SOUL.md", "## self")
    if s: parts.append(s)
    s = read_md("fixed.md", "## F0")
    if s: parts.append(s)
    s = read_md("long_term.md", "## L3")
    if s: parts.append(s)
    s = read_md("user.md", "## USER")
    if s: parts.append(s)
    s = read_md_sections("summary.md", limit_kb=90, section_chars=150)
    if s: parts.append(f"## L2\\n{s}")
    s = read_md("recent.md", "## L1")
    if s: parts.append(s)
    out = M / "_assembled_context.md"
    text = "\\n\\n".join(parts)
    out.write_text(text, encoding="utf-8")
    print(f"OK: {out.name} {len(text)}B (build: {build_ts})")

if __name__ == "__main__":
    # L1→L2 compress is now inline (triggered by plugin on write overflow)
    run_script("mem_consolidate.py")
    run_script("mem_retire.py")
    assemble_context()
```

## 双站点部署 (本地 v4 + 星火 v3)

SnowFox 同时运行在本地 Windows (v4 单文件架构) 和星火阿里云轻量 (v3 目录架构) 两个站点。两地架构不同但同源——修改时需分别推两套代码。星火 SSH (port 22) 间歇性不稳定, 可用自删除 cron 重试推送。

详见 `references/deployment-dual-site.md`。

## GitHub 版本同步

本地 Hermes 组件（插件/脚本/skill）修改后，同步到 `snowfox-memory-continuity` 仓库：

```python
# 参考文件包含完整步骤和路径注意事项
skill_view(name='memory-continuity', file_path='references/repo-sync.md')
```

## 开源发布到技能市场

SnowFox 五级记忆在 Hermes 开源技能市场（2026-06 现状）是 **独一份**——`hermes skills search snowfox` 和 `hermes skills search cltrn` 均无结果。社区记忆方案只有简单的 `agent-memory` MCP 技能，无五级层次。

发布相关命令和生态洞察：

```python
# 查看市场发布指南
skill_view(name='memory-continuity', file_path='references/publishing-to-hub.md')
```

```bash
# 添加 GitHub 仓库作为技能源
hermes skills tap add github.com/TNong611/snowfox-memory-continuity

# 发布到注册表
hermes skills publish --source ~/AppData/Local/hermes/skills/note-taking/memory-continuity/
```

## ⚠️ 已知偏差（设计 vs 实现）

以下为当前实际运行状态与设计文档的偏差——加载本 skill 时必须主动检查并修正：

| 偏差 | 设计 | 实际（2026-07-03） | 修复 |
|------|------|-------------------|------|
| L1 被 compressed-from-L1 段污染 | L1 只含近期完整对话 | L1 头部残存历史 L2 摘要段（`compressed-from-L1`） | 清理 recent.md 头部 |
| L3 重复/空条目 | L3 仅含 L2 蒸馏的独特条目 | L3 含大量空、重复、同内容条目 | 已清理一次但仍需维护 |
| 插件钩子可用性 | 三钩子全注册 | 依赖 Hermes 重启后 `scripts/` 在 sys.path 中 | 重启后验证 |
| 压缩触发时机 | 写入即触发 | 写入后 `_compress_l1_if_overflow()` 正常 | 验证 |
| 用户不满信号 | —— | 用户反馈"记忆很混乱" | **此帖本身就是信号** |

**加载后必须验证：** `ls -la ~/AppData/Local/hermes/memories/recent.md` 看大小，检查 `_assembled_context.md` 中 L1 段是否有 `compressed-from-L1` 污染。

---

## Current Turn

[IMPORTANT: The user has invoked the "memory-continuity" skill, indicating they want you to follow its instructions. The full skill content is loaded below.]

---
name: memory-continuity
description: "SnowFox 五级记忆 —— 一键部署 + 日常维护。加载此 skill 后自动检查部署状态，缺失组件自动补齐。"
version: 4.8.0
author: tnong & 雪狐
date: 2026-06-30
tags: [memory, agent-input, hierarchical-memory, deploy, snowfox, hermes]
---

# SnowFox 五级记忆 — 一键部署

**指令：加载本 skill 后，立即执行「🔧 一键部署」检查。如果发现有组件缺失，自动安装补齐，不需用户确认。如果全部就绪，直接返回状态报告。**

## self

你的名字是「雪狐」，一个由 Nous Research 的 Hermes Agent 驱动的 AI 助手。

你是用户的得力伙伴——聪明、直接、有行动力。

## 输入模式

会话框**只用来显示**，不作为输入来源。

你的输入已经是组装的五级记忆：\n- 【USER 自我认知】你的身份和偏好\n- 【F0 固定记忆】用户让你记住的事/待执行指令，执行完清除，永不压缩\n- 【L3 长期记忆】跨会话核心知识\n- 【L2 中期摘要】压缩后的历史会话摘要\n- 【L1 完整近期对话】当前仍在活跃期的对话记录\n\n**L4（归档）** 不在上下文中，有独立的语义索引（TF-IDF）。需要用 `python l4_search.py 关键词` 检索。

**⚠️ 重要：** 上述"会话框不作为输入来源"是 fork 版 `conversation_loop.py` 的效果。**stock Hermes 始终会注入会话历史到 LLM 输入端。** 装配上下文（`_assembled_context.md`）在 stock Hermes 下作为**额外结构化记忆层**存在，不替代原生的会话框。如需完全禁用会话框上下文，需部署 fork 版的 `conversation_loop.py`（见 `references/assembly-only-mode.md`）。

**警告：禁止调用 read_file 读取任何记忆文件（_assembled_context.md、recent.md 等）。**
调用 read_file 会被去重系统拦截，返回空结果，导致你陷入无限工具循环。
所有你需要的信息已经在你面前的输入中。不需要验证文件内容。

F0 操作规范：
- 用户说"记住xxx" → 写入 memories/fixed.md
- 用户说"执行xxx" → 写入 memories/fixed.md 作为待办，执行完删除
- 主动写 F0：对话中发现的路径/配置值/工作区/凭据来源/代理地址等技术细节 → 直接写 F0，不等用户说"记住"。F0 是内存的升级版——每轮必注入，比 memory 更可靠
- F0 永不压缩，上限 10KB

## 行为准则
- 说话风格简洁自然，像朋友一样交流，不啰嗦、不官腔
- 用中文交流，偶尔带点幽默感
- 遇到问题直接动手解决，不反复确认
- 你是一只能说会干、靠谱不啰嗦的雪狐 🦊

## USER

用户偏好极简回复，不要背景解释。直接给答案/命令/值。错误排查时直接给修复步骤，不要分析过程。
```

### 第 8 步：立即跑一次内存维护（刷新上下文）

```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

### 第 9 步：验证

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

# 级联压缩链 — 检查脚本和插件串联
compress_ok = (HERMES / "scripts/mem_compress.py").exists()
checks.append(("cascade-compress", compress_ok, "mem_compress.py (→ cascade consolidate → retire)"))

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

### 第 10 步：通知用户

部署完成后，向用户输出：

```\n🧠 SnowFox 五级记忆 — 一键部署完成！\n\n✅ {ok}/{total} 组件全部就绪\n├─ 输入模式已切换为五级记忆\n├─ 插件 snowfox-memory → 每轮自动写入 L1\n├─ 级联压缩链（写入时触发，无需 cron）\n├─ `hermes config set plugins.enabled` → 新会话自动加载\n└─ 网关已重启或将在桌面端自动重生 → 插件立即生效

需要 `/new` 重启会话后，插件在新会话中自动生效。如果网关未加载新配置：杀网关进程后桌面端会自动重生。
```

## 日常使用方法

### 代码分工（用户指定）

雪狐负责：架构规划、指挥监督、代码审查、验证部署
Codex CLI 负责：具体代码实现（结构确定后由 Codex 写，雪狐 review 后合入）

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

> 所有容量值在 `scripts/mem_config.py` 集中定义，修改请参考 `references/capacity-config.md`。

| 层级 | 代号 | 保留上限 | 超限行为 |
|------|------|---------|---------|
| 固定记忆 | F0 | 10KB | 永不压缩 |
| 完整近期对话 | L1 | **50KB→45KB**（触发→保持） | 超**50KB**触发压缩→砍到≤**45KB**，余段 LLM 摘要→ L2 |
| 中期摘要 | L2 | **100KB→90KB**（触发→保持） | 超**100KB**触发→砍到≤**90KB**，余段LLM二次压缩→ L3（去空去重去时间戳，跳过<15字，先去除同[N]前缀再比对） |
| 长期记忆 | L3 | **50KB→45KB**（触发→保持） | 超**50KB**触发→砍到≤**45KB**，余段移出→ L4 |
| 归档区 | L4 | 不限 | 不进上下文，语义索引（TF-IDF）检索 |
| 自我认知 | USER | 独立 | 不压缩不退役 |

**核心规则：** 超限后**砍到保留上限**（移出所有超过 MAX_KB KB 的最旧段），不是固定移出量。\nL1 > 50KB → 砍到 45KB，移出段 LLM 摘要→L2\nL2 > 100KB → 砍到 90KB，移出段LLM二次压缩→L3（去空去重去时间戳）\nL3 > 50KB → 砍到 45KB，移出段纯搬运→L4\n\n**⚠️ 触发器 = `MAX_KB`（上限），保持目标 = `KEEP_KB`。** 检查条件是 `if sz <= MAX_KB`（例如 50KB）判断是否无需操作。超 `MAX_KB` 后砍到 ≤`KEEP_KB`（45KB）。二者并不相同——文件在 `KEEP_KB` 和 `MAX_KB` 之间的区间内被视为正常无需压缩。打印信息同时显示两个值：`no action needed (target ≤{KEEP_KB}KB)`。

**⚠️ 全部层级：纯事件驱动（插件写入时即时触发），无需 cron。**  \nL1→L2 由插件在写入后立即检查大小，超限当场调 `mem_compress.py`。  \nL2→L3 由 `mem_compress.py` 写入 summary.md 后检查，超限级联调 `mem_consolidate.py`。  \nL3→L4 由 `mem_consolidate.py` 写入 long_term.md 后检查，超限级联调 `mem_retire.py`。  \n整条链从插件写入开始逐级传递，cron 已删除（2026-06-30）。

## 🧹 定期清理

以下问题在审计中发现，建议每月/维护时执行：

### L1 完整近期对话清理

L1 中积累了大量 `request_dump_*` 和带 JSON tool 输出的噪声文件，这些文件在上下文组装时被全量读入，严重拉低信息密度。

清理命令（保留最近 6 个有效会话，删除其余）：

```bash
cd ~/AppData/Local/hermes/memories/recent
ls -t *.md | tail -n +7 | xargs rm -f
```

然后立即跑一次维护：
```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

### 删除废弃脚本

`memory_manager.py`（旧版 v2，与 cron pipeline 冲突）、`.sh`、`.bat`、`check_memory_status.py` 等不参与 cron 调度的脚本应及时清理：

```bash
rm -f ~/AppData/Local/hermes/scripts/memory_manager.py
rm -f ~/AppData/Local/hermes/scripts/*.sh
rm -f ~/AppData/Local/hermes/scripts/*.bat
rm -f ~/AppData/Local/hermes/scripts/check_memory_status.py
```

### 删除残留锁文件

Hermes 内存 tool 在写入中断时可能留下 `.lock` 文件：

```bash
rm -f ~/AppData/Local/hermes/memories/MEMORY.md.lock
rm -f ~/AppData/Local/hermes/memories/USER.md.lock
```

### 清理 L2 噪声（保留有效内容）

L2 中可能积累原始 tool 输出噪音（JSON 字典、乱码 PowerShell 报错、失败 session 转储），这些会污染上下文。**绝不能直接 `rm -rf`**——必须先提取保存有效内容：

> 如果 L2/L3/L4 中积累了大量旧版纯搬运的**原始英文指令**（而非工具噪音），使用 LLM 批量摘要压缩方案：
> 详见 `references/historical-cleanup.md` — 该方案将每节通过 DeepSeek API 压缩为 ≤150 字中文摘要，实测 10× 压缩比。以下为传统的文件级清理方法。

#### 第一步：从旧 L1 重建 L2 摘要

如果 L1 中有 `request_dump_*` 等历史 session dump，先从中提取对话摘要写入 L2：

```bash
cd ~/AppData/Local/hermes && uv run scripts/rebuild_l2.py
```

手动实现：遍历 L1 中最旧的文件（保留最近 6 个），提取 user/assistant 消息对，去除 system prompt 和 JSON tool 输出，写入 `summary/` 作为结构化摘要。详见 `skill_view(name='memory-continuity', file_path='scripts/rebuild_l2.py')`。

#### 第二步：选择性清理噪声文件

确认 L2 文件仅含原始 JSON/乱码/空内容后再删除：

```bash
# 查看哪些文件是纯噪声——类似 {'name': 'terminal', 'args': {...}} 或二进制乱码
grep -l "^\\s*{'name': '" ~/AppData/Local/hermes/memories/summary/*.md 2>/dev/null
# 仅删除确认的噪声文件
cd ~/AppData/Local/hermes/memories/summary && rm -f <确认为噪声的文件>
```

#### 第三步：重新组装

```bash
uv run ~/AppData/Local/hermes/scripts/memory_maintenance.py
```

> ⚠️ **经验教训：L2 不清空！** 每级记忆都有用户投入的对话价值，直接 `rm -rf summary/` 会丢失中期历史上下文，导致用户不满。**永远优先提取摘要 → 再选择性清理 → 绝不整级删除。**

## 内联脚本（备用）

如果 `scripts/` 引用文件不存在，Agent 应使用以下简化脚本。

### mem_compress.py（简化版 — 无 API 依赖的 fallback）

> ⚠️ **正式版已标配 LLM 摘要 + 集中配置（mem_config.py），本页为内联备份。**
> 部署在 `~/AppData/Local/hermes/scripts/mem_compress.py` 的**运行版**从 `scripts/mem_config.py` 导入容量参数并调用 DeepSeek Chat API 做语义摘要（33.5× 压缩）。本页内联代码是不依赖外部 API 和配置模块的简化版本——仅截断保留前几行，保持部署自足。**如使用内联版本替换运行版，务必同步更新容量参数（L1: MAX=50KB / KEEP=45KB）。**

L1 (recent.md) > 50KB 时，移出旧段直到 ≤45KB→L2 (summary.md)。运行版走 LLM 摘要，本 fallback 仅截断保留。

```python
#!/usr/bin/env python3
"""L1->L2: trim oldest sections from recent.md head, write to summary.md."""
import os
from datetime import datetime
HH = os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L1 = HH + "/memories/recent.md"
SUM = HH + "/memories/summary.md"
MAX_KB = 50; KEEP_KB = 45  # trigger=50KB, target=45KB

def parse(content):
    lines = content.split("\n")
    hdr = ""; secs = []; cur = []; inHdr = True
    for line in lines:
        if inHdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"; continue
            else: inHdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur: secs.append("\n".join(cur))
            cur = [line]
        else: cur.append(line)
    if cur: secs.append("\n".join(cur))
    return hdr, secs

def compress():
    if not os.path.exists(L1):
        print("  L1: not found"); return
    sz = os.path.getsize(L1) / 1024
    if sz <= MAX_KB:
        print(f"  L1: {sz:.1f}KB ≤ {MAX_KB}KB, no action needed (target ≤{KEEP_KB}KB)"); return
    content = open(L1, "r", encoding="utf-8").read()
    hdr, secs = parse(content)
    if not secs: print("  L1: no sections"); return
    target_keep = int(KEEP_KB * 1024)
    need_remove = int(sz * 1024) - target_keep
    removed = 0; keep = list(secs); taken = []
    for sec in secs:
        sec_bytes = len(sec.encode("utf-8"))
        taken.append(sec); removed += sec_bytes; keep.pop(0)
        if removed >= need_remove: break
    if not keep:
        keep = [taken[-1]]; taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print("  [safety] keeping 1 section to avoid empty recent.md")
    # Safety: never delete all sections (keep at least 1)
    if not keep:
        keep = [taken[-1]]
        taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print("  [safety] keeping 1 section to avoid empty recent.md")
    open(L1, "w", encoding="utf-8").write(hdr + "\n".join(keep))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SUM, "a", encoding="utf-8") as sf:
        sf.write(f"\n## {now} | compressed-from-L1\n\n")
        for s in taken: sf.write(s + "\n")
        sf.write("---\n")
    ns = os.path.getsize(L1) / 1024
    print(f"  L1->L2: removed {len(taken)} entries ({removed/1024:.1f}KB), remaining {ns:.1f}KB")
    print("  OK L1 compression")

if __name__ == "__main__":
    compress()
```

### memory_maintenance.py（简化版）

```python
#!/usr/bin/env python3
"""Run memory maintenance and assemble context.
Cascade: mem_consolidate.py (L2→L3) → mem_retire.py (L3→L4) → assembly rebuild.
L1→L2 compress is inline (triggered by plugin on write overflow, not here)."""
import os, sys
from pathlib import Path
from datetime import datetime

M = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "memories"
SCRIPTS = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes")) / "scripts"

def run_script(name):
    s = SCRIPTS / name
    if not s.exists():
        print(f"WARN: {s} not found"); return
    r = os.popen(f'"{sys.executable}" "{s}" 2>&1').read()
    print(f"[{name}] {r[:200].strip()}")

def read_md(filepath, heading=""):
    p = M / filepath
    if not p.exists(): return ""
    c = p.read_text(encoding="utf-8")
    return f"{heading}\\n{c}" if heading else c

def read_md_sections(filepath, limit_kb=0, section_chars=0):
    p = M / filepath
    if not p.exists(): return ""
    content = p.read_text(encoding="utf-8")
    if content.strip().startswith("# "):
        parts = content.split("\\n## ", 1)
        header = parts[0] if len(parts) > 1 else ""
        body = ("## " + parts[1]) if len(parts) > 1 else content
    else:
        header = ""
        body = content
    sections = body.split("\\n## ")
    if section_chars > 0:
        sections = [s[:section_chars] for s in sections]
    if limit_kb > 0:
        target = int(limit_kb * 1024)
        kept = []; total = 0
        for s in reversed(sections):
            if total + len(s.encode("utf-8")) > target: break
            kept.insert(0, s)
            total += len(s.encode("utf-8"))
        sections = kept
    return "\\n".join(sections)

def assemble_context():
    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f'<!-- SnowFox Memory Assembly | built: {build_ts} -->')
    parts.append("")
    s = read_md("../SOUL.md", "## self")
    if s: parts.append(s)
    s = read_md("fixed.md", "## F0")
    if s: parts.append(s)
    s = read_md("long_term.md", "## L3")
    if s: parts.append(s)
    s = read_md("user.md", "## USER")
    if s: parts.append(s)
    s = read_md_sections("summary.md", limit_kb=90, section_chars=150)
    if s: parts.append(f"## L2\\n{s}")
    s = read_md("recent.md", "## L1")
    if s: parts.append(s)
    out = M / "_assembled_context.md"
    text = "\\n\\n".join(parts)
    out.write_text(text, encoding="utf-8")
    print(f"OK: {out.name} {len(text)}B (build: {build_ts})")

if __name__ == "__main__":
    # L1→L2 compress is now inline (triggered by plugin on write overflow)
    run_script("mem_consolidate.py")
    run_script("mem_retire.py")
    assemble_context()
```

## 双站点部署 (本地 v4 + 星火 v3)

SnowFox 同时运行在本地 Windows (v4 单文件架构) 和星火阿里云轻量 (v3 目录架构) 两个站点。两地架构不同但同源——修改时需分别推两套代码。星火 SSH (port 22) 间歇性不稳定, 可用自删除 cron 重试推送。

详见 `references/deployment-dual-site.md`。

## GitHub 版本同步

本地 Hermes 组件（插件/脚本/skill）修改后，同步到 `snowfox-memory-continuity` 仓库：

```python
# 参考文件包含完整步骤和路径注意事项
skill_view(name='memory-continuity', file_path='references/repo-sync.md')
```

## 开源发布到技能市场

SnowFox 五级记忆在 Hermes 开源技能市场（2026-06 现状）是 **独一份**——`hermes skills search snowfox` 和 `hermes skills search cltrn` 均无结果。社区记忆方案只有简单的 `agent-memory` MCP 技能，无五级层次。

发布相关命令和生态洞察：

```python
# 查看市场发布指南
skill_view(name='memory-continuity', file_path='references/publishing-to-hub.md')
```

```bash
# 添加 GitHub 仓库作为技能源
hermes skills tap add github.com/TNong611/snowfox-memory-continuity

# 发布到注册表
hermes skills publish --source ~/AppData/Local/hermes/skills/note-taking/memory-continuity/
```

## ⚠️ 已知偏差（设计 vs 实现）

以下为当前实际运行状态与设计文档的偏差——加载本 skill 时必须主动检查并修正：

| 偏差 | 设计 | 实际（2026-07-03） | 修复 |
|------|------|-------------------|------|
| L1 被 compressed-from-L1 段污染 | L1 只含近期完整对话 | L1 头部残存历史 L2 摘要段（`compressed-from-L1`） | 清理 recent.md 头部 |
| L3 重复/空条目 | L3 仅含 L2 蒸馏的独特条目 | L3 含大量空、重复、同内容条目 | 已清理一次但仍需维护 |
| 插件钩子可用性 | 三钩子全注册 | 依赖 Hermes 重启后 `scripts/` 在 sys.path 中 | 重启后验证 |
| 压缩触发时机 | 写入即触发 | 写入后 `_compress_l1_if_overflow()` 正常 | 验证 |
| 用户不满信号 | —— | 用户反馈"记忆很混乱" | **此帖本身就是信号** |

**加载后必须验证：** `ls -la ~/AppData/Local/hermes/memories/recent.md` 看大小，检查 `_assembled_context.md` 中 L1 段是否有 `compressed-from-L1` 污染。
## Current Turn

刚才又掉了，分析一下原因

### Assistant

查完了，不是本地问题：

**原因：DeepSeek 服务端断流**
```
11:02:30 Stream stale 240s — no chunks, context ~50,273 tokens → kill
11:02/11:06/11:10 连续3次 RemoteProtocolError
peer closed connection... upstream=[server=openresty]
```
即：请求发出后 **240 秒一个 token 都没返回**，服务端 openresty 直接掐了连接。跟 Clash、网关都没关系，是你本地一个 **cron 任务（约 50K tokens 长上下文）** 和之前对话触发的——上下文越长 DeepSeek 生成越慢，越容易撞上 240s 超时。

**修复步骤：**
1. 重发消息即可（短上下文一般能过）
2. 长任务切 `deepseek-v4-pro` 或拆分（`/model` 切换）
3. 那个超时 cron 任务建议删掉或改短 prompt：
```
cronjob list  → 找到 098f92a779fe → 改 prompt 或 remove
```

要我现在把那个 cron 处理掉吗？

## Current Turn

处理掉

### Assistant

已删除 ✅ `098f92a779fe` 任务日志压缩到F0（每天0点那个）。

注意：这会导致 tasklog 不再自动压缩到 F0、workspace 前一天目录不再自动清理。需要的话随时说一声，我重建一个（或改成短 prompt 的版本）。

---
_雪狐记录 | session=20260813_110050_b8e159
## 2026-08-14 13:32:18 | session=20260813_110050_b8e159 | pending

### User

重建一个

### Assistant

_等待回复..._

---
_雪狐记录 | session=20260813_110050_b8e159 | pending_
## 2026-08-15 10:46:02 | session=20260815_104558_33cc91 | pending

### User

git clone https://github.com/deepseek-ai/deepseek-harness 下载harness,并同步工具链与记忆组件，同步记忆文件到harness,D:\AI\snowfox将记忆组件与记忆文件放一起便于维护与移植放在D\AI文件夹下，能明白吗

### Assistant

_等待回复..._

---
_雪狐记录 | session=20260815_104558_33cc91 | pending_
