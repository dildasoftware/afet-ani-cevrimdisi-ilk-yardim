"""
normalize_tr için kalıcı regresyon testleri.
Her grup aynı köke düşmesi beklenen kelime ailelerini içerir.
Bu dosya her yeni ek eklendiğinde/değiştiğinde çalıştırılmalı.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from normalize_tr import normalize_tr

# Tüm üyeler aynı köke düşmeli (ünsüz sertleştirme dahil).
WORD_FAMILIES_SAME_ROOT = [
    ["kanama", "kanamayı", "kanamalar", "kanamasının", "kanamaların"],
    ["kırık", "kırığı", "kırıkları", "kırığın"],
    ["yanık", "yanığı", "yanıkları", "yanığın"],
    ["boğulma", "boğulmayı", "boğulmalar", "boğulmanın"],
    ["şok", "şoku", "şokun", "şoklar"],
    ["hipotermi", "hipotermiyi", "hipoterminin"],
    ["bandaj", "bandajı", "bandajın", "bandajlar"],
    ["turnike", "turnikeyi", "turnikenin"],
]


def test_word_families_normalize_to_same_root():
    failures = []
    for family in WORD_FAMILIES_SAME_ROOT:
        roots = {normalize_tr(w) for w in family}
        if len(roots) > 1:
            failures.append((family, roots))
    if failures:
        for family, roots in failures:
            print(f"UYUSMUYOR: {family} -> {roots}")
        raise AssertionError(f"{len(failures)} kelime ailesi farkli koke dustu")
    print(f"[OK] {len(WORD_FAMILIES_SAME_ROOT)} ayni-kok ailesi tutarli sekilde normalize edildi.")


def test_noktalama_isaretleri_ek_kesmeyi_engellemez():
    from normalize_tr import normalize_tr
    noktali = normalize_tr("Kanayan yer üzerine temiz bir bezle bastırın.")
    noktasiz = normalize_tr("Kanayan yer üzerine temiz bir bezle bastırın")
    assert noktali == noktasiz, f"UYUSMUYOR: '{noktali}' != '{noktasiz}'"
    print(f"[OK] Noktalama testi gecti: '{noktali}'")


def test_gecmis_zaman_gereklilik_konusma_dili_ve_guvenlik():
    from normalize_tr import normalize_tr
    vakalar = [
        (["yaralandı"], "gecmis zaman - yaralanmak"),
        (["düştü"], "gecmis zaman - dusmek"),
        (["bayıldı"], "gecmis zaman - bayilmak"),
        (["kırıldı"], "gecmis zaman - kirilmak"),
        (["yapmalıyım", "yapmalı"], "gereklilik kipi - yapmak"),
        (["kanıyor", "kanıyo"], "konusma dili yor->yo"),
        (["geliyorum", "geliyo"], "konusma dili yor->yo 2"),
    ]
    hata_var = False
    for kelimeler, aciklama in vakalar:
        kokler = set(normalize_tr(k) for k in kelimeler)
        if len(kokler) != 1:
            print(f"HATA [{aciklama}]: {kelimeler} -> {kokler}")
            hata_var = True
        else:
            print(f"[OK] [{aciklama}]: {kelimeler} -> {kokler}")

    guvenlik_kontrolleri = {
        "kurtar": "kurt",
        "durdur": "durt",
    }
    for kelime, yasakli_sonuc in guvenlik_kontrolleri.items():
        sonuc = normalize_tr(kelime)
        if sonuc == yasakli_sonuc:
            print(f"GUVENLIK HATASI: '{kelime}' -> '{sonuc}' (TAHRIP OLDU, genis zaman eki yanlislikla eklenmis olabilir)")
            hata_var = True
        else:
            print(f"[OK] GUVENLIK: '{kelime}' -> '{sonuc}' (tahrip olmadi)")

    assert not hata_var, "Yukaridaki hatalara bak"
    print("[OK] Tum gecmis zaman/gereklilik/konusma dili/guvenlik testleri gecti")


def test_ascii_katlama_turkce_karakter_eksikligi():
    from normalize_tr import normalize_tr
    cift_kontrolleri = [
        (["boğulma", "bogulma"], "bogulma - turkce/ascii"),
        (["kırık", "kirik"], "kirik - turkce/ascii"),
        (["yanık", "yanik"], "yanik - turkce/ascii"),
    ]
    hata_var = False
    for kelimeler, aciklama in cift_kontrolleri:
        kokler = set(normalize_tr(k) for k in kelimeler)
        if len(kokler) != 1:
            print(f"HATA [{aciklama}]: {kelimeler} -> {kokler}")
            hata_var = True
        else:
            print(f"[OK] [{aciklama}]: {kelimeler} -> {kokler}")
    assert not hata_var, "Turkce/ASCII ciftleri birlesmedi"
    print("[OK] ASCII katlama testi gecti")


if __name__ == "__main__":
    test_word_families_normalize_to_same_root()
    test_noktalama_isaretleri_ek_kesmeyi_engellemez()
    test_gecmis_zaman_gereklilik_konusma_dili_ve_guvenlik()
    test_ascii_katlama_turkce_karakter_eksikligi()
