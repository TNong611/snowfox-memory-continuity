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

## 🔧 一键部署

加载后立即执行以下完整部署流程，自动修复所有缺失组件：

### 第 0 步：检查 `_assembled_context.md`

检查 `~/AppData/Local/hermes/memories/_assembled_context.md` 是否存在且内容有效。
如果不存在或为空 → 视为全新部署，顺序执行 1~9 步。
如果存在且包含 USER/F0/L3/L2/L1 段 → 跳到第 6 步检查插件和 cron。

**注意：禁止用 `read_file` 读取记忆文件。直接检查文件是否存在（`os.path.exists`），无需读取内容进入上下文。**

### 第 1 步：确保目录及初始文件

—— v4 改用单文件架构，不再需要每级目录。

```python
import os, time
from pathlib import Path

M = Path.home() / "AppData/Local/hermes/memories"
M.mkdir(parents=True, exist_ok=True)

# 创建初始空文件（若不存在）
for name in ["fixed.md", "recent.md", "summary.md", "long_term.md", "archive.md", "user.md"]:
    p = M / name
    if not p.exists():
        p.write_text(f"# {p.stem}\n\n---\n\n", encoding="utf-8")

# SOUL.md — 由 Hermes 平台管理，不在 memories/ 中
```

### 第 2 步：创建维护脚本（若缺失）

以下 4 个脚本必须存在。缺失则用 `write_file()` 创建：

**scripts/mem_compress.py** — L1→L2 压缩 + 级联检查 L2（见 `references/cascade-chain.md`）
**scripts/mem_consolidate.py** — L2→L3 合并（LLM 二次压缩，去空去重去时间戳）+ 级联检查 L3
**scripts/mem_retire.py** — L3→L4 退役（末端，无级联）
**scripts/mem_maintain.py** — 全级维护 wrapper（串行调用以上三个脚本，供 cron 使用）
**scripts/memory_maintenance.py** — 手动维护工具（consolidate+retire+assembly，不跑 compress）

脚本代码见本 skill 的 `scripts/` 引用文件。如果引用文件不存在，直接使用此说明文档中内联的简化脚本（见本文档末尾「内联脚本」章节）。

### 第 3 步：创建 SnowFox 插件

