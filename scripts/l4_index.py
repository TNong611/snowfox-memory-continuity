"""L4 语义索引构建 — 读取 archive.md，构建 TF-IDF 索引并缓存。"""

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
        json.dump({"titles": titles, "count": len(sections)}, f, ensure_ascii=False)

    print(f"L4 index: {len(sections)} sections indexed ({matrix.shape[1]} features)")


if __name__ == "__main__":
    build()
