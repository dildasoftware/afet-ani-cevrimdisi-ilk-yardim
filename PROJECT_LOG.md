# Proje Geliştirme Günlüğü

## Afet İlk Yardım Asistanı

Bu dosya, projenin geliştirme sürecini ve alınan kararları takip eder.

## Oturum: Web Arayüzü + API Entegrasyonu (12 Ağustos)

### Tamamlanan İşler
- FastAPI backend (src/api.py) oluşturuldu, /chat, /categories, /document/{doc}, /history endpoint'leri eklendi
- Tam web arayüzü (static/index.html, style.css, app.js) - "Komuta Merkezi" tasarımı, AFAD lacivert + Kızılay kırmızı kimlik
- Protokoller sayfası: 24 belge, 6 kategori, gezinilebilir
- Vaka Geçmişi: bellek-içi (in-memory) sorgu geçmişi, kart görünümü
- Bölge Bilgisi: dürüst yönlendirme sayfası (AFAD resmi linkine)
- Arama kutusu: hızlı sekmeleri client-side filtreleme

### Bulunan ve Düzeltilen Kritik Hatalar
1. cli.py'deki top_semantic_score bug'ı (önceki oturumdan, hatırlatma)
2. api.py'de AYNI kalıptaki 2. bir sessiz eşik hatası: has_sufficient_context, hibrit_sonuc[0]["semantic_score"] kullanıyordu (RRF fusion sonrası sıfırlanmış), ham semantic_sonuc[0]["score"]'a düzeltildi
3. Belge içeriğinde gömülü "Kaynak:" atıfları (24 belgenin TAMAMINDA, son chunk'ta) ayrıştırılıp ayrı bir source_citation alanına taşındı
4. Türkçe başlık üretimi bug'ı: /categories endpoint'i başlangıçta otomatik bir string-temizleme algoritmasıyla belge başlıkları üretiyordu, bu Türkçe karakterleri (ı, ş, ğ, ö, ü, ç) koruyamıyordu ("Bogulma Heimlich", "Sok" gibi hatalı çıktılar). 24 belgenin TAMAMI için elle yazılmış, sabit bir DOC_TITLES sözlüğüyle değiştirildi. Ders: az sayıda, sabit veri için (24 belge gibi) algoritmik üretim yerine elle doğrulanmış sabit veri daha güvenilir.
5. Chunk sıralama varsayımı doğrulandı: chunks tablosunda chunk_index kolonu yok, ORDER BY id ASC'in kaynak belgedeki orijinal madde sırasıyla (1, 2, 3...) birebir eşleştiği 01_kanama_kontrolu.md üzerinde TEST EDİLEREK kanıtlandı (varsayımla kabul edilmedi).

### Bilinen, Henüz Çözülmemiş Küçük Sorunlar
- 06_sok.md'de "Şok belirtileri:" gömülü bir alt-blok var, Kaynak: kalıbından farklı, henüz ayrıştırılmadı (kozmetik, düşük öncelik - "cila turu"nda ele alınacak)
- README.md, web arayüzü/API eklenmeden ÖNCEKİ haliyle kaldı, güncellenmesi gerekiyor

---

## Oturum: Frontend UX İyileştirmeleri + README + Eval Kanıtı (12 Ağustos — Devam)

> **Not:** Bu oturum aynı gün içinde Web Arayüzü oturumunun devamıdır, ayrı log girişi gerektiriyor çünkü farklı commit'lere karşılık gelir.

### Tamamlanan İşler (commit: `fb14216`)
- **Scroll düzeltmesi:** Sohbet alanı yeni mesaj geldiğinde otomatik alta kayıyor, eski taşma sorunu giderildi
- **Adım numaralandırma temizliği:** Retrieval'dan dönen adım metinlerinde kaynak dokümanın kendi numaraları çift sayıldığında oluşan `1. 1. Adım` formatı temizlendi
- **Güvenlik uyarı metni güçlendirildi:** Her yanıtın altına yasal sorumluluk reddi eklendi: *"Bu sistem, resmi kaynaklardan derlenmiş genel bilgi sunar; tıbbi personel yerine geçmez."* Mevcut CSS sınıfı kullanıldı, yeni stil eklenmedi

### README Güncellemesi (commit: `b3d042a`)
- README.md, web arayüzü ve API eklenmesiyle birlikte güncellendi; kurulum, kullanım ve mimari açıklama eksiksiz hale getirildi
- ~~"README güncellenmesi gerekiyor" backlog kalemi KAPANDI~~

### Eval Kanıtı Repoya Eklendi (commit: `f20d6f0`)
- `eval/` çıktıları (Precision@3=0.5556, Fallback=%87.5) kalıcı kanıt olarak GitHub'a gönderildi

### Temizlik (commit: `2f9685f`, `3686c3d`)
- Geçici test/debug dosyaları silindi: `backend_test.py`, `visual_check.py`, `measure.py`, `step3.py`
- Analiz scriptleri `docs/` klasörüne taşındı, eski prototip soru seti silindi

---

## Oturum: Canlı Test + Staj Sunumu GitHub Push (18–19 Ağustos)

### Amaç
Projeyi sıfırdan çalıştırıp uçtan uca canlı test etmek; staj sunumunu repoya göndermek.

### Ortam Doğrulaması
| Bileşen | Sürüm / Durum |
|---|---|
| Python | 3.12.4 ✅ |
| foundry-local-sdk | 1.2.4 ✅ |
| openai | 2.52.0 ✅ |
| fastapi | 0.129.2 ✅ |
| uvicorn | 0.41.0 ✅ |
| SQLite DB (afet.db ~6.7 MB) | ✅ |

### Canlı Test Sonuçları
- **Sunucu:** `http://localhost:8000` — tam aktif
- **Yanıt süresi:** `0.12s` (LLM-free template retrieval sayesinde)
- **Aktif kaynak:** 277 chunk / 24 belge / 6 kategori
- **Doğrulama:** %87.5 | **Precision@3:** 0.5556

**Test sorusu:** *"Kanama durumunda ne yapmalıyım?"*
- Protokol: `KNM-01` (Kanama Kontrol Protokolü), aciliyet: Yüksek
- Kaynak: `01_kanama_kontrolu.md`, `06_sok.md` — doğru kategoriden doğru chunk'lar döndü

### Staj Sunumu Git Operasyonu
1. `SUNUM.md` yanlışlıkla commit'lendi → `c563f8e` ile geri alındı
2. Doğru `SUNUM/` klasörü (pptx + pdf) `9b8bc87` commit'iyle push edildi

### Doğrulama Durumu
19 Ağustos oturumunda hiçbir kaynak kod değişikliği yapılmadı. Tüm metrikler (Precision@3, Fallback oranı) değişmeden kaldı. Bu oturum salt operasyonel doğrulama + deployment niteliğindedir.

### Doğrulama Durumu
Tüm yeni özellikler ham JSON çıktılarıyla test edildi. eval/run_eval.py metrikleri (Precision@3=0.5556, Fallback=%87.5) oturum boyunca hiç değişmedi - hiçbir değişiklik retrieval mantığına dokunmadı.
- 6 hızlı sekme (K1-K6) + Deprem (D1) regresyon testi: 7/7 geçti, her biri doğru kategori ve has_sufficient_context=true döndürdü.

### Kullanılan Modeller
Bugünkü oturumda, Claude Sonnet 4.6 limitleri nedeniyle işlerin büyük kısmı Gemini 3.1 Pro ile tamamlandı. Kritik kök-neden analizleri (api.py semantic_score bug'ı) Sonnet ile başlatıldı, mekanik/doğrulama görevleri (dosya okuma, JSON kontrolü, test çalıştırma) Gemini'ye devredildi.

### Tasarım Kararı: Frontend "Komuta Merkezi" Konsepti
Web arayüzü, jenerik "AI chat uygulaması" klişelerinden (koyu tema + neon mor/mavi vurgu, ya da krem + serif + turuncu) bilinçli olarak kaçınacak şekilde tasarlandı. Kimlik: AFAD kurumsal lacivert + Kızılay kırmızısı (sadece acil durum sinyali için), Georgia serif başlıklar + monospace veri etiketleri. Referans: gerçek komuta merkezi/enstrüman paneli estetiği, jenerik chatbot değil.


## Durum (3 Agustos)
- Proje klasoru tasindi: C:\Users\hp\Projeler\afet-ilk-yardim-asistani (scratch'ten cikarildi, kalici konum)
- hello_foundry.py calisiyor ve dogrulandi: gercek API = Configuration + FoundryLocalManager.initialize() + start_web_service() + catalog.get_model()
- Embedding vektor boyutu: 1024 (qwen3-embedding-0.6b)
- normalize_tr.py, chunking.py, db.py ilk uretilen hallerinde bizim tasarimimizla uyumsuzdu
  (db.py SQLite yerine JSON kullaniyordu) -- yeniden yaziliyor
- Siradaki adim: yeni normalize_tr/chunking/db kodunu test etmek, sonucu dogrulamak

## Siradaki adim
Antigravity'de uc dosyayi (normalize_tr.py, chunking.py, db.py) yeniden yaz,
test scriptini calistir, ciktiyi Claude'a getir.

## Durum guncelleme
- normalize_tr.py tamamlandi: yinelemeli ek kesme + unsuz yumusamasi (k/p/c/t <-> g/b/c/d) tersine cevirme
- tests/test_normalize_tr.py: 8 kelime ailesi, hepsi tam esitlik testinden geciyor (esneme yok)
- chunking.py ve db.py yeniden yazildi, izole test edildi (SQLite + FTS5, iki chunking stratejisi)
- hello_foundry.py dogrulandi: gercek API akisi = Configuration + FoundryLocalManager.initialize() + start_web_service() + catalog.get_model(), embedding boyutu = 1024

## Siradaki adim
Adim 2: data/documents/ altina 8 gercek ilk yardim dokumanini yazmak (Kizilay/AFAD kaynakli,
adim-bazli numarali format). Icerik Claude tarafindan resmi kaynaklardan arastirilip
kullanicinin onayiyla derlenecek - hicbir tibbi bilgi hafizadan uydurulmayacak.

## Durum guncelleme (tibbi_ilk_yardim tamamlandi)
- tibbi_ilk_yardim/ klasorunde 9 dosya olusturuldu ve dogrulandi:
  01_kanama_kontrolu (13 adim), 02_kirik_cikik_burkulma (12 adim),
  03_cpr_temel_yasam_destegi (23 adim, yetiskin), 03b_cpr_cocuk (19 adim),
  03c_cpr_bebek (17 adim), 04_bogulma_heimlich (9 adim), 05_yanik (14 adim),
  06_sok (9 adim), 07_donma_hipotermi (9 adim)
- Hepsi T.C. Saglik Bakanligi (2011) kaynakli, chunk_by_step ile dogrulandi
- deprem_davranisi/ (08,09,10) ve idari_surecler/ (16) daha once tamamlanmisti
- Toplam: 16 dokumanin 12'si tamamlandi
- Kalan: kirilgan gruplar (11-13), psikolojik destek (14), acil numaralar (15)

## BACKLOG - Geri donulecek karar: Yazim hatasi toleransi

Durum: Kapsam disi birakildi (bilincli karar, eksiklik degil)

Ne yapilmadi: Genel yazim hatasi duzeltme (harf eksik/fazla/yer degismis
kelimeler). Turkce karakter eksikligi (i/i, s/s gibi) AYRI ele alindi ve
YAPILDI (retrieval.py ASCII fallback fonksiyonu).

Neden yapilmadi: Sinirsiz kapsam riski + kanitlanmis ongorulemez yan etki
riski (genis zaman eki denemesinde "kurtar" kelimesinin "kurt"a cokmesi
gibi). 10 gunluk sure kisitinda bu risk kabul edilemez bulundu.

Guvenlik agi: semantic/embedding katmani + LLM'in "bilmiyorum, 112'yi
arayin" davranisi, yazim hatasi durumunda bile yanlis bilgi verilmesini
engelliyor.

Geri donme kosullari (ikisinden biri gerceklesirse tekrar gundeme alinacak):
1. Eval testinde (Gun 4-5) birden fazla soru gercek yazim hatasi yuzunden
   basarisiz olursa
2. Tampon gunde (Gun 9) plandan once bitilmisse ve bos vakit varsa

Ikisi de gerceklesmezse: ozellik projeye girmez, bu eksiklik degil
gerekceli bir sinirdir.

## Durum (Gun 1-2 tamamlandi)

Gun 1: normalize_tr son ek listesi tamamlandi (4 kategori + guvenlik testi),
retrieval.py'ye ASCII fallback + guven esigi eklendi, chunking baslik
sizintisi duzeltildi.

Gun 2: foundry_session.py (tek birlesik oturum), llm.py (guvenlik promptu +
cevap uretme) yazildi. llm_diagnostic.py ile test edildi: katmanli guvenlik
dogrulandi - retrieval yanlissa bile LLM "112'yi arayin" diyor, uydurma
yapmiyor.

BILINEN SINIRLAMA: has_sufficient_context RRF sirlama-tabanli oldugu icin
kaba bir sinyal (gercek benzerlik buyuklugunu tam yansitmiyor). Esik degeri
Gun 4-5 eval verisiyle kalibre edilecek.

Siradaki adim: cli.py yazilacak (Gun 3), sonra eval cercevesi (Gun 4-5).

## Gun 3 TAMAMLANDI - cli.py + mimari karar + hipotez testi

cli.py yazildi ve test edildi, uctan uca calisiyor.

KRITIK MIMARI KARAR (KESIN): LLM'in ilk yardim/afet talimat icerigini
serbest metin olarak yeniden uretmesi TAMAMEN KALDIRILDI. Gerekce: 3
farkli prompt stratejisi (varsayilan, kisitli, dusuk-temperature) sistematik
test edildi, ucu de phi-3.5-mini ile tutarli sekilde anlamsiz/bozuk Turkce
uretti. Yeni tasarim: generate_answer() kategoriye gore sabit giris cumlesi
+ kaynaktan BIREBIR alintilanan adimlar + sabit guvenlik uyarisi.
Hallucination riski mimari olarak SIFIRLANDI. RAG'in "Generate" adimi
altyapisi (foundry_session.py, llm.py) hala calisir durumda ama uretim
alani bilincli olarak sifira indirildi.

DUZELTME (onceki hatali hipotez): "Yanina diz cokun" chunk'inin birden
fazla alakasiz sorguda ust siraya cikmasi ilk once "embedding uzayinda
merkezi konum (hub chunk)" hipoteziyle aciklanmisti - BU HIPOTEZ TEST
EDILDI VE YANLIS CIKTI (6 alakasiz sorguyla olculen ortalama benzerlik,
rastgele secilen kontrol chunk'lardan farkli degil, hatta bir kontrol
chunk daha yuksek cikti).

GERCEK TEsHIS: qwen3-embedding-0.6b modelinin butun benzerlik uzayi
sikisik (0.26-0.44 araligi) - bu, TUM chunk'lar icin gecerli, tek bir
chunk'in ozel sorunu degil. Model bu korpus olceginde sinirli ayrim
gucune sahip. Sonuc: "cok korkuyorum" gibi korpusla zayif ortusen
sorgular bile has_sufficient_context esigini (0.01) geciyor ve yanlis
kategoriden chunk getiriyor.

BUNUN ONEMI: Bu, Gun 4-5'teki esik kalibrasyonunun (once "kaba tahmin"
olarak planlanmisti) aslinda KRITIK bir duzeltme oldugunu kanitliyor -
zayif bir "guclu chunk" degil, modelin genel ayrim gucu zayifligi soz
konusu. Eval asamasinda esik + kategori-filtreleme birlikte ele alinacak.

Siradaki adim: Gun 4-5, eval/ klasoru - 20-40 etiketli soru, Precision/
Recall/MRR, Category Purity@k, esik kalibrasyonu, guvenlik testi.

## Ek Test: Kapalı-Küme Sınıflandırma Denemesi

phi-3.5-mini, 8 kategoriden birini seçme görevinde (serbest metin üretimi 
DEĞİL, kısıtlı format) test edildi - 8 ambiguous/out_of_scope soru 
üzerinde. Sonuç: 0/8 doğru, format disiplini de bozuldu (bir soruda 
talimatı yok sayıp doğrudan cevap üretti - "Türkiye'nin başkenti 
neresi?" -> "Ankara"). Bu, Gün 3'teki "serbest üretim başarısız" 
bulgusunu tamamlayan ikinci bir kanıt: model bu ölçekte (3.8B) HİÇBİR 
sınıflandırma/karar görevinde güvenilir değil. Sonuç: LLM'in mimaride 
HİÇBİR karar/yönlendirme rolü olmamalı - mevcut "sabit metin + retrieval" 
tasarımı kesin olarak doğrulanmıştır.
