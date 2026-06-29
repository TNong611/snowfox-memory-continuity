"""L4 语义检索 — 对 archive.md 进行 TF-IDF 语义搜索。"""

import json, os, pickle, sys
from pathlib import Path

HH = os.environ.get("HERMES_HOME") or str(Path.home() / "AppData/Local/hermes")
ARC = HH + "/memories/archive.md"
IDX = HH + "/memories/archive.index.pkl"
META = HH + "/memories/archive.meta.json"


def search(query: str, top_k: int = 5) -> list[dict]:
    from sklearn.metrics.pairwise import cosine_similarity

    if not os.path.exists(IDX):
        print("Index not found. Run l4_index.py first.", file=sys.stderr)
        return []
    if not os.path.exists(ARC):
        print("archive.md not found", file=sys.stderr)
        return []

    with open(IDX, "rb") as f:
        data = pickle.load(f)
    vectorizer = data["vectorizer"]
    matrix = data["matrix"]
    with open(META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    titles = meta["titles"]

    # vectorize query
    qv = vectorizer.transform([query])
    sims = cosine_similarity(qv, matrix)[0]

    # get top_k results
    pairs = [(i, sims[i]) for i in range(len(sims))]
    pairs.sort(key=lambda x: -x[1])

    # read archive content for snippets
    content = open(ARC, encoding="utf-8").read()
    sections = content.split("\n## ")

    results = []
    for idx, score in pairs[:top_k]:
        if score < 0.05:
            continue
        snippet = sections[idx] if idx < len(sections) else titles[idx]
        if len(snippet) > 400:
            snippet = snippet[:400] + "..."
        results.append({
            "title": titles[idx],
            "score": round(float(score), 3),
            "snippet": snippet.strip(),
        })

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python l4_search.py <query> [top_k]")
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    results = search(query, top_k)
    if not results:
        print("No matching results.")
        return

    print(f"\n## L4 搜索结果: \"{query}\"\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['score']:.3f}] {r['title']}")
        print(f"   {r['snippet'][:200]}")
        print()


if __name__ == "__main__":
    main()
