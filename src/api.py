"""
FastAPI sunum katmani.
Retrieval adimlarini (embedding + BM25 + semantic + RRF) dogrudan
icinde calistirarak top_semantic_score'u HAM semantic_sonuc'tan alir.
Bu, RRF rank-1'inin BM25-only chunk olmasi durumunda semantic_score=0.0
yanilsamasini onler (kök neden: github.com issue #tbd).
cli.py, llm.py, retrieval.py'ye hic dokunulmaz.
"""
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from db import get_connection
from foundry_session import init_foundry_full_session
from embeddings import get_embedding
from retrieval import (
    bm25_search_with_fallback,
    semantic_search,
    rrf_fuse,
    has_sufficient_context,
)
from llm import _KATEGORI_GIRIS_CUMLELERI, _VARSAYILAN_GIRIS

DOC_TITLES = {
    "01_kanama_kontrolu.md": "Kanama Kontrolü",
    "02_kirik_cikik_burkulma.md": "Kırık, Çıkık, Burkulma",
    "03_cpr_temel_yasam_destegi.md": "CPR - Temel Yaşam Desteği",
    "03b_cpr_cocuk.md": "CPR - Çocuk",
    "03c_cpr_bebek.md": "CPR - Bebek",
    "04_bogulma_heimlich.md": "Boğulma (Heimlich Manevrası)",
    "05_yanik.md": "Yanık",
    "06_sok.md": "Şok",
    "07_donma_hipotermi.md": "Donma ve Hipotermi",
    "08_deprem_oncesi_hazirlik.md": "Deprem Öncesi Hazırlık",
    "09_deprem_aninda_davranis.md": "Deprem Anında Davranış",
    "10_deprem_sonrasi_ve_yikinti_altinda.md": "Deprem Sonrası ve Yıkıntı Altında",
    "11a_fiziksel_engelli_hazirlik.md": "Fiziksel Engelli Hazırlığı",
    "11b_gorme_engelli_hazirlik.md": "Görme Engelli Hazırlığı",
    "11c_isitme_engelli_hazirlik.md": "İşitme Engelli Hazırlığı",
    "11d_dil_konusma_engelli_hazirlik.md": "Dil ve Konuşma Engelli Hazırlığı",
    "11e_zihinsel_engelli_osb_hazirlik.md": "Zihinsel Engelli / OSB Hazırlığı",
    "12_kronik_hasta_ilac_sureklilik.md": "Kronik Hasta İlaç Sürekliliği",
    "13_afet_cantasi_ozel_malzemeler.md": "Afet Çantası Özel Malzemeler",
    "14a_psikolojik_ilkyardim_sureci.md": "Psikolojik İlk Yardım Süreci",
    "14b_psikolojik_ilkyardim_yapin_yapmayin.md": "Psikolojik İlk Yardım - Yapın/Yapmayın",
    "14c_cocuklarla_afet_sonrasi_iletisim.md": "Çocuklarla Afet Sonrası İletişim",
    "15_acil_numaralar_kurumlar.md": "Acil Numaralar ve Kurumlar",
    "16_tahliye_barinma_hasar_hak.md": "Tahliye, Barınma, Hasar Hakları",
}

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "afet.db")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

_FALLBACK_MESAJ = (
    "Sorunuzu net anlayamadım. Lütfen durumu biraz daha açık belirtin - "
    "örneğin 'kanama var', 'kırık olabilir', 'nefes alamıyor', 'bilinci "
    "kapalı', 'deprem oldu ne yapmalıyım' gibi. Acil ve ciddi bir durumsa "
    "hemen 112'yi arayın."
)

# ---------------------------------------------------------------------------
# Uygulama + global model nesneleri
# ---------------------------------------------------------------------------
app = FastAPI(title="Afet İlk Yardım Asistanı API")

_client = None
_emb_model_id = None
_chat_model_id = None
query_history = []


@app.on_event("startup")
async def startup():
    global _client, _emb_model_id, _chat_model_id
    print("Foundry Local oturumu başlatılıyor…")
    _client, _emb_model_id, _chat_model_id = init_foundry_full_session()
    print("Foundry Local oturumu hazır.")


# ---------------------------------------------------------------------------
# Static dosyalar + kök sayfa
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


