"""一次性迁移：recent.md 全文条目 → 纪要格式（截断 + 去重 + 限量）。
清掉历史污染段（skill 全文、compressed-from-L1 段），只保留最近 N 条纪要。
旧全文精华已沉淀在 summary.md / F0，不重复保留。
运行前自动备份为 recent.md.bak。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mem_assembly import clip, parse_sections  # noqa: E402

M = Path.home() / "AppData/Local/hermes/memories"
RECENT = M / "recent.md"
KEEP_ENTRIES = 20
USER_LIMIT = 300
ASST_LIMIT = 600


def extract_pair(sec: str) -> tuple[str, str]:
    """从条目里提取 (user, assistant) 全文。兼容旧 `### User` 与新 `**User**` 格式。"""
    u_buf, a_buf = [], []
    in_u = in_a = False
    for ln in sec.split("\n"):
        if ln.startswith("**User**"):
            in_u, in_a = True, False
            continue
        if ln.startswith("**Assistant**"):
            in_u, in_a = False, True
            continue
        if ln.startswith("### User"):
            in_u, in_a = True, False
            continue
        if ln.startswith("### Assistant"):
            in_u, in_a = False, True
            continue
        if ln.startswith("---"):
            in_u = in_a = False
            continue
        if in_u:
            u_buf.append(ln)
        elif in_a:
            a_buf.append(ln)
    return "\n".join(u_buf).strip(), "\n".join(a_buf).strip()


def fingerprint(text: str) -> str:
    return "".join(c for c in text if c.isalnum())[:40].lower()


def main():
    if not RECENT.exists():
        print("recent.md not found"); return
    content = RECENT.read_text(encoding="utf-8", errors="replace")
    hdr, secs = parse_sections(content)

    briefs = []
    for sec in secs:
        user, asst = extract_pair(sec)
        if not user:
            continue  # 跳过污染段（skill 全文、摘要段等无 User/Assistant 结构）
        briefs.append((sec.split("\n", 1)[0], clip(user, USER_LIMIT), clip(asst, ASST_LIMIT)))

    # 去重（按 user 指纹）
    seen, uniq = set(), []
    for head, u, a in briefs:
        fp = fingerprint(u)
        if fp in seen:
            continue
        seen.add(fp)
        uniq.append((head, u, a))

    tail = uniq[-KEEP_ENTRIES:]
    out = [f"# L1 Recent — 近期纪要（{len(tail)} 条，预算制注入）\n"]
    for head, u, a in tail:
        out.append(f"{head} | 纪要\n\n**User**: {u}\n\n**Assistant**: {a}\n\n---\n_雪狐记录 | 纪要\n")

    text = "\n".join(out)
    backup = RECENT.with_suffix(".md.bak")
    RECENT.rename(backup)
    RECENT.write_text(text, encoding="utf-8")
    print(f"migrated: {len(secs)} sections → {len(tail)} briefs ({len(text)/1024:.1f}KB)")
    print(f"backup: {backup}")


if __name__ == "__main__":
    main()
