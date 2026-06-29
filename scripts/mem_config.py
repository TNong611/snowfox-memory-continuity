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


def get_config() -> dict:
    """Return a snapshot dict for inspection / future dynamic loader."""
    return {
        "L1":   {"max_kb": L1_MAX_KB,   "keep_kb": L1_KEEP_KB},
        "L2":   {"max_kb": L2_MAX_KB,   "keep_kb": L2_KEEP_KB},
        "L3":   {"max_kb": L3_MAX_KB,   "keep_kb": L3_KEEP_KB},
        "L4":   {"max_kb": L4_MAX_KB,   "keep_kb": L4_KEEP_KB},
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
