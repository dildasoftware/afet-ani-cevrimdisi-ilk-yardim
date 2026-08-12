"""
Doküman ingestion: data/documents/ altındaki tüm .md dosyalarını okur,
chunk_by_step ile böler, klasör adını category olarak etiketler,
normalize_tr ile normalize eder ve SQLite'a yazar.

Bu ilk sürüm embedding İÇERMEZ (Faz 2'de eklenecek) — amaç önce metin
katmanının doğru çalıştığını kanıtlamak.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection, init_db, insert_chunk
from chunking import chunk_by_step
from normalize_tr import normalize_tr

DOCUMENTS_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "documents"
)
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "afet.db"
)


def ingest_all(documents_root: str = DOCUMENTS_ROOT, db_path: str = DB_PATH):
    conn = get_connection(db_path)
    init_db(conn)

    kategori_sayaclari = {}
    toplam_chunk = 0

    kategoriler = sorted(
        d for d in os.listdir(documents_root)
        if os.path.isdir(os.path.join(documents_root, d))
    )

    for kategori in kategoriler:
        kategori_yolu = os.path.join(documents_root, kategori)
        dosyalar = sorted(
            f for f in os.listdir(kategori_yolu) if f.endswith(".md")
        )
        kategori_sayaclari[kategori] = 0

        for dosya_adi in dosyalar:
            dosya_yolu = os.path.join(kategori_yolu, dosya_adi)
            with open(dosya_yolu, encoding="utf-8") as f:
                metin = f.read()

            baslik_satiri = ""
            for satir in metin.splitlines():
                if satir.strip().startswith("# "):
                    baslik_satiri = satir.strip().lstrip("#").strip()
                    break

            adimlar = chunk_by_step(metin)

            for adim in adimlar:
                normalize_edilmis = normalize_tr(f"{baslik_satiri} {adim}")
                insert_chunk(
                    conn,
                    source_doc=dosya_adi,
                    category=kategori,
                    content=adim,
                    normalized_content=normalize_edilmis,
                    chunk_strategy="step",
                    embedding=None,
                )
                kategori_sayaclari[kategori] += 1
                toplam_chunk += 1

    conn.close()
    return toplam_chunk, kategori_sayaclari


if __name__ == "__main__":
    toplam, sayaclar = ingest_all()
    print(f"TOPLAM CHUNK: {toplam}")
    for kategori, sayi in sorted(sayaclar.items()):
        print(f"  {kategori}: {sayi}")
