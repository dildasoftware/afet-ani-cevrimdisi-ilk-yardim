"""
Retrieval Değerlendirme Betiği (Evaluation Script)

eval/questions.json dosyasındaki etiketli soruları retrieval.py sistemine sorar ve
şu metrikleri hesaplar:
- Precision@k (k=3 ve k=5)
- Recall@k (k=3 ve k=5)
- MRR (Mean Reciprocal Rank)
- Category Purity@k (k=3 ve k=5)
- Fallback Doğruluğu (ambiguous ve out_of_scope tiplerinde has_sufficient_context == False doğrulaması)
"""

import json
import os
import sys
from datetime import datetime

# src modüllerine erişim
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from db import get_connection
from embeddings import init_foundry_embedding_session, get_embedding
from normalize_tr import normalize_tr
from retrieval import (
    bm25_search_with_fallback,
    semantic_search,
    rrf_fuse,
    has_sufficient_context,
)


def load_questions(questions_path: str = None) -> list[dict]:
    """eval/questions.json dosyasını yükler. Bulunamazsa net hata mesajıyla çöker."""
    if questions_path is None:
        questions_path = os.path.join(PROJECT_ROOT, "eval", "questions.json")

    if not os.path.exists(questions_path):
        raise FileNotFoundError(
            f"HATA: eval/questions.json bulunamadı. Beklenen konum: {questions_path}"
        )

    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_keyword_hit(keyword: str, chunk_content: str) -> bool:
    """
    normalize_tr rakamları siler (bkz. eval ön-analiz raporu),
    sayısal keyword'ler ham karşılaştırılır. Alfabetik keyword'ler
    ise normalize_tr ile karşılaştırılır.
    """
    if keyword.isdigit():
        return keyword in chunk_content

    norm_kw = normalize_tr(keyword)
    norm_content = normalize_tr(chunk_content)
    return bool(norm_kw and norm_kw in norm_content)


def run_single_query(conn, client, model_id: str, question: str, top_k: int = 5) -> tuple[list[dict], bool, float]:
    """
    BM25 + Semantic + RRF araması yapar.
    Oturum (client/model_id) dışarıdan parametre olarak alınır.
    Döndürür: (fused_results, has_sufficient_context, top_semantic_score)
    """
    query_vec = get_embedding(client, model_id, question)
    bm25_res = bm25_search_with_fallback(conn, question, k=top_k)
    sem_res = semantic_search(conn, query_vec, k=top_k)
    fused = rrf_fuse(bm25_res, sem_res, k=top_k)
    top_semantic_score = sem_res[0]["score"] if sem_res else 0.0
    has_ctx = has_sufficient_context(fused, top_semantic_score=top_semantic_score)
    return fused, has_ctx, top_semantic_score