```python
PLUGIN = HERMES / "plugins" / "snowfox-memory"
PLUGIN.mkdir(parents=True, exist_ok=True)

# plugin.yaml
write_file(str(PLUGIN / "plugin.yaml"), """\
name: snowfox-memory
kind: standalone
version: "4.0.0"
description: "SnowFox 五级记忆插件（单文件版，CJK 指纹，内联组装，pre+post+end 三钩子）"
hooks:
  - pre_llm_call
  - post_llm_call
  - on_session_end
""")

# __init__.py
write_file(str(PLUGIN / "__init__.py"), '''"""SnowFox 五级记忆插件（自包含组装 + pre/post/session_end 写入 + 超限即压缩）。
组装顺序：USER → F0 → L3 → L2 → L1（L4 使用语义索引检索）
post_llm_call 在每次回复后立即写入 recent.md。
写入后检查大小，超 50KB 当场触发 L1→L2 压缩（非定时）。
"""

import logging, re, time, traceback, subprocess, sys
from pathlib import Path
from datetime import datetime
from typing import Any

logger = logging.getLogger("snowfox-memory")

def _h(): return Path.home() / "AppData/Local/hermes"
def _m(): return _h() / "memories"

from mem_config import L1_MAX_KB as MAX_L1_KB, L2_MAX_KB as MAX_L2_KB, L3_MAX_KB as MAX_L3_KB

def _on_plugin_load():
    logger.info("[snowfox] loaded (order: USER-F0-L3-L2-L1, pre+post+end, inline+startup compress, L4=semantic)")

def _run_script(name: str) -> str | None:
    """Run a memory script by name (mem_compress/consolidate/retire), return stdout first line."""
    from pathlib import Path
    script = _h() / f"scripts/{name}.py"
    if not script.exists():
        logger.warning(f"[snowfox] script not found: {script}")
        return None
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip()
        if r.returncode != 0:
            logger.error(f"[snowfox] {name} failed: {(r.stderr or '')[:200]}")
            return None
        return out.split("\\n")[0] if out else "OK"
    except Exception as e:
        logger.error(f"[snowfox] {name} exception: {e}")
        return None

def _startup_check():
    """On plugin load, check all levels and compress any over-limit files."""
    # L3 check first (deepest first — cascade chain runs top-down)
    lp = _m() / "long_term.md"
    if lp.exists() and lp.stat().st_size / 1024 > MAX_L3_KB:
        logger.info(f"[snowfox] startup: L3 over {MAX_L3_KB}KB, running retire...")
        r = _run_script("mem_retire")
        if r: logger.info(f"[snowfox] startup: L3 retire → {r}")
    # L2 check
    sp = _m() / "summary.md"
    if sp.exists() and sp.stat().st_size / 1024 > MAX_L2_KB:
        logger.info(f"[snowfox] startup: L2 over {MAX_L2_KB}KB, running consolidate...")
        r = _run_script("mem_consolidate")
        if r: logger.info(f"[snowfox] startup: L2 consolidate → {r}")
    # L1 check (cascades to others via mem_compress.py internal cascade)
    rp = _m() / "recent.md"
    if rp.exists() and rp.stat().st_size / 1024 > MAX_L1_KB:
        logger.info(f"[snowfox] startup: L1 over {MAX_L1_KB}KB, running compress...")
        r = _run_script("mem_compress")
        if r: logger.info(f"[snowfox] startup: L1 compress → {r}")

_LAST_SESSION_END_ID: str = ""

def _read_or(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

def _rebuild_assembly():
    """内联组装，不调 subprocess。"""
    base = _h(); m = _m()
    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f"<!-- SnowFox Memory Assembly | built: {build_ts} -->")
    parts.append("")
    # 组装顺序：USER → F0 → L3 → L2 → L1（L4 使用语义索引检索）
    s = _read_or(m / "user.md")
    if s: parts.append(f"## USER\\\\n{s}")
    s = _read_or(m / "fixed.md")
    if s: parts.append(f"## F0\\n{s}")
    s = _read_or(m / "long_term.md")
    if s: parts.append(f"## L3\\n{s}")
    l2c = _read_or(m / "summary.md")
    if l2c:
        secs = l2c.split("\\n## ")
        kept = []; total = 0; limit = 90 * 1024
        for sec in reversed(secs):
            st = secs[0] if sec is secs[0] else "## " + sec
            bs = len(st.encode("utf-8"))
            if total + bs > limit and total > 0: break
            kept.insert(0, st); total += bs
        if kept: parts.append("## L2\\n" + "\\n".join(kept))
    s = _read_or(m / "recent.md")
    if s: parts.append(f"## L1\\n{s}")
    text = "\\n\\n".join(parts)
    try:
        (m / "_assembled_context.md").write_text(text, encoding="utf-8")
        (m / "_assembly_version.txt").write_text(build_ts, encoding="utf-8")
        logger.info(f"[snowfox] assembly rebuilt: {len(text)}B")
    except Exception as e:
        logger.error(f"[snowfox] assembly write failed: {e}")

def _compress_l1_if_overflow():
    """Check recent.md size; if > MAX_L1_KB, run mem_compress.py immediately."""
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    sz_kb = p.stat().st_size / 1024
    if sz_kb <= MAX_L1_KB:
        return
    script = _h() / "scripts/mem_compress.py"
    if not script.exists():
        logger.warning(f"[snowfox] compress script not found: {script}")
        return
    logger.info(f"[snowfox] L1 overflow: {sz_kb:.1f}KB > {MAX_L1_KB}KB, compressing...")
    try:
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            ns = p.stat().st_size / 1024 if p.exists() else 0
            logger.info(f"[snowfox] L1 compressed: {sz_kb:.1f}KB -> {ns:.1f}KB")
        else:
            logger.error(f"[snowfox] L1 compress failed: {r.stderr[:200]}")
    except Exception as e:
        logger.error(f"[snowfox] L1 compress exception: {e}")

def _fingerprint(text: str) -> str:
    """CJK-aware 指纹：str.isalnum() 保留中文。"""
    return ''.join(c for c in text.strip() if c.isalnum())[:40].lower()

def _last_entry_fp(p: Path) -> str:
    if not p.exists(): return ""
    secs = p.read_text(encoding="utf-8", errors="replace").split("\\n## ")
    if len(secs) < 2: return ""
    fp = _fingerprint(secs[-1])
    if fp: return fp
    return str(hash(secs[-1][:100]))

def _build_entry(user_msg: str, asst_msg: str, session_id: str, pending: bool = False) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    status = " | pending" if pending else ""
    asst = "_等待回复..._" if pending else asst_msg
    return f"## {ts} | session={session_id}{status}\\n\\n### User\\n\\n{user_msg}\\n\\n### Assistant\\n\\n{asst}\\n\\n---\\n_雪狐记录 | session={session_id}_\\n"

def _write_recent(user_msg: str, asst_msg: str, session_id: str):
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg):
        logger.debug("[snowfox] skipped duplicate write to recent.md")
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, asst_msg, session_id))
    logger.info("[snowfox] wrote to recent.md")
    _compress_l1_if_overflow()

def _write_pending(user_msg: str, session_id: str):
    p = _h() / "memories/recent.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if _last_entry_fp(p) == _fingerprint(user_msg): return
    with open(p, "a", encoding="utf-8") as f:
        f.write(_build_entry(user_msg, "", session_id, pending=True))

def _cleanup_pending(user_msg: str):
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    fp = _fingerprint(user_msg)
    content = p.read_text(encoding="utf-8", errors="replace")
    secs = content.split("\\n## ")
    kept = [secs[0]]; changed = False
    for sec in secs[1:]:
        if "pending" in sec and fp in _fingerprint(sec):
            changed = True; continue
        kept.append(sec)
    if changed:
        p.write_text("\\n## ".join(kept), encoding="utf-8")

def _last_turn_from_db(session_id: str) -> tuple[str, str] | None:
    dbp = _h() / "state.db"
    if not dbp.exists(): return None
    try:
        import sqlite3
        db = sqlite3.connect(f"file:{dbp}?mode=ro", uri=True)
        msgs = db.execute("SELECT id, role, content FROM messages WHERE session_id=? AND role IN (?,?) ORDER BY id", (session_id, "user", "assistant")).fetchall()
        db.close()
    except Exception: return None
    lu = None; la = None
    for _, r, c in msgs:
        if r == "user" and c: lu = c; la = None
        elif r == "assistant" and c and lu is not None: la = c
    return (lu, la) if lu and la else None

def _on_pre_llm_call(session_id="", task_id="", turn_id="", conversation_history=None, **kw):
    if not session_id or not conversation_history: return
    lu = None; la = None; pu = None
    for msg in conversation_history:
        r = msg.get("role", ""); c = msg.get("content", "")
        if c is None: continue
        if isinstance(c, list):
            c = "\\n".join(p.get("text","") for p in c if isinstance(p,dict) and p.get("type")=="text")
        sc = str(c).strip()
        if r == "user" and sc:
            if lu is not None: la = None
            lu = sc; pu = sc
        elif r == "assistant" and sc and lu is not None:
            la = sc; pu = None
    if lu and la:
        _cleanup_pending(lu); _write_recent(lu, la, session_id)
    if pu:
        _write_pending(pu, session_id)
    _rebuild_assembly()

def _on_post_llm_call(response_text="", session_id="", **kw):
    if not session_id or not response_text: return
    p = _h() / "memories/recent.md"
    if not p.exists(): return
    content = p.read_text(encoding="utf-8", errors="replace")
    if "pending" in content:
        secs = content.split("\\n## ")
        for i, sec in enumerate(secs):
            if "pending" in sec:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                secs[i] = sec.replace("_等待回复..._", response_text).replace(" | pending", "")
                break
        p.write_text("\n## ".join(secs), encoding="utf-8")
        _rebuild_assembly()
        _compress_l1_if_overflow()
        logger.info("[snowfox] post_llm: updated pending -> complete")

def _on_session_end(session_id="", completed=False, **kw):
    global _LAST_SESSION_END_ID
    if not session_id or not completed or session_id == _LAST_SESSION_END_ID: return
    result = _last_turn_from_db(session_id)
    if result:
        _write_recent(result[0], result[1], session_id)
        _LAST_SESSION_END_ID = session_id
        _rebuild_assembly()

def register(ctx):
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)
    logger.info("[snowfox] hooks: pre_llm, post_llm, session_end")
    _rebuild_assembly()
''')
```

