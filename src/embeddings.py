"""
Foundry Local embedding oturumu ve embedding alma yardımcı fonksiyonları.
hello_foundry.py'de dogrulanan gercek API kullanilir. Oturum bir kez acilir,
her chunk icin yeniden baslatilmaz (verimlilik).
"""
from foundry_local_sdk import Configuration, FoundryLocalManager
from openai import OpenAI


def init_foundry_embedding_session(app_name: str = "afet-asistan"):
    config = Configuration(
        app_name=app_name,
        web=Configuration.WebService(),
    )
    FoundryLocalManager.initialize(config)
    mgr = FoundryLocalManager.instance
    mgr.start_web_service()

    base_url = mgr.urls[0]
    api_key = "foundry-local"

    emb_model = mgr.catalog.get_model("qwen3-embedding-0.6b")
    if emb_model is None:
        raise RuntimeError("qwen3-embedding-0.6b modeli katalogda bulunamadi")
    if not emb_model.is_cached:
        emb_model.download()
    emb_model.load()

    client = OpenAI(base_url=base_url + "/v1", api_key=api_key)
    return client, emb_model.id


def get_embedding(client, model_id: str, text: str):
    resp = client.embeddings.create(model=model_id, input=[text])
    return resp.data[0].embedding
