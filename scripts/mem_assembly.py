"""记忆注入预算制组装 — 公共模块（插件与 memory_maintenance.py 共用）。

解决的问题：全量注入 _assembled_context.md（154KB ≈ 5万+ token）导致
DeepSeek 240s 无 chunk 被 openresty 掐断。策略改为「注入预算制」：
- F0 / USER 全量优先（小且关键，永不裁剪）
- L1 / L2 / L3 按权重分配剩余预算，超预算段不注入（仍在磁盘上，不删除）
- 磁盘各层保留上限不变，本模块只约束「每轮注入 LLM 的量」

token 估算：CJK 1 字 ≈ 1 token，其余 4 字符 ≈ 1 token（DeepSeek 常见估算）。
36KB 中文 ≈ 1.2 万 token，加系统提示/工具定义/当前轮后总窗口约 3 万内，
距 50K 断流点留足余量。
"""
from pathlib import Path

# 默认注入预算（KB）；与 mem_config.ASSEMBLY_BUDGET_KB 保持一致
DEFAULT_BUDGET_KB = 36
# 权重：L1(近期纪要) > L2(中期摘要) > L3(长期记忆)
L1_WEIGHT = 5
L2_WEIGHT = 3
L3_WEIGHT = 2


def clip(text: str, limit: int) -> str:
    """压缩空白并截断到 limit 字符，超长加省略号。"""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit] + " …"


def est_tokens(text: str) -> int:
    """粗略 token 估算：CJK 1 字 ≈ 1 token，其余 4 字符 ≈ 1 token。"""
    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return cjk + (len(text) - cjk) // 4


def parse_sections(content: str) -> tuple[str, list[str]]:
    """拆出文件头与 ## 分段。头 = 首个 ## 前的所有行（含空行/注释）。"""
    lines = content.split("\n")
    hdr = ""
    secs = []
    cur = []
    in_hdr = True
    for line in lines:
        if in_hdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"
                continue
            in_hdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur:
                secs.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        secs.append("\n".join(cur))
    return hdr, secs


def _take_newest(secs: list[str], budget: int) -> str:
    """从尾部（最新）向前取段，段超预算时至少保留一段。"""
    kept = []
    total = 0
    for sec in reversed(secs):
        size = len(sec.encode("utf-8"))
        if total + size > budget and kept:
            break
        kept.insert(0, sec)
        total += size
    return "\n".join(kept)


def _take_oldest(secs: list[str], budget: int) -> str:
    """从头部（最早）向后取段，段超预算时至少保留一段。"""
    kept = []
    total = 0
    for sec in secs:
        size = len(sec.encode("utf-8"))
        if total + size > budget and kept:
            break
        kept.append(sec)
        total += size
    return "\n".join(kept)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def assemble_budgeted(m: Path, budget_kb: int = DEFAULT_BUDGET_KB) -> str:
    """按预算组装五级记忆，返回完整文本（含版本头）。

    顺序：USER → F0 → L3 → L2 → L1（与历史组装顺序一致）。
    L3 保留头部（长期沉淀），L2/L1 保留尾部（近期信息）。
    """
    from datetime import datetime

    user_s = _read(m / "user.md")
    fixed_s = _read(m / "fixed.md")
    l3_s = _read(m / "long_term.md")
    l2_s = _read(m / "summary.md")
    l1_s = _read(m / "recent.md")

    overhead = 400  # 版本头 + 各层标题 + 分隔符，约 0.4KB
    budget = budget_kb * 1024
    used = len(user_s.encode("utf-8")) + len(fixed_s.encode("utf-8")) + overhead
    remain = max(budget - used, 0)

    total_w = L1_WEIGHT + L2_WEIGHT + L3_WEIGHT
    l3_b = int(remain * L3_WEIGHT / total_w)
    l2_b = int(remain * L2_WEIGHT / total_w)
    l1_b = remain - l3_b - l2_b  # L1 拿剩余（含舍入余量）

    parts = []
    build_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    parts.append(f"<!-- SnowFox Memory Assembly | built: {build_ts} | budget={budget_kb}KB -->")
    if user_s:
        parts.append("## USER\n" + user_s)
    if fixed_s:
        parts.append("## F0\n" + fixed_s)
    if l3_s:
        _, secs = parse_sections(l3_s)
        if secs:
            parts.append("## L3\n" + _take_oldest(secs, l3_b))
    if l2_s:
        _, secs = parse_sections(l2_s)
        if secs:
            parts.append("## L2\n" + _take_newest(secs, l2_b))
    if l1_s:
        _, secs = parse_sections(l1_s)
        if secs:
            parts.append("## L1\n" + _take_newest(secs, l1_b))

    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys
    m = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "AppData/Local/hermes/memories"
    text = assemble_budgeted(m)
    print(f"assembly: {len(text)}B = {len(text)/1024:.1f}KB, est {est_tokens(text)} tokens")