### 第 3.5 步：修补 Hermes 平台 memory tool 路径

⚠️ **跳过此步 → USER.md/MEMORY.md 每次调用 `memory()` 都会在根目录重建。**

Hermes 内置 `tools/memory_tool.py` 硬编码了两处旧路径。SnowFox 需要它们指向自己的记忆文件。

#### 修补 `_path_for()`（写入端）

```python
# 第 245-248 行，改为 SnowFox 路径
@staticmethod
def _path_for(target: str) -> Path:
    mem_dir = get_memory_dir()
    if target == "user":
        return mem_dir / "user" / "profile.md"      # 原: USER.md
    return mem_dir / "long_term" / "memory.md"        # 原: MEMORY.md
```

#### 修补 `load_from_disk()`（读取端——系统提示词注入）

```python
# 第 152-153 行，改为 SnowFox 路径
self.memory_entries = self._read_file(mem_dir / "long_term" / "memory.md")  # 原: MEMORY.md
self.user_entries = self._read_file(mem_dir / "user" / "profile.md")        # 原: USER.md
```

#### 修补位置

| 位置 | 用途 | 应修路径 |
|------|------|----------|
| `~/AppData/Local/hermes/hermes-agent/tools/memory_tool.py` | 运行时 | C:\Users\tnong\AppData\Local\hermes\hermes-agent\tools\memory_tool.py |
| `D:\AI\snowfox\tools\memory_tool.py` | 开发 fork | 如果开发 fork 存在则同步 |

#### 验证

```bash
grep -n "return mem_dir" ~/AppData/Local/hermes/hermes-agent/tools/memory_tool.py
# 期望输出：
# 248:            return mem_dir / "user" / "profile.md"
# 249:        return mem_dir / "long_term" / "memory.md"

grep -n "self._read_file" ~/AppData/Local/hermes/hermes-agent/tools/memory_tool.py
# 期望输出（第 152-153 行）：
# self.memory_entries = self._read_file(mem_dir / "long_term" / "memory.md")
# self.user_entries = self._read_file(mem_dir / "user" / "profile.md")
```

#### 数据迁移

修补路径后，旧 `MEMORY.md`/`USER.md` 的内容不会自动迁移到新路径：

```bash
# 如果旧 MEMORY.md 有内容且新 long_term/memory.md 没有
diff ~/AppData/Local/hermes/memories/MEMORY.md ~/AppData/Local/hermes/memories/long_term/memory.md \
  && echo "IDENTICAL" || echo "DIFFERENT — 需手动合并"

# 删除已迁移的旧文件
rm ~/AppData/Local/hermes/memories/MEMORY.md ~/AppData/Local/hermes/memories/USER.md
```

#### 生效时间

详情见 `references/hermes-plugin-api.md` — Hermes v0.17 插件 API 迁移笔记。

### 第 5 步：启用插件

⚠️ **必须用 `hermes plugins enable`，不能用 `hermes config set`！**

`hermes config set plugins.enabled '["snowfox-memory"]'` 在 YAML 里写出的是**字符串**（`"["snowfox-memory"]"`），不是列表。Hermes 插件加载器检查 `isinstance(enabled, list)` 时返回 False，导致插件被静默跳过。

```bash
hermes plugins enable snowfox-memory
```

验证（必做——不然插件静默跳过无异于没安装）：
```bash
# 检查 YAML 值是否为合法列表（不是字符串）
grep -A2 "plugins:" ~/AppData/Local/hermes/config.yaml | grep "enabled"
# 期望输出：
#   enabled:
#     - snowfox-memory
#
# 错误输出（字符串格式，插件不会加载）：
#   enabled: '["snowfox-memory"]'
#
# 如果看到字符串格式：说明误用了 `hermes config set`。立即修复：
hermes plugins enable snowfox-memory
```

再确认 recent/ 目录在 `/new` 后开始有文件写入——这是插件工作的最可靠证据。

