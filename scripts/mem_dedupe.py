"""L3/L4 重复记忆去重合并 — 相似条目压缩为同一条并提升搜索权重。

机制：
- 归一化（去空白/标点/标题/时间戳/雪狐尾注）后按相似度聚类：
  包含关系（短⊂长）或 SequenceMatcher ratio >= 阈值（默认 0.72）判为同一条记忆
- 每组保留信息最全的一条（最长），独特行并入，标题标注 【重复×N】
- 高重复条目写回文件头部 → L3 组装（_take_oldest 从头取）自然优先注入
- L4 索引 meta.json 写入 weights（1 + log2(N)），l4_search 评分 ×weight

用法：
  python mem_dedupe.py            # dry-run：只报告将合并的组
  python mem_dedupe.py --apply    # 实际写回 L3/L4 并重建 L4 索引
  python mem_dedupe.py --threshold 0.65   # 调整相似度阈值
"""
import os, re, subprocess, sys
from difflib import SequenceMatcher

HH = os.environ.get("HERMES_HOME") or os.environ["USERPROFILE"] + "/AppData/Local/hermes"
L3 = HH + "/memories/long_term.md"
ARC = HH + "/memories/archive.md"

# 通用标题词：不携带信息，合并后从内容首行重新提取标题
GENERIC_TITLES = re.compile(
    r"^(consolidated|summary|user|assistant|session=\S+|"
    r"\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}(:\d{2})?)?(\s*\|\s*.*)?)$",
    re.IGNORECASE,
)
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?")
SESSION_RE = re.compile(r"session=\S+")
FOOT_RE = re.compile(r"^_?雪狐记录.*$")


def parse(content: str) -> tuple[str, list[str]]:
    """拆出文件头与 ## 段（与 mem_consolidate.py 同款）。"""
    lines = content.split("\n")
    hdr = ""; secs = []; cur = []; inHdr = True
    for line in lines:
        if inHdr:
            if line.startswith("# ") or line.startswith("_") or line.strip() == "" or line == "---":
                hdr += line + "\n"
                continue
            inHdr = False
        if line.startswith("## ") and not line.startswith("### "):
            if cur:
                secs.append("\n".join(cur))
            cur = [line]
        else:
            cur.append(line)
    if cur:
        secs.append("\n".join(cur))
    return hdr, secs


def norm(text: str) -> str:
    """归一化：去标题/时间戳/session/尾注/标点/空白，小写。用于相似度比较。"""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line == "---" or line.startswith("## ") or line.startswith("### "):
            continue
        if FOOT_RE.match(line):
            continue
        line = TS_RE.sub("", line)
        line = SESSION_RE.sub("", line)
        lines.append(line)
    joined = "".join(lines)
    return "".join(c for c in joined.lower() if c.isalnum())


def section_title(sec: str) -> str:
    m = re.match(r"^##\s+(.+)$", sec.split("\n", 1)[0])
    return m.group(1).strip() if m else ""


def _extract_topic(text: str) -> str:
    """从内容提取有意义的标题：跳过标题行/通用词/时间戳/尾注，取首个有信息量的行。"""
    for line in text.strip().split("\n"):
        raw = line.strip()
        if raw.startswith("## ") or not raw:
            continue
        line = re.sub(r"^[-•*#\s]+", "", raw)
        line = re.sub(r"^同\s*\[\d+\][：:]?", "", line).strip()
        line = TS_RE.sub("", line)
        line = SESSION_RE.sub("", line).strip()
        if not line or len("".join(c for c in line if c.isalnum())) < 4:
            continue
        if FOOT_RE.match(line) or GENERIC_TITLES.match(line):
            continue
        return line[:60]
    return "记忆条目"


def _is_noise_line(line: str) -> bool:
    """合并时跳过：重复引用行（同[N]）、纯时间戳/session 行、无信息量行。"""
    nl = norm(line)
    if not nl or len(nl) < 4:
        return True
    if re.match(r"^同\s*\[\d+\][：:]", line.strip()):
        return True
    stripped = SESSION_RE.sub("", TS_RE.sub("", line.strip())).strip("，。；;, ")
    return len("".join(c for c in stripped if c.isalnum())) < 4


def weight_of(sec: str) -> float:
    """解析条目内的重复次数 → 权重（无标记 = 1.0）。"""
    m = re.search(r"【重复×(\d+)】", sec)
    if not m:
        return 1.0
    n = int(m.group(1))
    return 1.0 + __import__("math").log2(n)


