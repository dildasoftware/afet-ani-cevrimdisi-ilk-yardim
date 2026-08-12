import sys, os
sys.path.insert(0, 'src')
from db import get_connection
from foundry_session import init_foundry_full_session
import json, math

def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

conn = get_connection('data/afet.db')
client, emb_model_id, chat_model_id = init_foundry_full_session()

supheli = conn.execute(
    "SELECT c.id, c.content, e.vector FROM chunks c JOIN embeddings e ON c.id=e.chunk_id "
    "WHERE c.content LIKE '%Yan%na diz %k%n%' LIMIT 1"
).fetchone()
print("SUPHELI CHUNK:", supheli["content"])
supheli_vec = json.loads(supheli["vector"])

kontrol_chunklari = conn.execute(
    "SELECT c.id, c.content, e.vector FROM chunks c JOIN embeddings e ON c.id=e.chunk_id "
    "ORDER BY RANDOM() LIMIT 6"
).fetchall()

test_sorgulari = [
    "acil numaralar nelerdir",
    "engelli bireyler icin afet cantasi",
    "deprem sonrasi tahliye sureci",
    "cocuklarla nasil konusmaliyim",
    "yanik tedavisi",
    "kirik kemik belirtileri",
]

print()
print("=== SUPHELI CHUNK'IN 6 ALAKASIZ SORGUYLA ORTALAMA BENZERLIGI ===")
supheli_skorlar = []
for soru in test_sorgulari:
    qv = client.embeddings.create(model=emb_model_id, input=[soru]).data[0].embedding
    skor = cosine(supheli_vec, qv)
    supheli_skorlar.append(skor)
    print(f"  '{soru}' -> {skor:.4f}")
print(f"  ORTALAMA: {sum(supheli_skorlar)/len(supheli_skorlar):.4f}")

print()
print("=== 6 RASTGELE KONTROL CHUNK'IN AYNI SORGULARLA ORTALAMA BENZERLIGI ===")
query_vectors = []
for soru in test_sorgulari:
    qv = client.embeddings.create(model=emb_model_id, input=[soru]).data[0].embedding
    query_vectors.append(qv)

for kc in kontrol_chunklari:
    kc_vec = json.loads(kc["vector"])
    skorlar = [cosine(kc_vec, qv) for qv in query_vectors]
    ort = sum(skorlar)/len(skorlar)
    print(f"  '{kc['content'][:40]}...' -> ORTALAMA: {ort:.4f}")