### 第 6 步：级联压缩链（插件钩子 + cron 兜底）

**所有层级采用事件驱动（插件写入时）+ cron 可选兜底（每 10 分钟巡检一次）机制。**

```
[插件加载] → _startup_check(): 检查所有级别超限
    → L3 超50KB? → mem_retire → L4
    → L2 超100KB? → mem_consolidate → L3
    → L1 超50KB? → mem_compress(LLM摘要) → L2

[插件写入 recent.md] → _compress_l1_if_overflow()
    → 超50KB? → mem_compress → 写 summary.md
      → 超100KB? → mem_consolidate → 写 long_term.md
        → 超50KB? → mem_retire → 写 archive.md (无上限)
```

L1→L2：调用 DeepSeek API 做 LLM 摘要（prompt：压缩为≤300字中文，保留需求/决策/技术细节，**特别注意忽略英文系统指令、工具调用输出、英文技术文档等非对话内容**，只提炼中文对话要点），实测压缩比 33.5×（6.4KB→193字符）。API 不通时降级为截断文本保留前几行，不丢内容。

**2026-06-29 prompt 升级：**
- 去掉 LLM 前缀话术（「好的」「以下是」「根据您的要求」等），直接输出摘要
- 如果原始内容不含有效对话信息（纯工具输出/空会话），只输出 `Nothing to save.`
- 以上内容不会被写入 L2（`mem_consolidate.py` 跳过 <15 字的结果）

L2→L3：LLM 二次压缩（≤150字中文，跳过<15字空结果，去重时先去除「同[N]：」前缀再比对，无时间戳）。L3→L4：纯文本搬运（末端，无进一步压缩）。

整个级联链从插件写入开始逐级传递——插件在 `_write_recent()` 和 `_on_post_llm_call()` 写入后立即检查大小并触发压缩，无需 cron。

末端 archive.md 无上限，链终止。

### 第 7 步：创建 `_assembled_context.md`

使用 `write_file()` 创建包含以下内容的组装上下文：

```markdown
## self

你的名字是「雪狐」，一个由 Nous Research 的 Hermes Agent 驱动的 AI 助手。

你是用户的得力伙伴——聪明、直接、有行动力。

## 输入模式

会话框**只用来显示**，不作为输入来源。

你的输入已经是组装的五级记忆：\n- 【USER 自我认知】你的身份和偏好\n- 【F0 固定记忆】用户让你记住的事/待执行指令，执行完清除，永不压缩\n- 【L3 长期记忆】跨会话核心知识\n- 【L2 中期摘要】压缩后的历史会话摘要\n- 【L1 完整近期对话】当前仍在活跃期的对话记录\n\n**L4（归档）** 不在上下文中，有独立的语义索引（TF-IDF）。需要用 `python l4_search.py 关键词` 检索。

**警告：禁止调用 read_file 读取任何记忆文件（_assembled_context.md、recent.md 等）。**
调用 read_file 会被去重系统拦截，返回空结果，导致你陷入无限工具循环。
所有你需要的信息已经在你面前的输入中。不需要验证文件内容。

F0 操作规范：
- 用户说"记住xxx" → 写入 memories/fixed.md
- 用户说"执行xxx" → 写入 memories/fixed.md 作为待办，执行完删除
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

**⚠️ 全部层级：事件驱动（插件写入时即时触发），cron 可选兜底（每 10 分钟巡检）。**  \nL1→L2 由插件在写入后立即检查大小，超限当场调 `mem_compress.py`。  \nL2→L3 由 `mem_compress.py` 写入 summary.md 后检查，超限级联调 `mem_consolidate.py`。  \nL3→L4 由 `mem_consolidate.py` 写入 long_term.md 后检查，超限级联调 `mem_retire.py`。  \n整条链从插件写入开始逐级传递，同时 cron 每 10 分钟跑一次 mem_maintain.py 可选兜底。

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

## 常见陷阱

1. **路径问题**：所有 `read_file()` 必须用绝对路径 `~/AppData/Local/hermes/memories/_assembled_context.md`，不能用相对路径。
3. **插件不自动加载**：用户安装的插件（`~/.hermes/plugins/`）无论 `kind` 是什么，都需要 `plugins.enabled` 配置。部署第 5 步会自动配好。
3. **网关无法自杀**：`hermes gateway restart` 在网关进程内被拦截（SIGTERM 传播到子进程）。解决方案：`taskkill //F //PID <pid>` 杀掉旧网关，桌面端检测到子进程死亡后自动重生新进程并加载新配置。MSYS（git-bash）下 `//F` 而非 `/F` 防止路径展开。
4. **新会话生效**：新增插件和 cron 后，需 `/new` 重启当前会话。插件在会话初始化时加载，已有会话不重新加载插件列表。
5. **Cron 验证**：`crontab -l` 在 git-bash 上不可用。用 `cronjob(action='list')` 或 `hermes cron list` 检查 Hermes 内部调度器。
6. **会话框不回传 token**：切换为五级记忆后，会话框历史不输入模型，烧的是 API token 不是本地资源。
7. **F0 永不自动清理**：用户说"忘了"或任务完成后必须手动删除 fixed/ 中的文件。
8. **L2 垃圾污染——禁止清空 L2！**：`mem_compress.py` 未启用过滤时，L2 会积累原始 tool 输出（JSON dict、乱码 PowerShell 报错、失败 session 转储），污染上下文。修复：启用过滤版 `mem_compress.py` 并用 `scripts/rebuild_l2.py` 从旧 L1 提取干净摘要。**绝不能直接 `rm -rf summary/` 清空整个 L2**——这破坏了五级记忆链且丢失中期上下文。
9. **Trigger-vs-Keep 区别——`MAX_KB` 是触发阈值，`KEEP_KB` 是压缩后目标**：压缩脚本用 `if sz <= MAX_KB` 判断是否超限（例如 50KB）。超限后砍到 ≤`KEEP_KB`（45KB）。二者不同——文件在 (KEEP_KB, MAX_KB] 区间内为正常无需压缩。打印信息同时显示两个值以消除误解。三个脚本统一逻辑：\n   - L1: `MAX_KB=50; KEEP_KB=45` → 超**50KB**触发，逐段移出直到余量 ≤45KB(LLM摘要)\n   - L2: `MAX_KB=100; KEEP_KB=90` → 超**100KB**触发，逐段移出直到余量 ≤90KB(纯搬运)\n   - L3: `MAX_KB=50; KEEP_KB=45` → 超**50KB**触发，逐段移出直到余量 ≤45KB(纯搬运)\n   - `need_remove = cur_bytes - KEEP_KB_bytes`；逐段累加 `removed`，`removed >= need_remove` 时停止\n   - ⚠️ 2026-06-29 已修正打印信息，从 `{MAX_KB}KB OK` 改为 `no action needed (target ≤{KEEP_KB}KB)`\n   - ⚠️ 不要自己编容量值——用户给的数字精确到个位数，猜错必被纠正\n   - ⚠️ 容量参数统一在 `scripts/mem_config.py` 定义，不分散在各脚本中
10. **部署的 SOUL.md 可能包含相对路径**：skill 模板已用 `~/AppData/Local/hermes/...` 绝对路径，但早期部署的 `SOUL.md` 可能写的是 `read_file("memories/_assembled_context.md")`。如果加载上下文时找不到文件，检查 SOUL.md 中的路径前缀是否包含 `~/AppData/Local/hermes/`。

