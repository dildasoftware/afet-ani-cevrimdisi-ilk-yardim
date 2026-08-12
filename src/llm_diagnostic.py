"""
Uctan uca tani testi: tek Foundry Local oturumundan hem embedding hem
chat kullanarak, biri cevaplanabilir biri kasitli alakasiz iki soruyu test eder.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from foundry_session import init_foundry_full_session
from retrieval import bm25_search_with_fallback, semantic_search, rrf_fuse, has_sufficient_context
from llm import generate_answer

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "afet.db")

TEST_SORULARI = [
    "yanığım var ne yapmalıyım",
    "arabamın lastiği patladı ne yapmalıyım",
]


def get_embedding(client, model_id, text):
    resp = client.embeddings.create(model=model_id, input=[text])
    return resp.data[0].embedding


def run_llm_diagnostic():
    conn = get_connection(DB_PATH)
    client, emb_model_id, chat_model_id = init_foundry_full_session()

    for soru in TEST_SORULARI:
        print(f"SORU: {soru}")
        soru_vektor = get_embedding(client, emb_model_id, soru)
        bm25_sonuc = bm25_search_with_fallback(conn, soru, k=5)
        semantic_sonuc = semantic_search(conn, soru_vektor, k=5)
        hibrit_sonuc = rrf_fuse(bm25_sonuc, semantic_sonuc, k=3)
        yeterli = has_sufficient_context(hibrit_sonuc)

        print(f"  Yeterli baglam var mi: {yeterli}")
        if hibrit_sonuc:
            print(f"  En iyi RRF skoru: {hibrit_sonuc[0]['rrf_score']:.4f}")

        cevap = generate_answer(client, chat_model_id, soru, hibrit_sonuc, yeterli)
        print(f"  CEVAP: {cevap}")
        print()


if __name__ == "__main__":
    run_llm_diagnostic()
