# Afet Anı: Çevrimdışı İlk Yardım Asistanı

**İnternet olmadığında çalışan, resmi kaynaklardan doğrulanmış, yapay zekânın asla tahmin etmediği bir acil durum asistanı.**

*Microsoft Foundry Local Staj Projesi*  
*[Ad Soyad] · [Tarih]*  
*GitHub: [dildasoftware/afet-ani-cevrimdisi-ilk-yardim](https://github.com/dildasoftware/afet-ani-cevrimdisi-ilk-yardim)*

---

## ⚠️ Sorun: Deprem anında internet çöktüğünde ne olur?

2023 Kahramanmaraş depreminde baz istasyonları çöktü, elektrik kesildi, milyonlarca insan saatlerce — bazen günlerce — internete erişemedi. Tam da en çok bilgiye ihtiyaç duyduğumuz anda, cebimizdeki en güçlü araç işe yaramaz hale geldi.

**Bu proje, tam olarak bu soruya cevap arıyor:**  
> *"İnterneti hiç beklemeyen bir ilk yardım asistanı yapabilir miyiz?"*

### Çevrimdışı Çalışma
Sistem, kurulumdan sonra **hiçbir internet bağlantısı gerektirmeden** çalışır.
Model çalıştırma, arama, cevap üretimi — hepsi kullanıcının kendi bilgisayarında.

---

## 💡 Çözüm: Tamamen yerel çalışan bir RAG sistemi

RAG (Retrieval-Augmented Generation): kullanıcının sorusu önce kendi yerel bilgi tabanında aranır, sonra bulunan gerçek kaynaklardan cevap oluşturulur.

* **Microsoft Foundry Local:** Yapay zeka modelleri bulutta değil, doğrudan kullanıcının bilgisayarında çalışır.
* **277 Doğrulanmış Kaynak:** 24 resmi belgeden derlenmiş, T.C. Sağlık Bakanlığı ve AFAD kaynaklı bilgi.
* **Tahmin Etmeyen Model:** Yapay zeka hiçbir zaman kendi kelimeleriyle konuşmaz — sadece kaynaktan alıntı yapar.

---

## 🏗️ Mimari: Sorudan cevaba hibrit arama hattı

1. **Kullanıcı Sorusu**
2. **BM25 (Anahtar Kelime)** + **Semantic Search (Anlam Bazlı)**
3. **RRF Birleştirme**
4. **Eşik Kontrolü**

* **Yeterli Bağlam Var:** Kaynaktan birebir alıntı + kategoriye özel giriş cümlesi + Acil Durum Kartı gösterilir.
* **Yetersiz Bağlam:** Sistem tahmin etmez — kullanıcıyı daha açık bir soru sormaya yönlendirir, 112’yi hatırlatır.
* **S.O.S. Baypas:** Acil durum modu, yukarıdaki tüm arama hattını atlayarak anında 112 bilgisini gösterir — panik anında saniyeler önemlidir.

---

## 🛑 En Kritik Mühendislik Kararı: Model, hiçbir zaman kendi kelimeleriyle konuşmaz

Geliştirme sürecinde, küçük dil modeli (phi-3.5-mini) iki farklı görevde test edildi. İkisinde de sistematik olarak başarısız oldu — bu, mimarinin temel taşı haline geldi.

* **3/3 Serbest Üretim Stratejisi:** Tutarlı şekilde bozuk Türkçe üretti.
* **0/8 Kapalı-küme Sınıflandırma:** Doğru kategori seçilemedi.

**Sonuç:** LLM’e hiçbir zaman karar verme veya metin üretme yetkisi verilmedi — sadece doğrulanmış kaynak metinleri birebir sunar.

---

## ⚙️ Teknoloji Yığını: Ne kullandık, neden kullandık?

* **Foundry Local:** Yerel model çalıştırma altyapısı
* **qwen3-embedding-0.6b:** 1024 boyutlu anlamsal vektör üretimi
* **SQLite + FTS5:** Yerel veritabanı ve tam metin arama
* **BM25 + RRF:** Hibrit anahtar kelime + anlam bazlı sıralama
* **FastAPI:** Web arayüzü için backend API
* **Vanilla JS/CSS:** Harici bağımlılık olmadan, offline-uyumlu arayüz

---

## 📚 Bilgi Tabanı: Sadece resmi, doğrulanmış kaynaklardan

* **277** Bilgi Parçası
* **24** Kaynak Belge
* **6** Kategori *(Tıbbi İlk Yardım, Deprem Davranışı, Kırılgan Gruplar, Psikolojik Destek, İletişim Kaynakları, İdari Süreçler)*

**Kaynaklar:** *T.C. Sağlık Bakanlığı, AFAD, Türk Kızılay, İPKB/İSMEP, T.C. İçişleri Bakanlığı*

---

## 🖥️ Web Arayüzü: “Komuta Merkezi” — Bir sohbet uygulaması değil

Jenerik yapay zeka sohbet klişelerinden bilinçli olarak kaçınıldı — AFAD lacivert ve Kızılay kırmızısı kimliğiyle, gerçek bir enstrüman paneli estetiği.

* **Hızlı Protokol:** Tek tıkla en sık ihtiyaç duyulan 6+ senaryo
* **Protokoller:** 24 belgenin tamamı, kategori kategori gezinme
* **Vaka Geçmişi:** Oturum boyunca sorulan tüm sorular ve cevaplar
* **Bölge Bilgisi:** AFAD’ın resmi toplanma alanı servisine yönlendirme
* **S.O.S. Kartı:** Aramayı atlayarak anında 112 bilgisi ve söz şablonu
* **Anlık Arama:** Protokolleri yazdıkça filtreleme (Ctrl+K)

---

## 📊 Değerlendirme: 20 soruluk etiketli test setiyle ölçüldü

* **Precision@3:** 0.56
* **Recall@3:** 0.42
* **MRR:** 0.65
* **Fallback Doğruluğu (Güvenli Reddetme):** %87.5

> Belirsiz veya kapsam dışı 8 sorudan 7’sinde sistem doğru şekilde “bilmiyorum” dedi — uydurma cevap vermedi. Kalan 1 durum: dilin doğal belirsizliğinden kaynaklanan, matematiksel olarak tek eşikle çözülemeyen bilinen bir sınır.

---

## 📈 Geliştirme Süreci: Dört gerçek hata, dört ölçülebilir iyileşme

| Aşama | Precision@3 | Fallback Doğruluğu |
| :--- | :--- | :--- |
| İlk ölçüm | 0.4722 | %0 |
| Eşik mekanizması düzeltmesi | 0.4722 | %50 |
| Bağlamsal embedding | 0.5556 | %62.5 |
| Fusion-skor hatası düzeltmesi | 0.5556 | %87.5 |

**En değerli ders:**  
*“RRF skoru sıralama içindir, güven eşiği için doğrudan kullanılamaz.”* Bu hata iki farklı kod yolunda (CLI ve API) ayrı ayrı ortaya çıktı — aynı prensibin her yerde titizlikle uygulanması gerektiğinin kanıtı.

---

## ⚠️ Dürüst Değerlendirme: Bilinen Sınırlamalar

*Bunlar birer eksiklik değil, gerekçelendirilmiş mühendislik kararları.*

* **Matematiksel olarak çözülemez sınır durumu:** Dilin doğal belirsizliği, tek bir eşikle tam çözülemiyor.
* **Reranker eksikliği:** Cross-encoder modeli Foundry Local kataloğunda mevcut değil.
* **Küçük ölçekli embedding:** Yazım/noktalama farklarına duyarlı olabiliyor.
* **Test seti boyutu:** 20 soru ile sınırlı — daha geniş veriyle genellenebilirlik artırılabilir.
* **LLM kısıtı:** Hiçbir karar/üretim rolü almıyor — doğal bir sohbet deneyimini (geri soru sorma) engelliyor.

---

## 🧠 Çıkarımlar: Öğrenilen Dersler

1. **RRF skoru güven ölçüsü değildir:** Sıralama için tasarlanmış bir skor, mutlak alaka düzeyini göstermez.
2. **Katmanlar arası tutarlılık kritik:** BM25 ve embedding’in aynı bağlamı kullanması Precision’ı %18 artırdı.
3. **Eval doğru ≠ üretim doğru:** Eşik düzeltmesi eval’e uygulandı ama CLI’ye uygulanmamıştı — sessizce bozuktu.
4. **Küçük modellerin sınırı erken test edilmeli:** Serbest üretim ve sınıflandırma ayrı ayrı test edilerek mimari netleşti.

---

### Teşekkürler

> *"Bir sistemin en önemli özelliği, ne kadar akıllı görünmesi değil, ne zaman ‘bilmiyorum’ demesi gerektiğini bilmesidir."*
