#!/usr/bin/env python3
"""Повтор сравнения поиска на исправленной библиотеке недели 5.

Воспроизводит методику notebooks/search_METHOD.md и код ячеек
notebooks/search_lab.ipynb на корпусе library/search_corpus_dedup.jsonl:
- токенизация: [a-zа-яё0-9]+, стоп-слова, слова длиной > 1;
- BM25 с k1=1.2, b=0.75;
- векторный поиск intfloat/multilingual-e5-small с префиксами
  query:/passage: и нормализацией векторов.

Запуск:
  /home/artem/ai4science/week_5/.venv/bin/python src/repeat_search_dedup.py

Выход: results/week5_search_dedup.json
"""
import json, math, re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "library" / "search_corpus_dedup.jsonl"
OUT = ROOT / "results" / "week5_search_dedup.json"
MODEL_NAME = "intfloat/multilingual-e5-small"

QUERIES = [
    "coupling between periodic and aperiodic variability in X-ray pulsars",
    "broad wings around pulse frequency peaks in power spectra",
    "accretion column eclipse phase resolved variability",
    "Почему шумовая переменность зависит от фазы пульсаций?",
    "Какие ограничения есть у моделей переменности EXO 2030+375?",
]

STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were which with we our can".split())


def tokenize(text):
    return [w for w in re.findall(r"[a-zа-яё0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def main():
    docs = [json.loads(line) for line in CORPUS.open(encoding="utf-8")]
    # text уже готов в корпусе (title + ". " + abstract); abstract отсутствует.
    n_docs = len(docs)

    # --- BM25 index ---
    index = defaultdict(dict)
    doc_len = []
    for i, d in enumerate(docs):
        tokens = tokenize(d["text"])
        doc_len.append(len(tokens))
        for word, tf in Counter(tokens).items():
            index[word][i] = tf
    avg_len = sum(doc_len) / n_docs

    def bm25_scores(query, k1=1.2, b=0.75):
        scores = np.zeros(n_docs)
        for w in tokenize(query):
            postings = index.get(w, {})
            w_idf = math.log(1 + (n_docs - len(postings) + 0.5) / (len(postings) + 0.5))
            for i, tf in postings.items():
                scores[i] += w_idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * doc_len[i] / avg_len))
        return scores

    # --- vector encoder ---
    encoder = SentenceTransformer(MODEL_NAME)

    def encode(texts, role):
        prefix = {"query": "query: ", "passage": "passage: "}[role]
        return encoder.encode([prefix + t for t in texts], normalize_embeddings=True, show_progress_bar=False)

    doc_vecs = encode([d["text"] for d in docs], "passage")

    def vec_scores(query):
        return doc_vecs @ encode([query], "query")[0]

    def ranking(scores, k=3, positive_only=True):
        order = [int(i) for i in np.argsort(-scores)[:k]]
        if positive_only:
            order = [i for i in order if scores[i] > 0]
        return order

    def metrics(ranked, relevant, k=10):
        hits = [1 if i in relevant else 0 for i in ranked[:k]]
        first = next((r for r, h in enumerate(hits, 1) if h), None)
        dcg = sum(h / math.log2(r + 1) for r, h in enumerate(hits, 1))
        ideal = sum(1 / math.log2(r + 1) for r in range(1, min(k, len(relevant)) + 1))
        return {"точность@5": sum(hits[:5]) / 5, f"полнота@{k}": sum(hits) / len(relevant),
                "MRR": 1 / first if first else 0.0, f"nDCG@{k}": dcg / ideal}

    # Релевантность: для каждого запроса подходящие работы по названию и аннотации.
    # Оценка качественная, по методике. Здесь отмечаем подходящие вручную по выдаче.
    relevant = {q: set() for q in QUERIES}

    results = {"model_name": MODEL_NAME, "queries": QUERIES, "n_docs": n_docs,
               "bm25": {"k1": 1.2, "b": 0.75}, "retrievals": [], "metrics": {}}
    for q in QUERIES:
        sb, sv = bm25_scores(q), vec_scores(q)
        rb, rv = ranking(sb), ranking(sv, positive_only=False)
        results["retrievals"].append({
            "query": q,
            "bm25": [{"id": docs[i]["id"], "title": docs[i]["title"], "score": float(sb[i])} for i in rb],
            "vector": [{"id": docs[i]["id"], "title": docs[i]["title"], "score": float(sv[i])} for i in rv],
        })

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"записан {OUT} — {n_docs} документов, {len(QUERIES)} запросов")


if __name__ == "__main__":
    main()