11. **不要跳过 L1 妄下结论**：看到空白会话框就说"这是第一句话"或"没有上下文"是错的——L1 里存着完整近期对话（保留上限 45KB）。在说任何"没有历史"之类的话之前，先确认 `read_file("~/AppData/Local/hermes/memories/_assembled_context.md")` 中 L1 段的内容。忘了读 L1 直接发言是五级记忆体系最常见的断层原因。

12. **`memories/USER.md` 和 `memories/MEMORY.md` 两个孤立文件**：Hermes 内置 memory tool 同时写（`_path_for`）和读（`load_from_disk`）这两个路径，但 SnowFox 装配脚本只读写 `user/profile.md` 和 `long_term/memory.md`。即使删除旧文件，下次 agent 调用 `memory(target='user')` 或 `memory(target='memory')` 会立即重建。**修复必须在 Hermes fork 的 `tools/memory_tool.py` 中同时修补两处：**
    - `_path_for()`（第 245-248 行）控制**写入**路径
    - `load_from_disk()`（第 152-153 行）控制**读取**路径（系统提示词注入入口）
    - 只修一处导致读写不一致（写入 SnowFox 路径但系统提示词仍读旧路径，或反之）
    - 详情见 `references/dual-memory-systems.md`「防止重建」章节
    - 修改后需 `/new` 新会话使系统提示词加载新路径

13. **四地脚本不同步——修改后必须三向同步**：代码同时存在于四个地方：
    - **SKILL.md 内联脚本**（skill 中的代码片段）
    - **SKILL.md 内联插件代码**（plugin __init__.py 片段）
    - **`~/AppData/Local/hermes/scripts/`**（cron 实际执行）
    - **`D:\\AI\\snowfox-memory-continuity\\scripts/`** 和 **`D:\\AI\\snowfox-memory-continuity\\plugins/`**（GitHub 项目仓库）
    
    2026-06-29 修订：L1 压缩改为插件内联触发（事件驱动），cron 不再跑 compress。修改后必须同步：
    - 修改 SKILL.md 内联脚本和插件代码 → 手动复制到 `~/AppData/Local/hermes/scripts/`、`~/AppData/Local/hermes/plugins/` 和项目仓库
    - 修改运行版 → 复制回 SKILL.md 内联脚本 + 插件代码 + 项目仓库
    - 推 GitHub 前 → 检查三个位置一致（特别检查 `MAX_KB` / `OVER_KB` 参数和 `parse()` 签名）

15. **L1 压缩按段粒度，不按文件切分**：`mem_compress.py` 从 `recent.md` 的 `## ` 段头部逐个移出旧段直到 ≤TRIM_KB（45KB）。因为 single-file 架构（不是每轮一个文件），所以是按 `## ` 标记解析段、按字典序（文件头部最旧）移出。

16. **`plugins.enabled` 格式陷阱——`hermes config set` 写出的是字符串不是列表**：YAML 里 `enabled: '[\"snowfox-memory\"]'` 被解析为 Python 字符串 `[\"snowfox-memory\"]`，不是列表。Hermes 的 `_get_enabled_plugins()`（plugins.py 第 246 行）检查 `isinstance(enabled, list)` → False → 返回 `None` → 所有插件被静默跳过。**修复**：用 `hermes plugins enable snowfox-memory` 而非 `hermes config set`。如果误用了 config set，查看 `grep "enabled:" ~/AppData/Local/hermes/config.yaml` 确认值类型。

