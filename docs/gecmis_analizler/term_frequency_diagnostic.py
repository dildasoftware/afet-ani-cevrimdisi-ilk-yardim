"""
Terim sıklığı tanı testi: iki sorunlu sorgudaki ("kolum yaralandı ne
yapmalıyım", "kanıyo nasıl durdururum") her bir terimin, 277 chunk'lık
korpusun kaçında gectigini olcer. Bir terim chunk'larin cok buyuk kismina
(orn. %15+) girdiginde bu terim ayirt edici degildir ve BM25 gurultusune
neden olur.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from normalize_tr import normalize_tr

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "afet.db")

SORUNLU_SORGULAR = [
    "kolum yaralandı ne yapmalıyım",
    "kanıyo nasıl durdururum",
]


def run_term_frequency_diagnostic():
    conn = get_connection(DB_PATH)
    toplam_chunk = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"Toplam chunk sayisi: {toplam_chunk}")
    print()

    for sorgu in SORUNLU_SORGULAR:
        normalized = normalize_tr(sorgu)
        terimler = [t for t in normalized.split() if t.strip()]
        print(f"SORGU: {sorgu}")
        print(f"  Normalize edilmis terimler: {terimler}")
        for terim in terimler:
            try:
                sayi = conn.execute(
                    "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?",
                    (terim,),
                ).fetchone()[0]
            except Exception as e:
                sayi = f"HATA: {e}"
            if isinstance(sayi, int):
                yuzde = (sayi / toplam_chunk) * 100
                bayrak = " <-- COK YAYGIN, AYIRT EDICI DEGIL" if yuzde >= 15 else ""
                print(f"    '{terim}': {sayi}/{toplam_chunk} chunk (%{yuzde:.1f}){bayrak}")
            else:
                print(f"    '{terim}': {sayi}")
        print()


if __name__ == "__main__":
    run_term_frequency_diagnostic()
