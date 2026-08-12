"""
Türkçe ek temizleme (lightweight stemming) katmanı.
Eklemeli dil yapısı nedeniyle kelimeler birden fazla ek alabilir
(ör. kanama+yı), bu yüzden ekler tek geçişte değil, kelime kısalmayı
bırakana kadar yinelemeli olarak kesilir.
"""
import re

_SUFFIXES = sorted([
    "lerinden", "larından", "lerini", "larını", "leriyle", "larıyla",
    "mizin", "mızın", "nizin", "nızın", "nuzun", "nüzün",
    "iyor", "ıyor", "uyor", "üyor",
    "ıyo", "iyo", "uyo", "üyo",
    "dir", "dır", "dur", "dür",
    "muş", "miş", "mış", "müş",
    "ecek", "acak",
    "malı", "meli",
    "yım", "yim", "yum", "yüm",
    "lar", "ler",
    "nin", "nın", "nun", "nün",
    "den", "dan", "ten", "tan",
    "de", "da", "te", "ta",
    "dı", "di", "du", "dü",
    "tı", "ti", "tu", "tü",
    "yı", "yi", "yu", "yü",
    "sı", "si", "su", "sü",
    "nı", "ni", "nu", "nü",
    "ya", "ye",
    "na", "ne",
    "im", "ım", "um", "üm",
    "in", "ın", "un", "ün",
    "e", "a", "i", "ı", "u", "ü",
], key=len, reverse=True)

_MIN_STEM_LEN = 3
_MAX_PASSES = 3


def normalize_tr(text: str, min_stem_len: int = _MIN_STEM_LEN) -> str:
    """Metni küçük harfe çevirir, her kelimeden ekleri yinelemeli olarak keser,
    ardından ünsüz yumuşamasını tersine çevirir (ğ→k, b→p, c→ç, d→t)."""
    words = re.findall(r"[a-zçğıöşü]+", text.lower())
    _ASCII_MAP = str.maketrans("çğıöşü", "cgiosu")
    return " ".join(
        _harden_final_consonant(_strip_suffixes_iterative(w, min_stem_len)).translate(_ASCII_MAP)
        for w in words
    )


def _strip_suffixes_iterative(word: str, min_stem_len: int) -> str:
    for _ in range(_MAX_PASSES):
        stripped = _strip_one_suffix(word, min_stem_len)
        if stripped == word:
            break
        word = stripped
    return word


def _strip_one_suffix(word: str, min_stem_len: int) -> str:
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= min_stem_len:
            return word[: -len(suf)]
    return word


_SOFT_TO_HARD = {"ğ": "k", "b": "p", "c": "ç", "d": "t"}


def _harden_final_consonant(word: str) -> str:
    """Türkçe ünsüz yumuşamasını (k/p/ç/t -> ğ/b/c/d) tersine çevirir.
    Ek kesildikten sonra ortaya çıkan yumuşak son sesi sert karşılığına
    çevirerek 'kırık' ve 'kırığı' gibi çiftlerin aynı köke düşmesini sağlar."""
    if word and word[-1] in _SOFT_TO_HARD:
        return word[:-1] + _SOFT_TO_HARD[word[-1]]
    return word
