# Afet Anı Çevrimdışı İlk Yardım Asistanı

**Tamamen çevrimdışı çalışan, Türkçe dilinde, kaynak-doğrulanmış bir ilk yardım ve afet bilgilendirme asistanı.**

Microsoft Foundry Local üzerinde çalışan yerel bir RAG (Retrieval-Augmented Generation) sistemi. 2023 Kahramanmaraş depremi sonrası yaşanan iletişim ve internet altyapısı çöküşünden ilham alınarak; internet bağlantısı olmadan, tamamen kullanıcının bilgisayarında çalışabilen bir soru-cevap sistemi olarak tasarlanmıştır.

İki arayüzü vardır: bir **web tabanlı "Komuta Merkezi"** paneli (FastAPI + vanilla HTML/CSS/JS) ve orijinal bir **komut satırı (CLI)** aracı.

**Repo:** [github.com/dildasoftware/afet-ani-cevrimdisi-ilk-yardim](https://github.com/dildasoftware/afet-ani-cevrimdisi-ilk-yardim)

---

## İçindekiler

1. [Amaç ve Motivasyon](#amaç-ve-motivasyon)
2. [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
3. [Mimari](#mimari)
4. [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
5. [Proje Yapısı](#proje-yapısı)
6. [Kurulum](#kurulum)
7. [Kullanım — Web Arayüzü](#kullanım--web-arayüzü)
8. [Kullanım — Komut Satırı (CLI)](#kullanım--komut-satırı-cli)
9. [Tasarım Kararları ve Gerekçeleri](#tasarım-kararları-ve-gerekçeleri)
10. [Test ve Değerlendirme Sonuçları](#test-ve-değerlendirme-sonuçları)
11. [Bilinen Sınırlamalar](#bilinen-sınırlamalar)
12. [Öğrenilen Dersler](#öğrenilen-dersler)
13. [Gelecek Çalışmalar](#gelecek-çalışmalar)

---

## Amaç ve Motivasyon

Doğal afetler sırasında (özellikle depremlerde) baz istasyonlarının çökmesi, elektrik kesintileri ve internet altyapısının hasar görmesi sık karşılaşılan bir durumdur. Bu koşullarda, insanların doğru ilk yardım bilgisine anında ve güvenilir şekilde ulaşabilmesi hayati önem taşır.

Bu proje, **hiçbir internet bağlantısı gerektirmeden**, kullanıcının kendi bilgisayarında çalışan, resmi ve doğrulanmış kaynaklardan (T.C. Sağlık Bakanlığı, AFAD, İPKB/İSMEP, İçişleri Bakanlığı) beslenen bir soru-cevap sistemi sunar.

**Kritik tasarım ilkesi:** Sistem, hiçbir zaman yapay zeka modelinin "hafızasından" veya tahmininden tıbbi/acil durum bilgisi üretmez. Her cevap, önceden doğrulanmış kaynak belgelerden **birebir alıntılanır.**

---

## Öne Çıkan Özellikler

- 🩹 **6 kategori, 24 doküman, 277 bilgi parçası** — kanama, kırık/çıkık, CPR (yetişkin/çocuk/bebek ayrı), boğulma, yanık, şok, donma/hipotermi, deprem davranışı, kırılgan gruplar, psikolojik destek, iletişim kaynakları, idari süreçler
- 🔌 **%100 çevrimdışı çalışma** — Microsoft Foundry Local ile yerel LLM/embedding çalıştırma
- 🎯 **Hibrit arama** — BM25 (anahtar kelime) + Semantic Search (anlam bazlı) + Reciprocal Rank Fusion
- 🛡️ **Halüsinasyon riski sıfıra indirilmiş mimari** — LLM serbest metin üretmez, sadece kaynaktan doğrudan alıntı yapar
- 🖥️ **"Komuta Merkezi" web arayüzü** — hızlı protokol sekmeleri, canlı gecikme grafiği, kanıt/kaynak paneli
- 📖 **Protokoller sayfası** — 24 belgenin tamamı, soru sormadan, kategori kategori gezinilebilir
- 🕓 **Vaka Geçmişi** — oturum içinde sorulan tüm sorular ve cevapları tekrar görüntüleme
- 🚨 **S.O.S / Acil Durum Kartı** — retrieval'i tamamen atlayarak anında 112 bilgisi gösterir (hem web hem CLI'de `!112`)
- 🔎 **Anlık protokol arama** — hızlı sekmeleri client-side filtreleme
- ⚠️ **Güvenli reddetme mekanizması** — sistem emin olmadığında "bilmiyorum" der, uydurma cevap vermez
- 📊 **Ölçülebilir, test edilmiş performans** — 20 soruluk etiketli değerlendirme seti ile doğrulanmış, sonuçlar repoda (`eval/results.json`)

---

## Mimari

```
┌───────────────────────────────────────────────────────────────┐
│         Kullanıcı — Web Arayüzü (Komuta Merkezi)                │
│         veya Komut Satırı (CLI)                                  │
└───────────────────────────┬───────────────────────────────────┘
                             │ Soru
                             ▼
                  ┌──────────────────────┐
                  │ Acil durum modu mu?   │──── Evet ──► Anında sabit
                  │ (S.O.S / "!112")      │              acil durum metni
                  └──────────┬───────────┘              (retrieval YOK)
                             │ Hayır
                             ▼
        ┌────────────────────────────────────────┐
        │         Hibrit Retrieval Katmanı         │
        │  ┌──────────────┐    ┌────────────────┐ │
        │  │  BM25 (FTS5) │    │ Semantic Search │ │
        │  │  Anahtar     │    │ (Cosine Sim.,   │ │
        │  │  kelime      │    │  qwen3-embed.)  │ │
        │  └──────┬───────┘    └────────┬────────┘ │
        │         └──────────┬──────────┘          │
        │                    ▼                      │
        │         Reciprocal Rank Fusion (RRF)       │
        └────────────────────┬────────────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │  Yeterli bağlam var mı? │
                │  (RRF skoru + HAM       │
                │   semantic skor eşiği)  │
                └────────┬───────┬───────┘
                    Evet │       │ Hayır
                         ▼       ▼
              ┌──────────────┐ ┌──────────────────┐
              │ Kaynaktan     │ │ "Sorunuzu net      │
              │ birebir       │ │ anlayamadım..."    │
              │ alıntı +      │ │ + örnek cümleler    │
              │ sabit uyarı   │ │                     │
              └──────┬───────┘ └─────────┬──────────┘
                     └───────────┬───────┘
                                 ▼
                          Kullanıcıya Cevap
                    (JSON — web) / (metin — CLI)
```

**Veri katmanı:** SQLite veritabanı (`data/afet.db`, yerel olarak üretilir) — chunk metinleri, kategori bilgisi, kaynak dosya adı ve embedding vektörlerini tutar. FTS5 sanal tablosu BM25 aramasını destekler.

**LLM'in rolü:** Sistemdeki `phi-3.5-mini` modeli, **hiçbir karar veya içerik üretme rolü almaz.** Bu, bilinçli bir mimari karar olup gerekçesi aşağıda ayrıntılı açıklanmıştır.

**Web katmanı:** `src/api.py` (FastAPI), `cli.py`'deki retrieval mantığını tekrar kullanarak `/chat`, `/categories`, `/document/{doc}`, `/history` uç noktalarını sunar. Frontend (`static/`) saf HTML/CSS/JS'dir, hiçbir harici çerçeve veya CDN bağımlılığı yoktur — offline ilkesine sadıktır.

---

## Kullanılan Teknolojiler

| Bileşen | Teknoloji |
|---|---|
| Yerel model çalıştırma | Microsoft Foundry Local |
| Embedding modeli | `qwen3-embedding-0.6b` (1024 boyutlu vektör) |
| Sohbet modeli (mimaride hazır, aktif üretim yapmıyor) | `phi-3.5-mini` |
| Veritabanı | SQLite + FTS5 (tam metin arama) |
| Anahtar kelime arama | BM25 |
| Anlamsal arama | Cosine similarity |
| Sonuç birleştirme | Reciprocal Rank Fusion (RRF) |
| Dil işleme | Özel Türkçe normalizasyon modülü (`normalize_tr.py`) — ünsüz yumuşaması, ek kesme, ASCII katlama |
| Backend (web) | FastAPI + Uvicorn |
| Frontend (web) | Saf HTML / CSS / JavaScript (harici bağımlılık yok) |
| Programlama dili | Python |
| Arayüzler | Web (Komuta Merkezi) ve Komut Satırı (CLI) |

---

## Proje Yapısı

```
afet-ani-cevrimdisi-ilk-yardim/
├── data/
│   └── documents/               # 24 kaynak Markdown belgesi, 6 kategori
│       ├── tibbi_ilk_yardim/
│       ├── deprem_davranisi/
│       ├── kirilgan_gruplar/
│       ├── psikolojik_destek/
│       ├── iletisim_kaynaklar/
│       └── idari_surecler/
│       # data/afet.db kurulum sırasında yerel olarak üretilir (repoda değil)
├── src/
│   ├── ingest.py                # Belge okuma, chunk'lama, DB'ye yazma
│   ├── embed_chunks.py          # Chunk'lar için embedding üretimi
│   ├── chunking.py              # Adım-bazlı chunk'lama stratejisi
│   ├── normalize_tr.py          # Türkçe metin normalizasyonu
│   ├── db.py                    # SQLite bağlantı ve şema yönetimi
│   ├── embeddings.py            # Foundry Local embedding oturumu
│   ├── foundry_session.py       # Foundry Local birleşik oturum yönetimi
│   ├── retrieval.py             # BM25 + semantic + RRF + eşik kontrolü
│   ├── llm.py                   # Cevap üretimi (kaynak alıntı + sabit metinler)
│   ├── cli.py                   # Komut satırı arayüzü
│   └── api.py                   # FastAPI backend (web arayüzü için)
├── static/
│   ├── index.html                # Web arayüzü — "Komuta Merkezi"
│   ├── style.css
│   └── app.js
├── eval/
│   ├── questions.json            # 20 soruluk etiketli değerlendirme seti
│   ├── run_eval.py               # Değerlendirme betiği
│   └── results.json              # Değerlendirme sonuçları (repoda, kanıt olarak saklanır)
├── docs/
│   └── gecmis_analizler/         # Geliştirme sürecindeki bağımsız teşhis scriptleri (üretim kodu değil)
├── tests/
│   └── test_normalize_tr.py
├── PROJECT_LOG.md                # Geliştirme günlüğü, alınan kararlar
└── README.md
```

---

## Kurulum

### Ön Koşullar

- Python 3.10 veya üzeri
- [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/) kurulu olmalı
- Windows, macOS veya Linux

### Adımlar

```bash
# 1. Depoyu klonlayın
git clone https://github.com/dildasoftware/afet-ani-cevrimdisi-ilk-yardim.git
cd afet-ani-cevrimdisi-ilk-yardim

# 2. Sanal ortam oluşturun (önerilir)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Foundry Local SDK'nın kurulu ve çalışır durumda olduğunu doğrulayın
python -c "from foundry_local_sdk import FoundryLocalManager; print('Foundry Local hazır')"

# 5. Belgeleri işleyip veritabanını oluşturun (ilk kurulumda bir kez)
python src/ingest.py
python src/embed_chunks.py
```

> **Not:** İlk çalıştırmada Foundry Local, gerekli modelleri (`qwen3-embedding-0.6b`, `phi-3.5-mini`) internet üzerinden indirir. Bu tek seferlik bir işlemdir — sonraki tüm kullanımlar tamamen çevrimdışı gerçekleşir.

---

## Kullanım — Web Arayüzü

```bash
python -m uvicorn src.api:app --port 8000
```

Sunucu hazır olduğunda (`Application startup complete`) tarayıcıdan `http://localhost:8000` adresini açın.

**Arayüz bölümleri:**

| Bölüm | Açıklama |
|---|---|
| **Komuta Merkezi** | Ana ekran — hızlı protokol sekmeleri (K1-K6, D1) ve komut girişi |
| **Protokoller** | 24 belgenin tamamını, kategori kategori, soru sormadan gezinme |
| **Bölge Haritası** | AFAD'ın resmi toplanma alanı sorgulama servisine dürüst yönlendirme |
| **Vaka Geçmişi** | Bu oturumda sorulan tüm soruların ve cevapların listesi (bellek-içi, sunucu yeniden başlatılınca sıfırlanır) |
| **S.O.S butonu** | Retrieval'i atlayarak anında acil durum kartı ve 112 arama şablonu gösterir |
| **Arama kutusu** | Hızlı protokol sekmelerini anlık filtreler (`Ctrl+K` ile odaklanma) |

---

## Kullanım — Komut Satırı (CLI)

```bash
python src/cli.py
```

```
$ python src/cli.py
Foundry Local oturumu başlatılıyor, modeller yükleniyor...

Soru: Kanama nasıl durdurulur?

Bu durumda asagidaki ilk yardim adimlarini izleyin:

--- Kaynak (birebir alinti): 01_kanama_kontrolu.md ---
  6. Kanayan yer üzerine temiz bir bezle bastırın.
  7. Kanama durmazsa, ilk bezi kaldırmadan üzerine ikinci bir bez koyup basıncı artırın.

========================================
Bu bilgi tibbi tavsiye yerine gecmez.
Ciddi bir durumda 112'yi arayin.
========================================
🚨 ACİL DURUM NUMARASI: 112
========================================
```

| Komut | Açıklama |
|---|---|
| `!112` | Retrieval/embedding'i tamamen atlayarak **anında** acil durum bilgisi gösterir |
| `çıkış` / `exit` | Programdan çıkar |

Sistem, sorulan sorunun kapsamı dışında olduğunu veya belirsiz olduğunu tespit ettiğinde, **uydurma bir cevap vermek yerine** kullanıcıyı daha açık bir soru sormaya yönlendirir ve her durumda 112'yi hatırlatır.

---

## Tasarım Kararları ve Gerekçeleri

### 1. LLM Neden Serbest Metin Üretmiyor?

`phi-3.5-mini` modeline üç farklı prompt stratejisiyle kısa bir giriş cümlesi ürettirmek denendi. **Üçü de tutarlı şekilde anlamsız/bozuk Türkçe üretti.** Ayrıca modelin **kapalı-küme sınıflandırma** (8 kategoriden birini seçme) görevinde de 8 sorudan **0'ında doğru** kategori seçildiği görüldü.

**Sonuç:** Bu ölçekteki (3.8B parametre) modelin hiçbir serbest karar/üretim görevinde güvenilmez olduğu kanıtlandı. Sistem, LLM'e **hiçbir zaman** karar verme veya metin üretme yetkisi vermez — sadece önceden doğrulanmış kaynak metinleri birebir sunar.

### 2. Neden Hibrit Arama (BM25 + Semantic)?

Sadece anahtar kelime araması eş anlamlı ifadeleri yakalayamaz. Sadece semantic arama ise küçük embedding modelinin sınırlı ayrım gücü nedeniyle yetersiz kalabilir. Reciprocal Rank Fusion, her iki yöntemin zayıflığını dengeler.

### 3. Neden Yaş Gruplarına Göre Ayrı CPR Belgeleri?

Yetişkin, çocuk ve bebek CPR teknikleri önemli ölçüde farklılık gösterir. Üç ayrı belge oluşturularak retrieval'ın yanlış yaş grubu bilgisini getirme riski yapısal olarak azaltıldı.

### 4. Eşik Kalibrasyonu Nasıl Yapıldı?

Sistemin "yeterli bilgi var mı" kararı, retrieval sonuçlarının ham semantic similarity skoruna dayanır. Bu eşik (`0.45`), 20 soruluk değerlendirme setindeki gerçek skor dağılımı analiz edilerek belirlenmiştir.

### 5. Web Arayüzü Neden "Komuta Merkezi" Tarzında Tasarlandı?

Frontend, jenerik "AI chat uygulaması" klişelerinden (koyu tema + neon mor/mavi vurgu, ya da krem + serif + turuncu) bilinçli olarak kaçınacak şekilde tasarlandı. Kimlik: AFAD kurumsal lacivert + Kızılay kırmızısı (sadece acil durum sinyali için), Georgia serif başlıklar + monospace veri etiketleri. Referans noktası, jenerik bir chatbot değil, gerçek bir komuta merkezi/enstrüman paneli estetiğidir.

### 6. Web ve CLI Arasındaki Kod Tekrarı Neden Kabul Edildi?

`api.py`, retrieval adımlarını `cli.py`'nin `answer_query()` fonksiyonunu çağırmak yerine kendi içinde tekrar eder. Bu bilinçli bir tercihtir: iki dosyayı birbirinden bağımsız tutup, birinde yapılan bir değişikliğin diğerini sessizce bozmasını önler (bkz. Öğrenilen Dersler, madde 3).

---

## Test ve Değerlendirme Sonuçları

Sistem, 20 soruluk etiketli bir değerlendirme seti (`eval/questions.json`) üzerinde test edilmiştir. Ham sonuçlar `eval/results.json` içinde repoda saklanmaktadır.

### Genel Sonuçlar (Bilgi Soruları, N=12)

| Metrik | Değer |
|---|---|
| Precision@3 | 0.5556 |
| Precision@5 | 0.4833 |
| Recall@3 | 0.4167 |
| Recall@5 | 0.4792 |
| MRR | 0.6528 |
| Category Purity@3 | 0.9722 |
| Category Purity@5 | 0.9167 |

### Güvenli Reddetme Doğruluğu (Belirsiz + Kapsam Dışı, N=8)

| Metrik | Değer |
|---|---|
| **Fallback Doğruluğu** | **%87,5 (7/8)** |

Kalan 1 durum, matematiksel olarak tek bir eşikle çözülemeyen bilinen bir sınır durumudur (bkz. Bilinen Sınırlamalar).

### Değerlendirme Sürecinin İyileşme Geçmişi

| Aşama | Precision@3 | Fallback Doğruluğu |
|---|---|---|
| İlk ölçüm | 0.4722 | %0 |
| Eşik mekanizması düzeltmesi sonrası | 0.4722 | %50 |
| Bağlamsal embedding sonrası | 0.5556 | %62,5 |
| Fusion-skor hatası düzeltmesi sonrası (CLI) | 0.5556 | %87,5 |
| Aynı hata sınıfının API katmanında bulunup düzeltilmesi sonrası | 0.5556 | **%87,5 (korunuyor)** |

### Regresyon Testi Kapsamı

Web arayüzü eklendikten sonra, 6 hızlı protokol sekmesinin (K1-K6) ve deprem sekmesinin (D1) tamamı ayrı ayrı test edilmiş, 7/7'si doğru kategori ve `has_sufficient_context=true` döndürmüştür.

---

## Bilinen Sınırlamalar

1. **Matematiksel olarak çözülemez sınır durumu:** Bazı belirsiz ifadeler, doğru kategori sorularının minimum semantic skorundan daha yüksek skor alabilir. Tek bir eşik değeri bunu tam çözemez — dilin doğal belirsizliğinden kaynaklanan bir sınırdır.

2. **Reranker (cross-encoder) modeli mevcut değil:** Foundry Local'in model kataloğunda reranking modeli bulunmamaktadır.

3. **Embedding modelinin yazım/noktalama duyarlılığı:** Küçük ölçekli embedding modeli, aynı anlama gelen ama farklı yazılmış ifadelere farklı skorlar verebilir.

4. **Yazım hatası toleransı kapsam dışı bırakılmıştır:** Genel yazım hatası düzeltmesi, öngörülemeyen yan etki riski nedeniyle bilinçli olarak kapsam dışı bırakılmıştır. Türkçe karakter eksikliği ayrıca ele alınmış ve çözülmüştür.

5. **Değerlendirme seti küçük ölçeklidir (n=20):** Daha geniş bir veri setiyle doğrulanması, sonuçların genellenebilirliğini artıracaktır.

6. **LLM hiçbir karar/üretim rolü almaz:** Hallucination riskini ortadan kaldırmak için bilinçli bir tercihtir, ancak doğal bir sohbet deneyimini (örn. geri soru sorma) engeller.

7. **Bazı belgelerde gömülü alt-başlıklar tam ayrıştırılmamıştır:** Örneğin `06_sok.md`'de "Şok belirtileri:" ile başlayan bir blok, ilgili maddenin içinde kalabalık görünebilir. Sistematik "Kaynak:" atıf bloğu (24 belgenin tamamında) ayrıştırılıp temizlenmiştir; bu istisna kozmetik önceliklidir, düzeltilmesi planlanmaktadır.

8. **Vaka Geçmişi kalıcı değildir:** Bilinçli bir tasarım kararıyla, sorgu geçmişi sunucu belleğinde tutulur; sunucu yeniden başlatıldığında sıfırlanır (tek-kullanıcılı, yerel bir araç için kabul edilebilir bir basitleştirme).

---

## Öğrenilen Dersler

1. **RRF skoru, "güven eşiği" için doğrudan kullanılamaz.** Reciprocal Rank Fusion skoru sıralama amaçlı tasarlanmıştır, mutlak bir alaka düzeyi ölçüsü değildir. Doğru güven kararı için ham semantic similarity skoruna ayrıca bakılması gerekmiştir. Bu hata, hem CLI'de hem daha sonra bağımsız olarak API katmanında (farklı bir kod yolunda) iki kez ortaya çıkmıştır — aynı prensibin birden fazla yerde titizlikle uygulanması gerektiğinin kanıtıdır.

2. **Embedding ve BM25 katmanları arasında tutarlılık kritiktir.** Bu asimetri fark edilip düzeltildiğinde (bağlamsal embedding), Precision@3 %18 artış gösterdi.

3. **Değerlendirme (eval) betiğinin doğru çalışması, üretim kodunun doğru çalıştığı anlamına gelmez.** Retrieval eşiği düzeltmesi `eval/run_eval.py`'ye uygulanmış ama `cli.py`'ye uygulanmamış olması nedeniyle, gerçek kullanıcı arayüzü sessizce her soruyu reddediyordu. Bu, uçtan uca doğrulamanın önemini gösteren kritik bir bulgudur.

4. **Küçük dil modellerinin sınırları erken test edilmelidir.** Modelin serbest üretim ve kapalı-küme sınıflandırma görevlerinde ayrı ayrı test edilmesi, mimari kararların sağlam bir temele oturmasını sağlamıştır.

5. **Bir eşik değeri her zaman mükemmel olamaz.** Dilin doğal belirsizliği nedeniyle, tek bir sayısal eşikle %100 doğruluk elde etmek matematiksel olarak mümkün olmayabilir.

6. **Az sayıda, sabit veri için algoritmik üretim yerine elle doğrulanmış sabit veri daha güvenilirdir.** 24 belgenin başlıklarını otomatik bir string-temizleme algoritmasıyla üretmek Türkçe karakterleri (ı, ş, ğ, ö, ü, ç) bozdu; elle yazılmış sabit bir sözlükle değiştirilmesi hem daha basit hem daha doğru oldu.

---

## Gelecek Çalışmalar

- Daha büyük bir embedding modelinin (`qwen3-embedding-8b`) donanım maliyeti/performans dengesinin ölçülmesi
- Değerlendirme setinin 20'den 40-50 soruya genişletilmesi
- Bölge Haritası'nın, AFAD'ın açık toplanma alanı verisiyle gerçek bir offline arama özelliğine dönüştürülmesi
- Yazdırılabilir, çevrimdışı bir "acil durum özet kartı" özelliğinin eklenmesi
- Reranking modelleri Foundry Local kataloğuna eklendiğinde, retrieval kalitesinin bu teknikle iyileştirilmesi
- `06_sok.md` benzeri gömülü alt-başlık bloklarının genel bir çözümle ayrıştırılması

---

## Kaynaklar

- T.C. Sağlık Bakanlığı, İlk Yardım Yönetmeliği (2011)
- AFAD (Afet ve Acil Durum Yönetimi Başkanlığı)
- İPKB/İSMEP (İstanbul Proje Koordinasyon Birimi / İstanbul Sismik Riskin Azaltılması ve Acil Durum Hazırlık Projesi)
- T.C. İçişleri Bakanlığı
- 112.gov.tr

---

*Bu proje, Microsoft Foundry Local kullanılarak çevrimdışı RAG uygulamaları geliştirme konulu bir staj programı kapsamında geliştirilmiştir.*