# ---------------------------------------------------------------------------
# /chat endpoint'i
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
async def chat(req: ChatRequest):
    if not _client:
        raise HTTPException(status_code=503, detail="Model henüz yüklenmedi.")

    question = req.question

    # Her istekte yeni bağlantı (thread-safety)
    conn = get_connection(DB_PATH)
    try:
        # --- Retrieval adımları (cli.py/answer_query ile birebir aynı sıra) ---
        query_vector = get_embedding(_client, _emb_model_id, question)
        bm25_sonuc = bm25_search_with_fallback(conn, question, k=5)
        semantic_sonuc = semantic_search(conn, query_vector, k=5)
        hibrit_sonuc = rrf_fuse(bm25_sonuc, semantic_sonuc, k=3)

        # KRİTİK: top_semantic_score'u HAM semantic_sonuc'tan al —
        # hibrit_sonuc[0] BM25-only chunk olabilir (semantic_score=0.0 yanılsaması).
        # cli.py satır 44 ile BİREBİR AYNI:
        top_semantic_score = semantic_sonuc[0]["score"] if semantic_sonuc else 0.0

    finally:
        conn.close()

    # --- has_sufficient_context ---
    yeterli = has_sufficient_context(hibrit_sonuc, top_semantic_score=top_semantic_score)

    # --- answer_intro ---
    if not yeterli:
        answer_intro = _FALLBACK_MESAJ
    else:
        ana_kategori = hibrit_sonuc[0]["category"] if hibrit_sonuc else None
        answer_intro = _KATEGORI_GIRIS_CUMLELERI.get(ana_kategori, _VARSAYILAN_GIRIS)

    # --- sources: sadece yeterli ise, orijinal sıra korunarak grupla ---
    sources = []
    if yeterli and hibrit_sonuc:
        # OrderedDict ile ilk görünme sırasını koru
        gruplar: OrderedDict[str, list] = OrderedDict()
        for chunk in hibrit_sonuc:
            doc = chunk["source_doc"]
            if doc not in gruplar:
                gruplar[doc] = []
            gruplar[doc].append(chunk["content"])

        for doc, lines in gruplar.items():
            sources.append({"doc": doc, "lines": lines})

    response_json = {
        "answer_intro": answer_intro,
        "sources": sources,
        "has_sufficient_context": yeterli,
    }

    from datetime import datetime
    query_history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "question": question,
        "has_sufficient_context": yeterli,
        "answer_intro": response_json["answer_intro"],
        "sources": response_json["sources"],
    })
    if len(query_history) > 50:
        query_history.pop(0)

    return response_json


# ---------------------------------------------------------------------------
# /history endpoint'i
# ---------------------------------------------------------------------------
@app.get("/history")
async def get_history():
    return {"history": query_history[::-1]}


# ---------------------------------------------------------------------------
# /categories endpoint'i
# ---------------------------------------------------------------------------
@app.get("/categories")
async def get_categories():
    conn = get_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT category, source_doc, COUNT(*) as chunk_count "
            "FROM chunks GROUP BY category, source_doc ORDER BY category, source_doc"
        )
        rows = cursor.fetchall()
        
        categories_dict = OrderedDict()
        category_labels = {
            "tibbi_ilk_yardim": "Tıbbi İlk Yardım",
            "deprem_davranisi": "Deprem Davranışı",
            "kirilgan_gruplar": "Kırılgan Gruplar",
            "psikolojik_destek": "Psikolojik Destek",
            "iletisim_kaynaklar": "İletişim Kaynakları",
            "idari_surecler": "İdari Süreçler"
        }
        
        for row in rows:
            cat_id = row["category"]
            doc_name = row["source_doc"]
            chunk_count = row["chunk_count"]
            
            if cat_id not in categories_dict:
                categories_dict[cat_id] = {
                    "id": cat_id,
                    "label": category_labels.get(cat_id, cat_id),
                    "documents": []
                }
            
            title = DOC_TITLES.get(doc_name, doc_name.replace(".md", "").replace("_", " ").title())
            

            categories_dict[cat_id]["documents"].append({
                "doc": doc_name,
                "title": title,
                "chunk_count": chunk_count
            })
            
        return {"categories": list(categories_dict.values())}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# /document/{doc_name} endpoint'i
# ---------------------------------------------------------------------------
import re

def split_content_and_citation(text):
    # "\n\nKaynak:" kalıbını bul ve ayır
    match = re.search(r'\n\nKaynak:.*', text, re.DOTALL)
    if match:
        clean_line = text[:match.start()].strip()
        citation = match.group(0).replace('\n\nKaynak:', '').strip()
        return clean_line, citation
    return text, None


@app.get("/document/{doc_name}")
async def get_document(doc_name: str):
    conn = get_connection(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT category, content FROM chunks WHERE source_doc = ? ORDER BY id ASC", (doc_name,))
        rows = cursor.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
            
        category = rows[0]["category"]
        lines = []
        source_citation = None
        for row in rows:
            clean_line, citation = split_content_and_citation(row["content"])
            lines.append(clean_line)
            if citation and not source_citation:
                source_citation = citation
        
        return {
            "doc": doc_name,
            "category": category,
            "lines": lines,
            "source_citation": source_citation
        }
    finally:
        conn.close()
