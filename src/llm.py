"""
Guvenlik odakli cevap uretme. Sadece retrieval'dan gelen baglami kullanir,
yeterli baglam yoksa tahmin etmeden 112'ye yonlendirir.
"""

SYSTEM_PROMPT = """Sen Turkiye'de afet ve ilk yardim konusunda bilgi veren bir asistansin.

Sana bir BAGLAM ve bir SORU verilecek. Su kurallara KESINLIKLE uy:

1. Cevabini SADECE BAGLAM icindeki bilgiye dayandir. Baglamda olmayan hicbir bilgiyi ekleme, tahmin etme, uydurma.
2. Baglam soruyu cevaplamaya yetersizse, SADECE su cumleyi yaz: "Bu konuda elimdeki kaynaklarda yeterli bilgi yok. Lutfen 112'yi arayarak profesyonel yardim isteyin."
3. Baglam yeterliyse: BAGLAM'daki ilgili adimlari kisa, acik Turkce ile, numarali liste halinde tekrar yaz. Baska hicbir sey ekleme veya yorumlama.
4. Cevabinin EN SONUNA, ayri bir satirda, TAM OLARAK su iki cumleyi ekle: "Bu bilgi tibbi tavsiye yerine gecmez. Ciddi bir durumda 112'yi arayin."
5. Baglam idari_surecler kategorisindense, bu iki cumlenin altina AYRICA ekle: "Bu bilgi guncel olmayabilir, kesin bilgi icin AFAD'dan teyit edin."

Baska hicbir aciklama, yorum veya ek bilgi ekleme.
"""


def build_context_text(chunks):
    parts = []
    for c in chunks:
        parts.append(f"[Kaynak kategori: {c['category']} | Belge: {c['source_doc']}]\n{c['content']}")
    return "\n\n".join(parts)


_KATEGORI_GIRIS_CUMLELERI = {
    "tibbi_ilk_yardim": "Bu durumda asagidaki ilk yardim adimlarini izleyin:",
    "deprem_davranisi": "Bu durumda asagidaki davranis kurallarini izleyin:",
    "kirilgan_gruplar": "Bu durumda asagidaki hazirlik onerilerini izleyin:",
    "psikolojik_destek": "Bu durumda asagidaki yaklasimi izleyin:",
    "iletisim_kaynaklar": "Asagidaki iletisim bilgilerini kullanabilirsiniz:",
    "idari_surecler": "Asagidaki surec bilgilerini inceleyebilirsiniz:",
}
_VARSAYILAN_GIRIS = "Bu durumda asagidaki adimlari izleyin:"


_ACIL_DURUM_KARTI = (
    "\n"
    "========================================\n"
    "\U0001f6a8 ACİL DURUM NUMARASI: 112\n"
    "========================================\n"
)


def generate_answer(client, model_id, query, chunks, sufficient, min_display_score=0.015):
    if not sufficient:
        cevap = (
            "Sorunuzu net anlayamadım. Lütfen durumu biraz daha açık belirtin - "
            "örneğin 'kanama var', 'kırık olabilir', 'nefes alamıyor', 'bilinci "
            "kapalı', 'deprem oldu ne yapmalıyım' gibi. Acil ve ciddi bir durumsa "
            "hemen 112'yi arayın."
        )
        return cevap + _ACIL_DURUM_KARTI

    from collections import OrderedDict
    gosterilecekler = [c for c in chunks if c.get("rrf_score", 1.0) >= min_display_score] or chunks[:1]

    gruplar = OrderedDict()
    kategoriler = set()
    for c in gosterilecekler:
        gruplar.setdefault(c["source_doc"], []).append(c["content"])
        kategoriler.add(c["category"])

    ana_kategori = gosterilecekler[0]["category"] if gosterilecekler else None
    intro_cumle = _KATEGORI_GIRIS_CUMLELERI.get(ana_kategori, _VARSAYILAN_GIRIS)

    satirlar = [intro_cumle, ""]
    for kaynak, icerikler in gruplar.items():
        satirlar.append(f"--- Kaynak (birebir alinti): {kaynak} ---")
        for icerik in icerikler:
            satirlar.append(f"  {icerik}")
        satirlar.append("")

    cevap = "\n".join(satirlar).strip()
    cevap += "\n\n" + "=" * 40
    cevap += "\nBu bilgi tibbi tavsiye yerine gecmez."
    cevap += "\nCiddi bir durumda 112'yi arayin."
    if "idari_surecler" in kategoriler:
        cevap += "\nBu bilgi guncel olmayabilir, kesin bilgi icin AFAD'dan teyit edin."
    cevap += _ACIL_DURUM_KARTI
    return cevap