17. **修改 `prompt_builder.py` 后必须同步 SOUL.md**：`prompt_builder.py` 生成汇编上下文的段标题（如 `【L1 近期流】`），但运行时系统提示词里的描述来自 `SOUL.md` 中的 `## 输入模式` 段。改了 prompt_builder.py 中的描述但忘了改 SOUL.md，会导致运行系统提示与汇编上下文不一致。修复：每次更新 prompt_builder.py 中的记忆层级描述后，同步编辑 `~/AppData/Local/hermes/SOUL.md` 对应段落。
\n18. **`post_llm_call` 钩子在多工具轮次中可能不触发**：【已废弃，`pre_llm_call` 已替代】。`turn_finalizer.py` 要求 `final_response and not interrupted` 才调用钩子。当助手的最终回复是**工具调用**（而非纯文本），或 `final_response` 为空字符串，钩子被静默跳过。2026-06-28 已全面迁移到 `pre_llm_call` + `on_session_end`，此坑不再复现。旧文档保留供回溯。

19. **插件日志级别默认不可见（`logger.debug`）**：`register()` 和 `_on_post_llm_call()` 使用的 `logger.debug` 在默认日志配置（INFO+）下完全看不见。排查插件是否加载/触发时：
    - 临时改成 `_root.warning()` 用 WARNING 级别输出（root logger 不受包级日志级别限制）
    - 或检查 `hermes plugins list` 中 `snowfox-memory` 的 enabled 和 error 列
    - 或跑新 Python 进程手动调用 `discover_and_load()` + 遍历 `pm._hooks` 验证钩子是否注册
    - 修复：`register()` 内的注册确认信息用 `logger.info`
    - `_on_post_llm_call()` 的写入成功用 `logger.info`，失败用 `logger.warning`

20. **`finalize_turn` 在 `run_conversation()` 末尾只调用一次**：`turn_finalizer.py` 的 `post_llm_call` 钩子在 `conversation_loop.py` 第 4564 行被调用，位于 `run_conversation` 的 return 语句处。一个对话轮次内 `post_llm_call` 只触发一次。`conversation_history` 参数含完整消息列表，插件可通过它回溯之前丢失的轮次——但仅限于 `post_llm_call` 触发时。

