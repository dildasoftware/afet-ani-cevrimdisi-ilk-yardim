"""
Hibrit retrieval: BM25 (SQLite FTS5) + semantic (embedding kosinus benzerligi)
+ RRF (Reciprocal Rank Fusion) ile birlestirme.

ONEMLI TASARIM NOTU: FTS5 MATCH varsayilan olarak terimleri zimni AND ile
birlestirir (tum terimler ayni satirda olmali). Gunluk konusma dilindeki
sorgularda (soru kelimeleri, doldurma kelimeleri icerir) bu neredeyse hicbir
zaman eslesme bulamaz. Bu yuzden terimler OR ile birlestiriliyor - bu, BM25'in
"lexical/anahtar kelime" katmani olarak gorevini (en az bir terim eslesmesi
yeterli, semantic katman zaten anlamsal yakinligi karsiliyor) dogru sekilde
yerine getirmesini saglar.
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(__file__))

from normalize_tr import normalize_tr


_SORU_PARCACIKLARI = {
    normalize_tr(k) for k in [
        "ne", "nasıl", "mı", "mi", "mu", "mü", "midir", "mıdır",
        "niçin", "neden", "ise", "için", "gibi", "ile", "olursa",
        "olsa", "her", "bir", "bu", "şu", "o", "ki",
    ]
}


def bm25_search(conn, query, k=5):
    normalized_query = normalize_tr(query)
    terimler = [
        t for t in normalized_query.split()
        if t.strip() and t not in _SORU_PARCACIKLARI
    ]
    if not terimler:
        return []
    fts_query = " OR ".join(terimler)
    rows = conn.execute(
        """
        SELECT c.id, c.source_doc, c.category, c.content, bm25(chunks_fts) as score
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.rowid
        WHERE chunks_fts MATCH ?
        ORDER BY bm25(chunks_fts)
        LIMIT ?
        """,
        (fts_query, k),
    ).fetchall()
    return [dict(r) for r in rows]


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search(conn, query_vector, k=5):
    rows = conn.execute(
        """
        SELECT c.id, c.source_doc, c.category, c.content, e.vector
        FROM chunks c JOIN embeddings e ON c.id = e.chunk_id
        """
    ).fetchall()

    scored = []
    for row in rows:
        vec = json.loads(row["vector"])
        score = cosine_similarity(query_vector, vec)
        scored.append({
            "id": row["id"], "source_doc": row["source_doc"],
            "category": row["category"], "content": row["content"],
            "score": score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def rrf_fuse(bm25_results, semantic_results, k=5, rrf_k=60):
    scores = {}
    meta = {}
    semantic_scores = {}

    for rank, r in enumerate(bm25_results, start=1):
        cid = r["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        meta[cid] = r

    for rank, r in enumerate(semantic_results, start=1):
        cid = r["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank)
        meta[cid] = r
        # Ham cosine similarity skorunu koru (semantic_search "score" anahtariyla dondurur)
        semantic_scores[cid] = r.get("score", 0.0)

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    sonuc = []
    for cid, score in fused:
        m = meta[cid]
        sonuc.append({
            "id": cid,
            "rrf_score": score,
            "semantic_score": semantic_scores.get(cid, 0.0),
            "source_doc": m["source_doc"],
            "category": m["category"],
            "content": m["content"],
        })
    return sonuc


_TR_ASCII_MAP = str.maketrans("çğıöşü", "cgiosu")


def _ascii_fold(text: str) -> str:
    """Turkce karakterleri ASCII karsiliklarina cevirir (kaniyor gibi
    yazimlari yakalamak icin yedek deneme katmani)."""
    return text.translate(_TR_ASCII_MAP)


def bm25_search_with_fallback(conn, query, k=5):
    """Once normal bm25_search dener, sonuc yoksa ASCII-folded sorguyla
    tekrar dener (Turkce karakter eksikligine karsi yedek katman)."""
    sonuc = bm25_search(conn, query, k=k)
    if sonuc:
        return sonuc
    ascii_query = _ascii_fold(query)
    if ascii_query != query:
        return bm25_search(conn, ascii_query, k=k)
    return []


def has_sufficient_context(fused_results, top_semantic_score=0.0,
                           min_rrf_score=0.01, min_semantic_score=0.45):
    """Fuse edilmis sonuclarin yeterince alakali olup olmadigini kontrol eder.
    Hicbir sonuc esik degerin uzerinde degilse, sistem 'bilmiyorum' demeli.

    top_semantic_score: semantic_search'un rank-1 sonucunun ham cosine similarity
    degeri. RRF fusion'dan BAGIMSIZ bir sinyal - fused_results icinden okunmaz,
    cunku fused rank-1 chunk BM25-only olabilir (semantic_score=0.0 yanilsamasi).

    # Eşik n=20 eval setinden kalibre edildi. Q15 ('Biri hasta oldu') 
    True grubunun min skorundan (0.4758) yüksek skor alıyor (0.5346) - 
    bu MATEMATIKSEL OLARAK çözülemez bir sınır durumu (dilin doğal 
    belirsizliği). Tek eşikle asla %100 fallback doğruluğu mümkün değil.
    """
    if not fused_results:
        return False
    if fused_results[0]["rrf_score"] < min_rrf_score:
        return False
    if top_semantic_score < min_semantic_score:
        return False
    return True

