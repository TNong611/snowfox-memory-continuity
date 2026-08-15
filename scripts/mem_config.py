"""
Memory capacity configuration — single source of truth for all levels.
Import from here instead of hardcoding MAX/KEEP values.

Future: replace module-level constants with a JSON/config-file loader
for dynamic runtime adjustment (planned dynamic-adjustment module).
"""

# ── Level 1: Recent (recent.md) ──
L1_MAX_KB = 50      # Trigger: compress when exceeds this
L1_KEEP_KB = 45     # Target: trim to ≤ this after compression

# ── Level 2: Summary (summary.md) ──
L2_MAX_KB = 100     # Trigger: consolidate when exceeds this
L2_KEEP_KB = 90     # Target: trim to ≤ this after consolidation

# ── Level 3: Long-term (long_term.md) ──
L3_MAX_KB = 50      # Trigger: retire when exceeds this
L3_KEEP_KB = 45     # Target: trim to ≤ this after retirement

# ── Level 4: Archive (archive.md) ──
L4_MAX_KB = 0       # 0 = unlimited (no trigger)
L4_KEEP_KB = 0      # 0 = unlimited (no trim)

# ── Assembly injection budget (每轮注入 LLM 的记忆预算) ──
# 背景：全量注入 154KB ≈ 5万+ token 曾致 DeepSeek 240s 断流。
# 36KB 中文 ≈ 1.2 万 token；F0/USER 全量优先，L1/L2/L3 按权重分配。
# 磁盘各层保留上限不变，此预算只约束「组装进 _assembled_context.md 的量」。
ASSEMBLY_BUDGET_KB = 36

# L4 语义检索注入预算（KB）：预留给每轮自动 l4_search 结果的量
L4_INJECT_KB = 2

# 组装权重：L1(近期纪要) > L2(中期摘要) > L3(长期记忆)
ASSEMBLY_WEIGHTS = {"L1": 5, "L2": 3, "L3": 2}


def get_config() -> dict:
    """Return a snapshot dict for inspection / future dynamic loader."""
    return {
        "L1":   {"max_kb": L1_MAX_KB,   "keep_kb": L1_KEEP_KB},
        "L2":   {"max_kb": L2_MAX_KB,   "keep_kb": L2_KEEP_KB},
        "L3":   {"max_kb": L3_MAX_KB,   "keep_kb": L3_KEEP_KB},
        "L4":   {"max_kb": L4_MAX_KB,   "keep_kb": L4_KEEP_KB},
        "assembly": {
            "budget_kb": ASSEMBLY_BUDGET_KB,
            "l4_inject_kb": L4_INJECT_KB,
            "weights": ASSEMBLY_WEIGHTS,
        },
    }


def summary() -> str:
    """Human-readable config summary."""
    c = get_config()
    lines = ["Memory capacity config:"]
    for level, vals in c.items():
        mx = vals["max_kb"]
        kp = vals["keep_kb"]
        if mx == 0 and kp == 0:
            lines.append(f"  {level}: unlimited")
        else:
            lines.append(f"  {level}: max={mx}KB → keep≤{kp}KB")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