def compute_metrics_for_question(q: dict, fused_results: list[dict], has_ctx: bool,
                                  top_semantic_score: float = 0.0, k_values: list[int] = [3, 5]) -> dict:
    """
    Tek bir soru için Precision@k, Recall@k, MRR, Category Purity@k ve Fallback doğrulukunu hesaplar.
    top_semantic_score: semantic_search rank-1 sonucunun ham cosine similarity değeri.
    """
    q_type = q["question_type"]
    expected_category = q.get("expected_category")
    keywords = q.get("relevant_chunk_keywords", [])
    expected_has_ctx = q["expected_has_sufficient_context"]

    # ambiguous ve out_of_scope sorularında precision/recall/purity hesaplanmaz (None)
    if q_type in {"ambiguous", "out_of_scope"}:
        fallback_success = (has_ctx == expected_has_ctx)
        return {
            "id": q["id"],
            "question": q["question"],
            "question_type": q_type,
            "expected_category": expected_category,
            "expected_has_sufficient_context": expected_has_ctx,
            "actual_has_sufficient_context": has_ctx,
            "top_semantic_score": round(top_semantic_score, 6),
            "fallback_success": fallback_success,
            "precision": {f"p@{k}": None for k in k_values},
            "recall": {f"r@{k}": None for k in k_values},
            "mrr": None,
            "category_purity": {f"purity@{k}": None for k in k_values},
            "retrieved_chunks": [
                {
                    "rank": idx + 1,
                    "id": c["id"],
                    "category": c["category"],
                    "source_doc": c["source_doc"],
                    "rrf_score": c["rrf_score"],
                    "semantic_score": c.get("semantic_score", 0.0),
                    "content_snippet": c["content"][:100] + "..." if len(c["content"]) > 100 else c["content"],
                }
                for idx, c in enumerate(fused_results)
            ],
        }

    # Normal ve age_specific sorular için detaylı metrikler
    evaluated_chunks = []
    first_hit_rank = None

    for idx, c in enumerate(fused_results):
        rank = idx + 1
        content = c["content"]
        cat = c["category"]

        # Hangi keyword'ler isabet etti?
        matched_kws = [kw for kw in keywords if is_keyword_hit(kw, content)]
        is_hit = len(matched_kws) > 0
        cat_match = (cat == expected_category)

        if is_hit and first_hit_rank is None:
            first_hit_rank = rank

        evaluated_chunks.append({
            "rank": rank,
            "id": c["id"],
            "category": cat,
            "source_doc": c["source_doc"],
            "rrf_score": c["rrf_score"],
            "semantic_score": c.get("semantic_score", 0.0),
            "content_snippet": content[:100] + "..." if len(content) > 100 else content,
            "matched_keywords": matched_kws,
            "is_hit": is_hit,
            "category_match": cat_match,
        })

    # Precision@k, Recall@k, Category Purity@k hesaplama
    precision_dict = {}
    recall_dict = {}
    purity_dict = {}

    for k in k_values:
        sub = evaluated_chunks[:k]
        hits = sum(1 for c in sub if c["is_hit"])
        cat_matches = sum(1 for c in sub if c["category_match"])

        # Payda HER ZAMAN SABİT k kalır (fused_results 5'ten az gelse bile)
        precision_dict[f"p@{k}"] = round(hits / k, 4)
        purity_dict[f"purity@{k}"] = round(cat_matches / k, 4)

        # Recall: k içindeki benzersiz keyword isabet sayısı / toplam keyword sayısı
        unique_kws_hit = set()
        for c in sub:
            unique_kws_hit.update(c["matched_keywords"])

        if keywords:
            recall_dict[f"r@{k}"] = round(len(unique_kws_hit) / len(keywords), 4)
        else:
            recall_dict[f"r@{k}"] = 0.0

    # MRR
    mrr = round(1.0 / first_hit_rank, 4) if first_hit_rank is not None else 0.0

    fallback_success = (has_ctx == expected_has_ctx)

    return {
        "id": q["id"],
        "question": q["question"],
        "question_type": q_type,
        "expected_category": expected_category,
        "expected_has_sufficient_context": expected_has_ctx,
        "actual_has_sufficient_context": has_ctx,
        "top_semantic_score": round(top_semantic_score, 6),
        "fallback_success": fallback_success,
        "precision": precision_dict,
        "recall": recall_dict,
        "mrr": mrr,
        "category_purity": purity_dict,
        "retrieved_chunks": evaluated_chunks,
    }


def compute_fallback_accuracy(all_results: list[dict]) -> float:
    """ambiguous ve out_of_scope tipi sorular için fallback doğruluk oranını hesaplar."""
    fallback_qs = [
        r for r in all_results
        if r["question_type"] in {"ambiguous", "out_of_scope"}
    ]
    if not fallback_qs:
        return 0.0

    correct = sum(1 for r in fallback_qs if r["fallback_success"])
    return round(correct / len(fallback_qs), 4)


def aggregate_by_type(all_results: list[dict], k_values: list[int] = [3, 5]) -> dict:
    """Tüm soruların geneli ve soru tipi bazında ortalamaları hesaplar."""
    groups = {}

    # Soru tiplerine göre grupla
    for r in all_results:
        t = r["question_type"]
        groups.setdefault(t, []).append(r)

    # İlgili (normal/age_specific) sorular
    content_qs = [r for r in all_results if r["question_type"] in {"normal", "age_specific"}]

    def _calc_averages(qs):
        if not qs:
            return None
        res = {}
        for k in k_values:
            res[f"p@{k}"] = round(sum(r["precision"][f"p@{k}"] for r in qs) / len(qs), 4)
            res[f"r@{k}"] = round(sum(r["recall"][f"r@{k}"] for r in qs) / len(qs), 4)
            res[f"purity@{k}"] = round(sum(r["category_purity"][f"purity@{k}"] for r in qs) / len(qs), 4)
        res["mrr"] = round(sum(r["mrr"] for r in qs) / len(qs), 4)
        return res

    by_type_summary = {}
    for t, qs in groups.items():
        if t in {"normal", "age_specific"}:
            by_type_summary[t] = {
                "count": len(qs),
                "metrics": _calc_averages(qs)
            }
        else:
            correct_count = sum(1 for r in qs if r["fallback_success"])
            by_type_summary[t] = {
                "count": len(qs),
                "fallback_accuracy": round(correct_count / len(qs), 4) if qs else 0.0
            }

    overall_metrics = _calc_averages(content_qs)

    return {
        "overall_content_metrics": overall_metrics,
        "total_questions": len(all_results),
        "content_questions_count": len(content_qs),
        "by_question_type": by_type_summary,
    }


