"""
Belge parçalama (chunking) stratejileri: paragraf-bazlı ve adım-bazlı.
İlk yardım dokümanları numaralı adım listesi formatında yazılacağı için
iki stratejiyi eval aşamasında karşılaştıracağız.
"""
import re
from typing import List


def chunk_by_paragraph(text: str, max_chars: int = 500) -> List[str]:
    """Paragraf sınırlarına göre böler; uzun paragrafları max_chars'a göre ayırır."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        if len(p) <= max_chars:
            chunks.append(p)
        else:
            words, current, length = p.split(), [], 0
            for w in words:
                if length + len(w) + 1 > max_chars and current:
                    chunks.append(" ".join(current))
                    current, length = [], 0
                current.append(w)
                length += len(w) + 1
            if current:
                chunks.append(" ".join(current))
    return chunks


_STEP_PATTERN = re.compile(r"(?m)^\s*\d+\.\s+")


def chunk_by_step(text: str) -> List[str]:
    """Numaralı adım listelerini ('1. ... 2. ...') her adım ayrı chunk olacak
    şekilde böler. Numaralı adım bulunamazsa paragraf-bazlı chunking'e düşer."""
    matches = list(_STEP_PATTERN.finditer(text))
    if not matches:
        return chunk_by_paragraph(text)
    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        chunk = re.sub(r'\n##[^\n]*\n?$', '', chunk).strip()
        if chunk:
            chunks.append(chunk)
    return chunks