def cluster(secs: list[str], threshold: float) -> list[list[str]]:
    """贪心聚类：按长度降序，最长的作种子吸收相似段。"""
    indexed = sorted(range(len(secs)), key=lambda i: -len(secs[i]))
    norms = [norm(s) for s in secs]
    groups: list[list[int]] = []
    used = set()
    for i in indexed:
        if i in used:
            continue
        g = [i]
        used.add(i)
        ni = norms[i]
        for j in indexed:
            if j in used or not ni:
                continue
            nj = norms[j]
            if not nj:
                continue
            similar = (ni in nj or nj in ni) or SequenceMatcher(None, ni, nj).ratio() >= threshold
            if similar:
                g.append(j)
                used.add(j)
        groups.append(g)
    return [[secs[i] for i in g] for g in groups]


def merge_group(group: list[str]) -> str:
    """合并一组相似段：保留最长一条，独特行并入，标题标注 【重复×N】。"""
    base = max(group, key=len)
    base_lines = base.split("\n")
    base_norm_lines = {norm(l) for l in base_lines}
    extra_lines: list[str] = []
    for other in group:
        if other == base:
            continue
        for line in other.split("\n"):
            ls = line.strip()
            nl = norm(line)
            if not ls or not nl or ls == "---" or ls.startswith("## "):
                continue
            if _is_noise_line(line):
                continue
            if nl in base_norm_lines or nl in {norm(x) for x in extra_lines}:
                continue
            extra_lines.append(ls)
    # 标题：通用词则从内容首行提取
    title = section_title(base)
    if not title or GENERIC_TITLES.match(title):
        title = _extract_topic(base)
    # 正文：剔除 base 的旧标题行（首行 ## ）与噪音行，保留其余
    body_lines = []
    for i, l in enumerate(base_lines):
        ls = l.strip()
        if not ls:
            continue
        if i == 0 and ls.startswith("## "):
            continue
        if _is_noise_line(l):
            continue
        body_lines.append(ls)
    merged_body = "\n".join(body_lines) + (
        "\n" + "\n".join(extra_lines) if extra_lines else ""
    )
    return f"## {title} 【重复×{len(group)}】\n{merged_body}"


def run(dry_run: bool, threshold: float) -> None:
    total_saved = 0
    for path, label in ((L3, "L3"), (ARC, "L4")):
        if not os.path.exists(path):
            print(f"  {label}: not found")
            continue
        content = open(path, "r", encoding="utf-8").read()
        hdr, secs = parse(content)
        if len(secs) < 2:
            print(f"  {label}: {len(secs)} 段，无需去重")
            continue
        groups = cluster(secs, threshold)
        dup_groups = [g for g in groups if len(g) > 1]
        if not dup_groups:
            print(f"  {label}: 无重复条目（{len(secs)} 段）")
            continue
        # 合并 + 高重复条目排前（权重降序）
        merged = [merge_group(g) if len(g) > 1 else g[0] for g in groups]
        merged.sort(key=weight_of, reverse=True)
        new_text = hdr + "\n".join(merged)
        saved = (len(content) - len(new_text)) / 1024
        total_saved += saved
        print(f"  {label}: {len(secs)} 段 → {len(merged)} 段，合并 {sum(len(g)-1 for g in dup_groups)} 条重复，省 {saved:.1f}KB")
        for g in dup_groups:
            print(f"    · [{len(g)}×] {section_title(g[0])[:48]}")
        if not dry_run:
            open(path, "w", encoding="utf-8").write(new_text)
    if dry_run:
        print(f"  预计共省 {total_saved:.1f}KB（--apply 生效）")
    elif os.path.exists(ARC):
        try:
            r = subprocess.run([sys.executable, HH + "/scripts/l4_index.py"],
                               capture_output=True, text=True, timeout=30)
            print("  " + (r.stdout or r.stderr).strip()[:200])
        except Exception as e:
            print(f"  [l4_index rebuild]: {e}")


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    thr = 0.72
    if "--threshold" in sys.argv:
        thr = float(sys.argv[sys.argv.index("--threshold") + 1])
    print("🧹 记忆去重合并 (" + ("dry-run" if dry else "apply") + f", threshold={thr})")
    run(dry, thr)
