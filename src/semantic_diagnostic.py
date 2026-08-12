"""
Semantic arama tani testi: gundelik/gayri-resmi sorularla gercek dokumanlar
arasindaki kosinus benzerligini olcer.
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from embeddings import init_foundry_embedding_session, get_embedding

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


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def run_diagnostic():
    conn = get_connection(DB_PATH)
    client, model_id = init_foundry_embedding_session()

    chunk_rows = conn.execute(
        "SELECT c.id, c.source_doc, c.category, c.content, e.vector "
        "FROM chunks c JOIN embeddings e ON c.id = e.chunk_id"
    ).fetchall()

    print(f"Toplam embed edilmis chunk: {len(chunk_rows)}")
    print()

    for soru in TEST_SORULARI:
        soru_vektor = get_embedding(client, model_id, soru)
        skorlar = []
        for row in chunk_rows:
            chunk_vektor = json.loads(row["vector"])
            skor = cosine_similarity(soru_vektor, chunk_vektor)
            skorlar.append((skor, row["source_doc"], row["category"], row["content"][:70]))
        skorlar.sort(reverse=True, key=lambda x: x[0])

        print(f"SORU: {soru}")
        for skor, kaynak, kategori, icerik in skorlar[:3]:
            print(f"  {skor:.4f} | {kategori} | {kaynak} | {icerik}")
        print()


if __name__ == "__main__":
    run_diagnostic()