def print_console_table(aggregate: dict, fallback_acc: float):
    """Metrik sonuçlarını okunaklı bir konsol tablosu olarak yazdırır."""
    print("\n" + "=" * 70)
    print(" RETRIEVAL EVALUATION (DEĞERLENDİRME) SONUÇLARI")
    print("=" * 70)

    over = aggregate.get("overall_content_metrics")
    if over:
        print(f" Genel Bilgi Soruları (N={aggregate['content_questions_count']}) Ortalamaları:")
        print(f"   Precision@3 : {over['p@3']:.4f}  |  Precision@5 : {over['p@5']:.4f}")
        print(f"   Recall@3    : {over['r@3']:.4f}  |  Recall@5    : {over['r@5']:.4f}")
        print(f"   MRR         : {over['mrr']:.4f}")
        print(f"   Purity@3    : {over['purity@3']:.4f}  |  Purity@5    : {over['purity@5']:.4f}")
    else:
        print(" Bilgi sorusu metriği hesaplanamadı.")

    print("-" * 70)
    print(" Soru Tipi Bazında Kırılım:")

    for q_type, data in aggregate.get("by_question_type", {}).items():
        cnt = data["count"]
        if "metrics" in data and data["metrics"]:
            m = data["metrics"]
            print(f"   > {q_type:<14} (N={cnt}): P@3={m['p@3']:.2f}, P@5={m['p@5']:.2f}, R@3={m['r@3']:.2f}, R@5={m['r@5']:.2f}, MRR={m['mrr']:.2f}, Pur@5={m['purity@5']:.2f}")
        elif "fallback_accuracy" in data:
            acc = data["fallback_accuracy"]
            print(f"   > {q_type:<14} (N={cnt}): Fallback Doğruluğu = {acc * 100:.1f}%")

    print("-" * 70)
    print(f" Toplam Fallback Doğruluğu (ambiguous + out_of_scope): {fallback_acc * 100:.1f}% ({int(fallback_acc * 8)}/8)")
    print("=" * 70 + "\n")


def save_results_json(all_results: list[dict], aggregate: dict, fallback_acc: float, path: str = None):
    """Sonuçları eval/results.json olarak kaydeder."""
    if path is None:
        path = os.path.join(PROJECT_ROOT, "eval", "results.json")

    output_data = {
        "meta": {
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(all_results),
            "k_values": [3, 5],
        },
        "aggregate": {
            "overall_content_metrics": aggregate.get("overall_content_metrics"),
            "fallback_accuracy": fallback_acc,
        },
        "by_question_type": aggregate.get("by_question_type"),
        "questions": all_results,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    db_path = os.path.join(PROJECT_ROOT, "data", "afet.db")
    conn = get_connection(db_path)

    # 1. Questions dosyasını yükle (yoksa FileNotFoundError fırlatır)
    questions = load_questions()

    # 2. Embedding oturumunu DÖNGÜ DIŞINDA TEK KERE başlat
    print("Foundry Local Embedding oturumu başlatılıyor...")
    client, model_id = init_foundry_embedding_session()
    print("Oturum açıldı. Değerlendirme başlatılıyor...\n")

    all_results = []

    for q in questions:
        fused_res, has_ctx, top_sem = run_single_query(conn, client, model_id, q["question"], top_k=5)
        metrics = compute_metrics_for_question(q, fused_res, has_ctx, top_semantic_score=top_sem, k_values=[3, 5])
        all_results.append(metrics)

    conn.close()

    # Ortalamalar ve Fallback doğruluğu
    fallback_acc = compute_fallback_accuracy(all_results)
    aggregate = aggregate_by_type(all_results, k_values=[3, 5])

    # Konsola bas
    print_console_table(aggregate, fallback_acc)

    # JSON kaydet
    save_results_json(all_results, aggregate, fallback_acc)

    print("Eval tamamlandı. Sonuçlar eval/results.json içinde.")


if __name__ == "__main__":
    main()