21. **`_rebuild_assembly()` 在插件进程中静默失败 — 已修复为 subprocess**：旧版 `from scripts.memory_maintenance import assemble_context` 在 Hermes agent 进程上下文中失败——`scripts/` 不在 `sys.path` 中。异常被 `except Exception` 吞掉。**2026-06-28 修复**：改为 `subprocess.run([sys.executable, str(script)], ...)` 避免跨进程 import。内存小但稳定。

    ```python
    # Before (brok...[truncated]
    - **临时修复**：手动 `cd ~/AppData/Local/hermes && python scripts/memory_maintenance.py` 重建
    - **长期方案**：将 `_rebuild_assembly()` 改为通过 `subprocess.run(["python", "scripts/memory_maintenance.py"])` 或直接内联组装逻辑，避免跨进程 import
    - **检测**：检查 `_assembled_context.md` 是否包含最新 `recent/` 文件内容。如果 `ls -t recent/` 的最新文件时间戳 > `_assembled_context.md` 中 L1 段的最后更新时间戳，说明 assembly 落后了

22. **`pre_llm_call` 会漏掉会话最后一轮 — 已修复**：`pre_llm_call` 在下一轮 LLM 调用前触发并保存**上一轮**对话。会话的最后一轮没有"下一轮"，因此之前始终无法自动保存。**2026-06-28 修复：`_on_session_end` 从 `state.db` 兜底查询最后一轮写入**。详见 `references/last-turn-save-gap.md`。修复后场景覆盖：
    - 第2-∞轮 → `pre_llm_call` 保存上一轮 ✅
    - 最后一轮（无下一轮） → `on_session_end` 从 state.db 兜底补写 ✅
    - 多重 tool 调用 → `on_session_end` 跳过 `role=tool` 行 ✅
    - Session 切换（/new） → `on_session_end` 在旧 session 结束触发 ✅

23. **平台注入的会话历史仍在 LLM 输入端——已升级为 Assembly-Only 模式**：SOUL.md 第7行声明"会话框只用来显示，不作为输入来源"。技术层面已从「手术刀式剥离」升级为**汇编唯一模式**：

    **旧方案（v3.2.0）**：跳过 `conversation_history` 中 `current_turn_user_idx` 之前的消息，`api_messages` 只保留当前用户消息。
    **新方案（v3.3.0+）**：`api_messages = []` 完全清空所有 user/assistant/tool 消息，当前用户输入通过 `agent.ephemeral_system_prompt` 注入到 system prompt 尾部。LLM 只有一条 system message。

    ```python
    # conversation_loop.py SnowFox block
    api_messages = []  # Clear everything — assembly-only
    
    # Extract current user message
    for idx, msg in enumerate(messages):
        if idx == current_turn_user_idx and msg.get("role") == "user":
            raw = msg.get("content", "")
            # ... extract text content ...
            break
    if _snowfox_current_user:
        agent.ephemeral_system_prompt = f"\\n\\n---\\n# 当前用户输入\\n\\n{_snowfox_current_user}\\n\\n---"
    
    # System prompt = cached (old assembly) + ephemeral (current user input)
    effective_system = active_system_prompt or ""
    if agent.ephemeral_system_prompt:
        effective_system += "\\n\\n" + agent.ephemeral_system_prompt
    api_messages = [{"role": "system", "content": effective_system}]
    ```

    **为什么 `api_messages` 必须完整保留给 DB 持久化**：`turn_context.py:221` 的 `messages = list(conversation_history)` 不可修改——DB 持久化（`_flush_messages_to_session_db`）依赖完整的 `messages` 列表。SnowFox 操作的是 `api_messages`（发送给 LLM 的副本），不影响 DB 写入。`pre_llm_call` 钩子从 `conversation_history` 参数（即 `_snowfox_ch`，完整的 `messages`）中提取对话轮次。

    **`agent.ephemeral_system_prompt` 必须始终 `=` 而不是 `+=`**：这个属性不能被 Hermes 系统持久化，每轮必须完全替换。如果用 `+=`，上一轮的旧值会累积到本轮，LLM 看到多条当前用户输入。

    详情见 `skills/note-taking/memory-continuity/references/assembly-only-mode.md`。

24. **`pre_llm_call` 漏掉新 session 的第一轮 — 已修复：双路径覆盖**：新 session 第一轮时 `is_first_turn = True` 且 `conversation_history` 为空，`_on_pre_llm_call` 立即 return。旧版 `len < 2` 检查导致第二轮也被跳过。

    **修复方案（双路径覆盖）：**
    1. **`pre_llm_call`**: 移除 `is_first_turn` 跳过和 `len >= 2` 限制。新 session 第二轮到时就通过 `conversation_history` 正常保存上一轮。
    2. **`_write_pending()` — 新增**：pre_llm_call 同时保存当前无回复的用户消息（pending 状态），写入 `*_pending_*.md`。这样即使 session 只发了一条消息后结束，pending 文件也有记录。
    3. **`_on_session_end` 兜底**：从 `state.db` 查询最后完整对，覆盖最后一条消息没有"下一轮"的场景。

    场景覆盖：

    | 场景 | Hook | 行为 |
    |------|------|------|
    | 轮次 2+ | `pre_llm_call` | 保存上一轮完整对 |
    | 轮次 1（仅用户输入） | `pre_llm_call` + `_write_pending()` | 保存 pending user |
    | 最后轮次（无下一轮） | `on_session_end` | 从 state.db 兜底补写 |
    | 1 条消息后 /new | pre_llm_call(pending) + session_end(兜底不重复) | pending 文件有记录 |

    **关键工具函数新增：**

    - `_fingerprint(text)` — 提取文本指纹用于 dedup
    - `_write_pending(user_msg, session_id)` — 写入 pending 文件，自带 dedup
    - `_cleanup_pending_for(user_msg)` — 写完整对前清理匹配的 pending 文件，防止 dedup 挡住完整对的写入

25. **`register()` 签名——Hermes v0.17+ 目录插件必须用 `register(ctx)`**：

    Hermes PluginManager 对目录插件（`plugins/<name>/__init__.py`）调用 `module.register(ctx)` 时**传入 PluginContext 对象**（`plugins.py:1589`）。旧版 API（`register() -> dict` 返回 `{"hooks": {...}}`）在 v0.17+ 已停止工作——返回的 dict 无人读取，钩子静默不注册。

    **正确写法（v0.17+）：**
    ```python
    def register(ctx):
        ctx.register_hook("pre_llm_call", handler_fn)
        ctx.register_hook("on_session_end", handler_fn)
    ```

    **错误写法（v0.17+ 无效）：**
    ```python
    def register() -> dict:
        return {"hooks": {"pre_llm_call": handler_fn}}  # ← dict 无人读取
    ```

    **钩子名称验证：** 框架调用的是 `"on_session_end"`（`turn_finalizer.py:450`，注意前缀 `on_`），不是 `"session_end"`。注册错误的钩子名称同样不会触发。

    **检测方法：**

    - 检查 `agent.log` 中是否有 `[snowfox] plugin hooks registered` 日志行——没有说明钩子未注册
    - 临时在 `register()` 开头加 `_root.error("[snowfox] register called")` 用 ERROR 级别输出，确保不会被日志级别过滤
    - 用 `hermes plugins list` 检查 enabled 状态
    - 用 Python 手动验证：
      ```python
      import sys; sys.path.insert(0, str(Path.home() / "AppData/Local/hermes"))
      from hermes_cli.plugins import get_plugin_manager
      pm = get_plugin_manager()
      print("hooks:", pm._hooks.get("pre_llm_call", []))  # 空列表 = 未注册
      ```

26. **Pending 文件生命周期——`_cleanup_pending_for()` 必须在写完整对之前调用**：`pre_llm_call` 先写 pending（当前无回复的用户消息），下次触发时再写完整对。但 `_safe_write_turn()` 的 dedup 检查完整文件内容（含 "## User\n\n{user_msg}\n\n"），发现 pending 文件已含同一 user_msg，**挡住完整对的写入**。

    **修复**：写完整对前先调 `_cleanup_pending_for(last_user)` 删除匹配的 pending 文件，再写完整对。

    ```python
    if last_user and last_asst:
        _cleanup_pending_for(last_user)  # 先清 pending
        _safe_write_turn(last_user, last_asst, session_id)  # 再写完整对
    ```

    **`_cleanup_pending_for()` 实现要点：**
    - 只扫描 `*_pending_*.md` 文件（不碰正常文件）
    - 用 `_fingerprint(user_msg)` 匹配（去除非字母数字字符，取前40位小写）
    - 匹配到直接 `f.unlink()`
    - 扫描范围限 recent/ 目录，避免误删其他文件

    **文件命名约定：**
    - Pending: `{timestamp}_pending_{session_id[:8]}_{title}.md`
    - 完整对: `{timestamp}_turn_{session_id[:8]}_{title}.md`
    - 完整对由 `_on_session_end` 兜底也可写入（后缀 `end_`）

    这样 cleanup 扫描 `*_pending_*.md` 能精确命中 pending 文件。

27. **文档与代码不同步——推前必须审查！**：修改了协议/路径/结构后如果不同步更新 README、文章.md、SKILL.md 的相关描述，下次有人加载 skill 时会拿到与运行系统不一致的说明。**推前审查 checklist：**

28. **L1 压缩是事件驱动自触发，无 cron。** 插件在 `_write_recent()` 和 `_on_post_llm_call()` 写入后立即检查大小并触发压缩——写入即检测，无需周期巡检。`_write_pending()` 会写入 pending 条目但不触发压缩，不过下一轮 `post_llm_call` 或 `pre_llm_call` 必然覆盖。

29. **容量参数在 `scripts/mem_config.py` 集中管理，不分散在各脚本中。** 调整容量时只改这一个文件，所有消费方（3 脚本 + 1 插件）自动生效。切勿直接去改 `mem_compress.py`/`mem_consolidate.py`/`mem_retire.py` 中的局部变量——它们已全部改为从 `mem_config.py` 导入。

30. **修改容量后须同步到所有位置：** `mem_config.py` 同时存在于：
    - `~/AppData/Local/hermes/scripts/mem_config.py`（运行版）
    - `D:\\AI\\snowfox-memory-continuity\\scripts\\mem_config.py`（GitHub 项目）
    - SKILL.md 中的容量表、内联脚本注释（以 `MAX_KB=50; KEEP_KB=45` 等注释形式）
    - `references/capacity-config.md`
    修改后须四向同步，否则部署和文档不一致。
    - SKILL.md 版本号变更 → README.md 表格、目录树、版本声明同步
    - 存储架构变更（目录→单文件） → README 目录树、文章.md 目录树、audit-checklist 中的路径
    - 插件钩子增减 → plugin.yaml 的 hooks 列表、SKILL.md 的钩子描述
    - 压缩脚本改动 → 检查 all 3 个脚本（mem_compress/consolidate/retire）的 `parse()` 签名一致
    - 审查方法：`git diff --stat` 看改动范围 → `git diff <file>` 逐文件审查 → 逐一检查对应文档段

31. **L1 压缩安全兜底——`keep.pop(0)` 在 `break` 前执行，可能删光所有段**：`mem_compress.py` 的移除循环在 `break` 判断之前执行 `keep.pop(0)`。如果第一段的大小就达到 `need_remove`，`keep` 变空列表，写入只剩 header → recent.md 所有历史丢失。

    **2026-06-29 修复：** 在 `open(L1, "w", ...)` 前加安全检查：
    ```python
    if not keep:
        keep = [taken[-1]]  # 放回最后被移除的一段
        taken.pop()
        removed = sum(len(s.encode("utf-8")) for s in taken)
        print("  [safety] keeping 1 section to avoid empty recent.md")
    ```

    **恢复方法：** 如果 recent.md 已被清空，从 Hermes 的 `state.db`（SQLite）重建：
    ```python
    import sqlite3, os
    from datetime import datetime
    db = sqlite3.connect(f"file:{os.environ['USERPROFILE']}/AppData/Local/hermes/state.db?mode=ro", uri=True)
    sessions = db.execute("SELECT session_id, MAX(id) FROM messages GROUP BY session_id ORDER BY MAX(id) DESC LIMIT 20").fetchall()
    # ... 提取 user/assistant 对，按 `## {timestamp} | session={sid}` 格式写入 recent.md
    ```
    详见 `references/recover-recent-from-db.md`。

32. **L3 清理必须彻底——一次完成，不要留尾巴**。用户对"只清理一部分"非常不满（"给我狠狠的压缩"）。清理 L3 时：
    - 解析全部 `## ` 段，不能只处理最近几段
    - 空内容判据包括但不限于：`(空)`、`（空）`、`(summary)`、`从L2合并的存档条目，内容为空`、空白行
    - 去重要归一化后比对，包括去掉 `同[N]：` 前缀
    - 无标题/垃圾标题（`session=unknown`, `compressed-from-L1` 等）一起过滤
    - 总长度 <20 字符的段直接视为空
    - 完成后重新验证文件（`wc -l` + 前几行检查），确保没有漏网之鱼
    - 如果第一遍跑完还有残留，继续第二遍直到完全干净

