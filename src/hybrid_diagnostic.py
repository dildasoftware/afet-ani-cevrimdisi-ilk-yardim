"""
Hibrit retrieval tani testi.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from embeddings import init_foundry_embedding_session, get_embedding
from retrieval import bm25_search, semantic_search, rrf_fuse

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "afet.db")

TEST_SORULARI = [
    "kolum yaralandı ne yapmalıyım",
    "kanıyo nasıl durdururum",
    "bebeğim nefes alamıyor tıkandı",
    "çok korkuyorum ne yapmalıyım",
    "deprem oldu enkazın altındayım",
    "tekerlekli sandalyedeyim deprem oldu ne yapmalıyım",
    "112 dışında hangi numarayı arayabilirim",
    "yanığım var soğuk su tutayım mı",
]


def run_hybrid_diagnostic():
    conn = get_connection(DB_PATH)
    client, model_id = init_foundry_embedding_session()

    for soru in TEST_SORULARI:
        soru_vektor = get_embedding(client, model_id, soru)

        bm25_sonuc = bm25_search(conn, soru, k=5)
        semantic_sonuc = semantic_search(conn, soru_vektor, k=5)
        hibrit_sonuc = rrf_fuse(bm25_sonuc, semantic_sonuc, k=3)

        print(f"SORU: {soru}")
        print(f"  BM25 eslesme sayisi: {len(bm25_sonuc)}")
        for r in bm25_sonuc[:2]:
            print(f"    BM25: {r['category']} | {r['source_doc']} | {r['content'][:60]}")
        print(f"  HIBRIT (RRF) sonuclari:")
        for r in hibrit_sonuc:
            print(f"    RRF={r['rrf_score']:.4f} | {r['category']} | {r['source_doc']} | {r['content'][:70]}")
        print()


if __name__ == "__main__":
    run_hybrid_diagnostic()
