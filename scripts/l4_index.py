"""L4 语义索引构建 — 读取 archive.md，构建 TF-IDF 索引并缓存。
每条段解析标题中的 【重复×N】 标记 → 权重（1 + log2(N)），存入 meta.json，
供 l4_search.py 评分加权（重复合并过的记忆排位更高）。"""

import json, os, pickle, re, sys
from pathlib import Path

HH = os.environ.get("HERMES_HOME") or str(Path.home() / "AppData/Local/hermes")
ARC = HH + "/memories/archive.md"
IDX = HH + "/memories/archive.index.pkl"
META = HH + "/memories/archive.meta.json"


def parse(content: str) -> list[dict]:
    """解析 archive.md 为带标题的段列表。"""
    lines = content.split("\n")
    sections = []
    cur_title = "(header)"
    cur_lines = []
    in_hdr = True

    for line in lines:
        if in_hdr:
            if line.startswith("## "):
                in_hdr = False
                if cur_lines:
                    sections.append({"title": cur_title, "text": "\n".join(cur_lines)})
                cur_title = line[3:].strip()
                cur_lines = [line]
            else:
                cur_lines.append(line)
        else:
            if line.startswith("## ") and not line.startswith("### "):
                if cur_lines:
                    sections.append({"title": cur_title, "text": "\n".join(cur_lines)})
                cur_title = line[3:].strip()
                cur_lines = [line]
            else:
                cur_lines.append(line)

    if cur_lines:
        sections.append({"title": cur_title, "text": "\n".join(cur_lines)})
    return sections


def build():
    if not os.path.exists(ARC):
        print("L4 index: archive.md not found"); return
    # sklearn 惰性导入：仅 build 需要，避免无 sklearn 环境 import 失败
    from sklearn.feature_extraction.text import TfidfVectorizer

    content = open(ARC, encoding="utf-8").read()
    sections = parse(content)
    if len(sections) <= 1:
        print("L4 index: no sections to index"); return

    texts = [s["text"] for s in sections]
    titles = [s["title"] for s in sections]
    # 权重：标题/正文中的 【重复×N】 → 1 + log2(N)；无标记 = 1.0
    weights = []
    for s in sections:
        m = re.search(r"【重复×(\d+)】", s["title"] + "\n" + s["text"])
        if m:
            n = max(int(m.group(1)), 1)
            weights.append(1.0 + __import__("math").log2(n))
        else:
            weights.append(1.0)

    vectorizer = TfidfVectorizer(
        max_features=10000,
        stop_words="english",
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b",
        norm="l2",
    )
    matrix = vectorizer.fit_transform(texts)

    with open(IDX, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "matrix": matrix}, f)
    with open(META, "w", encoding="utf-8") as f:
        json.dump({"titles": titles, "count": len(sections), "weights": weights}, f, ensure_ascii=False)

    print(f"L4 index: {len(sections)} sections indexed ({matrix.shape[1]} features, {sum(w > 1 for w in weights)} boosted)")


if __name__ == "__main__":
    build()