33. **L3 标签必须从摘要首句提取主题，不能用 `consolidated`**：`mem_consolidate.py` 写入 L3 时，标签由以下算法推导：
    ```python
    first_line = cleaned.strip().split('\\n')[0][:60]
    for pfx in ["- ", "• ", "关于", "本次", "会话"]:
        first_line = first_line[len(pfx):] if first_line.startswith(pfx) else first_line
    topic = first_line if len(first_line) > 4 else "summary"
    ```
    这使 L3 可按主题检索而非全是 `## consolidated`。如果未来要加退火或聚类标签，改 `mem_consolidate.py` 的这段 `extract topic` 逻辑即可。

34. **记忆系统维护：批量发现 → 自省校验 → 批量修复**：当遇到记忆系统多个结构性问题时，正确的流程是：
    - 一次性扫描所有相关脚本（compress/consolidate/retire/plugin/SKILL.md/references），发现全部问题
    - 列给用户确认，但同时对每项自省校验（用户指出的问题中可能部分其实不存在、或已有自动修复机制）
    - 用户确认后，**一次性提交所有代码修复**（不要一个一个来——用户明确表示"三个代码修一起上"）
    - 同步修改 SKILL.md 和 references 文件
    - 部署运行版 + 推 GitHub 一次完成
    - 最后全面验证所有改动
