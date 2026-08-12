# Geçmiş Analiz Scriptleri

Bu klasördeki dosyalar, projenin geliştirme sürecinde (Gün 3) 
mimari kararları desteklemek için kullanılan bağımsız teşhis 
scriptleridir. Hiçbiri üretim kodunun (src/ altındaki aktif 
modüllerin) bir parçası değildir ve hiçbiri import edilmez.

Detaylı bulgular için bkz: ../../PROJECT_LOG.md

- `hybrid_diagnostic.py`: Hibrit retrieval (BM25+semantic) davranış testi
- `llm_diagnostic.py`: Uçtan uca LLM/retrieval entegrasyon testi
- `semantic_diagnostic.py`: Gündelik dil ile semantic similarity ölçümü
- `term_frequency_diagnostic.py`: BM25 gürültü terimi tespiti
