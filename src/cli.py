"""
Komut satiri arayuzu: kullanicidan soru alir, hibrit retrieval + LLM
zincirinden gecirir, cevabi gosterir. Turkce karakterlerin dogru
gorunmesi icin UTF-8 encoding zorlanir.
"""
import sys
import os
import io

sys.path.insert(0, os.path.dirname(__file__))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from db import get_connection
from foundry_session import init_foundry_full_session
from retrieval import bm25_search_with_fallback, semantic_search, rrf_fuse, has_sufficient_context
from llm import generate_answer

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "afet.db")

_ACIL_MOD_METNI = (
    "\n========================================\n"
    "\U0001f6a8 ACİL DURUM MODU\n"
    "========================================\n"
    "Hemen 112'yi arayın.\n\n"
    "Söyleyebileceğiniz örnek cümle:\n"
    "'[Bulunduğunuz yer] adresinde, [durum: kanama/kırık/biliç kaybı/\n"
    "nefes darlığı] var. Yardım gerekiyor.'\n\n"
    "Sakin kalın. Mümkünse yaralıyı hareket ettirmeyin.\n"
    "========================================\n"
)


def get_embedding(client, model_id, text):
    resp = client.embeddings.create(model=model_id, input=[text])
    return resp.data[0].embedding


def answer_query(conn, client, emb_model_id, chat_model_id, query):
    query_vector = get_embedding(client, emb_model_id, query)
    bm25_sonuc = bm25_search_with_fallback(conn, query, k=5)
    semantic_sonuc = semantic_search(conn, query_vector, k=5)
    hibrit_sonuc = rrf_fuse(bm25_sonuc, semantic_sonuc, k=3)
    top_semantic_score = semantic_sonuc[0]["score"] if semantic_sonuc else 0.0
    yeterli = has_sufficient_context(hibrit_sonuc, top_semantic_score=top_semantic_score)
    cevap = generate_answer(client, chat_model_id, query, hibrit_sonuc, yeterli)
    return cevap, hibrit_sonuc


def main():
    print("=" * 60)
    print("Afet Ani Offline Ilk Yardim Asistani")
    print("Cikmak icin 'q' yazip Enter'a basin.")
    print("=" * 60)

    conn = get_connection(DB_PATH)
    print("Foundry Local yukleniyor, lutfen bekleyin...")
    client, emb_model_id, chat_model_id = init_foundry_full_session()
    print("Hazir.\n")

    while True:
        soru = input("Sorunuz: ").strip()
        if soru.lower() in ("q", "quit", "exit"):
            print("Gorusmek uzere.")
            break
        if not soru:
            continue

        # !112 acil bypass - hicbir retrieval/embedding cagrilmaz
        if soru.lower() == "!112":
            print(_ACIL_MOD_METNI)
            continue

        cevap, kaynaklar = answer_query(conn, client, emb_model_id, chat_model_id, soru)

        print()
        print("CEVAP:")
        print(cevap)
        print()

        if kaynaklar:
            print("Kullanilan kaynaklar:")
            for k in kaynaklar:
                print(f"  - {k['category']} / {k['source_doc']}")
        print()


if __name__ == "__main__":
    main()
