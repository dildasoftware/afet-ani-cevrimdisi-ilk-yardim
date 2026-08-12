import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from db import get_connection
from foundry_session import init_foundry_full_session
from cli import answer_query

def test_queries():
    print("Foundry Local oturumu başlatılıyor, modeller yükleniyor...")
    client, emb_model_id, chat_model_id = init_foundry_full_session()
    conn = get_connection(os.path.join(os.path.dirname(__file__), "data", "afet.db"))

    queries = [
        "biri hasta oldu",
        "çok korkuyorum",
        "yarın hava nasıl olacak"
    ]
    
    for q in queries:
        print(f"\n{'='*50}\nSORU: {q}")
        cevap, _ = answer_query(conn, client, emb_model_id, chat_model_id, q)
        print(f"CEVAP:\n{cevap}")
        
if __name__ == "__main__":
    test_queries()
