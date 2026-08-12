# Afet Anı Offline İlk Yardım Asistanı

**Tamamen çevrimdışı çalışan, Türkçe dilinde, kaynak-doğrulanmış bir ilk yardım ve afet bilgilendirme asistanı.**

Bu proje, Microsoft Foundry Local üzerinde çalışan yerel bir RAG (Retrieval-Augmented Generation) sistemidir. 2023 Kahramanmaraş depremi sonrası yaşanan iletişim ve internet altyapısı çöküşünden ilham alınarak; internet bağlantısı olmadan, tamamen kullanıcının bilgisayarında çalışabilen bir soru-cevap sistemi olarak tasarlanmıştır.

---

## İçindekiler

1. [Amaç ve Motivasyon](#amaç-ve-motivasyon)
2. [Öne Çıkan Özellikler](#öne-çıkan-özellikler)
3. [Mimari](#mimari)
4. [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
5. [Proje Yapısı](#proje-yapısı)
6. [Kurulum](#kurulum)
7. [Kullanım](#kullanım)
8. [Tasarım Kararları ve Gerekçeleri](#tasarım-kararları-ve-gerekçeleri)
9. [Test ve Değerlendirme Sonuçları](#test-ve-değerlendirme-sonuçları)
10. [Bilinen Sınırlamalar](#bilinen-sınırlamalar)
11. [Öğrenilen Dersler](#öğrenilen-dersler)
12. [Gelecek Çalışmalar](#gelecek-çalışmalar)

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
- 🚨 **Acil Durum Modu (`!112`)** — retrieval/embedding'i tamamen atlayarak anında 112 bilgisi gösterir
- ⚠️ **Güvenli reddetme mekanizması** — sistem emin olmadığında "bilmiyorum" der, uydurma cevap vermez
- 📊 **Ölçülebilir, test edilmiş performans** — 20 soruluk etiketli değerlendirme seti ile doğrulanmış

---

## Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                      Kullanıcı (CLI)                          │
└───────────────────────────┬─────────────────────────────────┘
                             │ Soru
                             ▼
                  ┌──────────────────────┐
                  │   "!112" mi?          │──── Evet ──► Anında sabit
                  └──────────┬───────────┘              acil durum metni
                             │ Hayır                     (retrieval YOK)
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
                │  (RRF skoru + ham       │
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
                    🚨 Acil Durum Kartı (112)
                                 │
                                 ▼
                          Kullanıcıya Cevap
```

**Veri katmanı:** SQLite veritabanı (`data/afet.db`) — chunk metinleri, kategori bilgisi, kaynak dosya adı ve embedding vektörlerini tutar. FTS5 sanal tablosu BM25 aramasını destekler.

**LLM'in rolü:** Sistemdeki `phi-3.5-mini` modeli, **hiçbir karar veya içerik üretme rolü almaz.** Bu, bilinçli bir mimari karar olup gerekçesi aşağıda ayrıntılı açıklanmıştır.

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
| Programlama dili | Python |
| Arayüz | Komut satırı (CLI) |

---

## Proje Yapısı

```
afet-ilk-yardim-asistani/
├── data/
│   ├── documents/              # 24 kaynak Markdown belgesi, 6 kategori
│   │   ├── tibbi_ilk_yardim/
│   │   ├── deprem_davranisi/
│   │   ├── kirilgan_gruplar/
│   │   ├── psikolojik_destek/
│   │   ├── iletisim_kaynaklar/
│   │   └── idari_surecler/
│   └── afet.db                 # SQLite veritabanı (chunk + embedding)
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
│   └── cli.py                   # Komut satırı arayüzü
├── eval/
│   ├── questions.json           # 20 soruluk etiketli değerlendirme seti
│   ├── run_eval.py              # Değerlendirme betiği
│   └── results.json             # Değerlendirme sonuçları (çalıştırma zamanında oluşur)
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
# 1. Depoyu klonlayın / proje klasörüne gidin
cd afet-ilk-yardim-asistani

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

# 6. Uygulamayı başlatın
python src/cli.py
```

> **Not:** İlk çalıştırmada Foundry Local, gerekli modelleri (`qwen3-embedding-0.6b`, `phi-3.5-mini`) internet üzerinden indirir. Bu tek seferlik bir işlemdir — sonraki tüm kullanımlar tamamen çevrimdışı gerçekleşir.

---

## Kullanım

Uygulama başlatıldıktan sonra, doğal dilde Türkçe sorular sorabilirsiniz:

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

### Özel Komutlar

| Komut | Açıklama |
|---|---|
| `!112` | Retrieval/embedding'i tamamen atlayarak **anında** acil durum bilgisi ve 112 arama şablonu gösterir. Panik anlarında en hızlı yanıt yolu. |
| `çıkış` / `exit` | Programdan çıkar |

Sistem, sorulan sorunun kapsamı dışında olduğunu (örn. "Türkiye'nin başkenti neresi?") veya belirsiz olduğunu (örn. "Yardım lazım") tespit ettiğinde, **uydurma bir cevap vermek yerine** kullanıcıyı daha açık bir soru sormaya yönlendirir ve her durumda 112'yi hatırlatır.

---

## Tasarım Kararları ve Gerekçeleri

### 1. LLM Neden Serbest Metin Üretmiyor?

Geliştirme sürecinde, `phi-3.5-mini` modeline üç farklı prompt stratejisiyle (varsayılan, kısıtlı, düşük-temperature) kısa bir giriş cümlesi ürettirmek denendi. **Üçü de tutarlı şekilde anlamsız/bozuk Türkçe üretti.** Bu, hallucination riskini kabul edilemez kılan bir bulguydu.

Ayrıca, modelin **kapalı-küme sınıflandırma** (önceden tanımlı 8 kategoriden birini seçme) görevinde de test edildi: 8 sorudan **0'ında doğru** kategori seçildi, hatta bir soruda talimat tamamen göz ardı edilip alakasız bir cevap üretildi.

**Sonuç:** Bu ölçekteki (3.8B parametre) modelin hiçbir serbest karar/üretim görevinde güvenilmez olduğu kanıtlandı. Bu nedenle sistem, LLM'e **hiçbir zaman** karar verme veya metin üretme yetkisi vermez — sadece önceden doğrulanmış kaynak metinleri birebir sunar.

### 2. Neden Hibrit Arama (BM25 + Semantic)?

Sadece anahtar kelime araması (BM25) eş anlamlı ifadeleri yakalayamaz ("kanama" ile "kan geliyor" arasındaki ilişki gibi). Sadece semantic arama ise küçük embedding modelinin (0.6B parametre) sınırlı ayrım gücü nedeniyle bazı durumlarda yetersiz kalabilir. İkisinin **Reciprocal Rank Fusion** ile birleştirilmesi, her iki yöntemin zayıflığını dengeler.

### 3. Neden Yaş Gruplarına Göre Ayrı CPR Belgeleri?

Yetişkin, çocuk ve bebek CPR teknikleri önemli ölçüde farklılık gösterir. Tek bir belgede dipnot/varyasyon şeklinde tutmak, retrieval sisteminin yanlış yaş grubuna ait bilgiyi getirme riskini artırır. Bu nedenle üç ayrı belge (`03_cpr_temel_yasam_destegi.md`, `03b_cpr_cocuk.md`, `03c_cpr_bebek.md`) oluşturularak retrieval riski yapısal olarak azaltıldı.

### 4. Eşik Kalibrasyonu Nasıl Yapıldı?

Sistemin "yeterli bilgi var mı, yok mu" kararı, retrieval sonuçlarının ham semantic similarity skoruna dayanır. Bu eşik (`0.45`), 20 soruluk değerlendirme setindeki gerçek skor dağılımı analiz edilerek, doğru cevapların minimum skoru ile yanlış/kapsam-dışı soruların maksimum skoru arasındaki aralıktan seçilmiştir.

---

## Test ve Değerlendirme Sonuçları

Sistem, 20 soruluk etiketli bir değerlendirme seti (`eval/questions.json`) üzerinde test edilmiştir. Sorular dört kategoriye ayrılır: **normal** (8), **yaşa özel** (4), **belirsiz** (4), **kapsam dışı** (4).

### Genel Sonuçlar (Bilgi Soruları, N=12)

| Metrik | Değer | Açıklama |
|---|---|---|
| Precision@3 | 0.5556 | Getirilen 3 sonuçtan ortalama %55,6'sı doğru |
| Precision@5 | 0.4833 | Getirilen 5 sonuçtan ortalama %48,3'ü doğru |
| Recall@3 | 0.4167 | Beklenen bilginin %41,7'si ilk 3 sonuçta yakalanıyor |
| MRR | 0.6528 | Doğru sonuç ortalama olarak üst sıralarda çıkıyor |
| Category Purity@3 | 0.9722 | Getirilen sonuçların %97,2'si doğru kategoriden |
| Category Purity@5 | 0.9167 | Getirilen sonuçların %91,7'si doğru kategoriden |

### Güvenli Reddetme Doğruluğu (Belirsiz + Kapsam Dışı, N=8)

| Metrik | Değer |
|---|---|
| **Fallback Doğruluğu** | **%87,5 (7/8)** |

Sistem, kapsam dışı veya belirsiz sorularda 8 sorudan 7'sinde doğru şekilde "bilmiyorum" cevabını vermiştir. Kalan 1 durum (bkz. Bilinen Sınırlamalar) matematiksel olarak tek bir eşikle çözülemeyen bir sınır durumudur.

### Değerlendirme Sürecinin İyileşme Geçmişi

| Aşama | Precision@3 | Fallback Doğruluğu |
|---|---|---|
| İlk ölçüm | 0.4722 | %0 |
| Eşik mekanizması düzeltmesi sonrası | 0.4722 | %50 |
| Bağlamsal embedding sonrası | 0.5556 | %62,5 |
| Fusion-skor hatası düzeltmesi sonrası | 0.5556 | **%87,5** |

---

## Bilinen Sınırlamalar

Bu proje, aşağıdaki sınırlamaları bilinçli olarak kabul etmiştir. Bunlar birer eksiklik değil, gerekçelendirilmiş mühendislik kararlarıdır:

1. **Matematiksel olarak çözülemez sınır durumu (Q15):** "Biri hasta oldu" gibi bazı belirsiz ifadeler, doğru kategori sorularının minimum semantic skorundan (0.4758) daha yüksek skor alabilir (0.5346). Bu durumda, hiçbir tek eşik değeri hem bu soruyu doğru reddedip hem de gerçek soruları kabul edemez — bu, dilin doğal belirsizliğinden kaynaklanan, tek eşikli bir sistemle aşılamayan bir sınırdır.

2. **Reranker (cross-encoder) modeli mevcut değil:** Foundry Local'in model kataloğu (47 model) incelenmiş, hiçbir reranking/cross-encoder modeli bulunmamıştır. Bu, retrieval kalitesinin iyileştirilmesi için endüstri standardı bir tekniğin, platform kısıtı nedeniyle kullanılamadığı anlamına gelir.

3. **Embedding modelinin yazım/noktalama duyarlılığı:** Küçük ölçekli embedding modeli (`qwen3-embedding-0.6b`), aynı anlama gelen ama farklı yazılmış ifadelere (örn. büyük/küçük harf, noktalama) farklı skorlar verebilir. Bu, modelin ölçeğinden kaynaklanan bilinen bir sınırlamadır.

4. **Yazım hatası toleransı kapsam dışı bırakılmıştır:** Genel yazım hatası düzeltmesi (harf eksik/fazla/yer değişmiş kelimeler), öngörülemeyen yan etki riski nedeniyle (örn. kelime köklerinin yanlış kelimelere çökmesi) bilinçli olarak kapsam dışı bırakılmıştır. Türkçe karakter eksikliği (ı/i, ş/s gibi) ayrı ele alınmış ve çözülmüştür.

5. **Değerlendirme seti küçük ölçeklidir (n=20):** Eşik kalibrasyonu bu küçük örneklemden yapılmıştır; daha geniş bir veri setiyle doğrulanması, sonuçların genellenebilirliğini artıracaktır.

6. **LLM hiçbir karar/üretim rolü almaz:** Bu, hallucination riskini ortadan kaldırmak için bilinçli bir tercihtir, ancak sistemin doğal bir sohbet deneyimi sunmasını (örn. "ne hastası?" diye geri soru sorma) engeller.

---

## Öğrenilen Dersler

1. **RRF skoru, "güven eşiği" için doğrudan kullanılamaz.** Reciprocal Rank Fusion skoru (`1/(60+rank)`) sıralama amaçlı tasarlanmıştır, mutlak bir alaka düzeyi ölçüsü değildir. İlk sıradaki herhangi bir sonuç, alakasız olsa bile benzer bir skor alır. Doğru güven kararı için ham semantic similarity skoruna ayrıca bakılması gerekmiştir.

2. **Embedding ve BM25 katmanları arasında tutarlılık kritiktir.** BM25 katmanı, arama sorgusunu başlık bilgisiyle zenginleştirilmiş şekilde işlerken, embedding katmanı bunu yapmıyordu. Bu asimetri fark edilip düzeltildiğinde (bağlamsal embedding), Precision@3 %18 artış gösterdi.

3. **Değerlendirme (eval) betiğinin doğru çalışması, üretim kodunun (CLI) doğru çalıştığı anlamına gelmez.** Geliştirme sürecinde, retrieval eşiği düzeltmesi `eval/run_eval.py`'ye doğru şekilde uygulanmış ama `cli.py`'ye uygulanmamış olması nedeniyle, gerçek kullanıcı arayüzü sessizce her soruyu reddediyordu — eval sonuçları bu hatayı hiç yansıtmıyordu. Bu, uçtan uca (end-to-end) doğrulamanın önemini gösteren kritik bir bulgudur.

4. **Küçük dil modellerinin (3-4B parametre) sınırları erken test edilmelidir.** Modelin serbest üretim ve kapalı-küme sınıflandırma görevlerinde ayrı ayrı test edilmesi, mimari kararların (LLM'in karar rolü almaması) sağlam bir temele oturmasını sağlamıştır.

5. **Bir eşik değeri her zaman mükemmel olamaz.** Dilin doğal belirsizliği nedeniyle, tek bir sayısal eşikle %100 doğruluk elde etmek matematiksel olarak mümkün olmayabilir. Bunu kabul etmek ve belgelemek, "sorunu çözülmemiş" bırakmaktan farklı, bilinçli bir mühendislik kararıdır.

---

## Gelecek Çalışmalar

- Daha büyük bir embedding modelinin (örn. `qwen3-embedding-8b`) donanım maliyeti/performans dengesinin ölçülmesi
- Değerlendirme setinin 20'den 40-50 soruya genişletilmesi, eşik kalibrasyonunun daha geniş veriyle doğrulanması
- Yazdırılabilir, çevrimdışı bir "acil durum özet kartı" özelliğinin eklenmesi
- Reranking modelleri Foundry Local kataloğuna eklendiğinde, retrieval kalitesinin bu teknikle iyileştirilmesi

---

## Kaynaklar

- T.C. Sağlık Bakanlığı, İlk Yardım Yönetmeliği (2011)
- AFAD (Afet ve Acil Durum Yönetimi Başkanlığı)
- İPKB/İSMEP (İstanbul Proje Koordinasyon Birimi / İstanbul Sismik Riskin Azaltılması ve Acil Durum Hazırlık Projesi)
- T.C. İçişleri Bakanlığı
- 112.gov.tr

---

*Bu proje, Microsoft Foundry Local kullanılarak çevrimdışı RAG uygulamaları geliştirme konulu bir staj programı kapsamında geliştirilmiştir.*