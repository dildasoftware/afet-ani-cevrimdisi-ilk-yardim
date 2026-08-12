"""
data/afet.db icindeki tum chunk'lar icin Foundry Local'den embedding alir
ve embeddings tablosuna kaydeder.

Baglam zenginlestirme: her chunk icin kaynak dosyanin basligini embedding
metninin onune ekler (ornek: "Kanama Kontrolu 6. Kanayan yer uzerine...").
Bu, BM25 katmaninin normalized_content'te zaten kullandigi baslik-
zenginlestirme mantigini embedding katmanina da tasir.
content alani DEGISMEZ - sadece embedding'e giden gecici string zenginlesir.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection, upsert_embedding
from embeddings import init_foundry_embedding_session, get_embedding

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "afet.db")
DOCUMENTS_ROOT = os.path.join(PROJECT_ROOT, "data", "documents")


def _build_title_map(documents_root: str = DOCUMENTS_ROOT) -> dict:
    """Tum .md dosyalarini bir kez tarayip {dosya_adi: baslik} sozlugu olusturur.
    Ornek: {'01_kanama_kontrolu.md': 'Kanama Kontrolu', ...}"""
    title_map = {}
    for kategori in os.listdir(documents_root):
        kategori_yolu = os.path.join(documents_root, kategori)
        if not os.path.isdir(kategori_yolu):
            continue
        for dosya_adi in os.listdir(kategori_yolu):
            if not dosya_adi.endswith(".md"):
                continue
            dosya_yolu = os.path.join(kategori_yolu, dosya_adi)
            with open(dosya_yolu, encoding="utf-8") as f:
                for satir in f:
                    if satir.strip().startswith("# "):
                        title_map[dosya_adi] = satir.strip().lstrip("#").strip()
                        break
                else:
                    # Baslik bulunamazsa dosya adini kullan
                    title_map[dosya_adi] = dosya_adi.replace("_", " ").replace(".md", "")
    return title_map


def embed_all_chunks(db_path: str = DB_PATH):
    conn = get_connection(db_path)
    client, model_id = init_foundry_embedding_session()

    # Baslik sozlugunu bir kez olustur (O(24) dosya okuma)
    title_map = _build_title_map()
    print(f"Baslik sozlugu olusturuldu: {len(title_map)} dosya")

    rows = conn.execute("SELECT id, source_doc, content FROM chunks ORDER BY id").fetchall()
    basarili = 0
    basarisiz = []

    for i, row in enumerate(rows, start=1):
        chunk_id = row["id"]
        source_doc = row["source_doc"]
        content = row["content"]

        # Baglam zenginlestirme: baslik + content (normalize_tr UYGULANMAZ,
        # embedding modeli dogal dil bekliyor)
        baslik = title_map.get(source_doc, "")
        embed_text = f"{baslik} {content}" if baslik else content

        try:
            vektor = get_embedding(client, model_id, embed_text)
            upsert_embedding(conn, chunk_id, vektor)
            basarili += 1
        except Exception as e:
            basarisiz.append((chunk_id, str(e)))

        if i % 50 == 0 or i == len(rows):
            print(f"  ilerleme: {i}/{len(rows)}")

    conn.close()
    return basarili, basarisiz


if __name__ == "__main__":
    basarili, basarisiz = embed_all_chunks()
    print(f"BASARILI: {basarili}")
    print(f"BASARISIZ: {len(basarisiz)}")
    if basarisiz:
        for cid, err in basarisiz[:10]:
            print(f"  chunk_id={cid}: {err}")

