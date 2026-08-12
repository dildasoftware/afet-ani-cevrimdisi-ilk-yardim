"""
Tek, birlesik Foundry Local oturumu: hem embedding hem chat modelini
AYNI oturumdan yukler. Iki ayri initialize() cagirmak (biri embedding
biri chat icin) singleton oturumla catisir - bu yuzden TEK fonksiyon
kullanilmali.
"""
from foundry_local_sdk import Configuration, FoundryLocalManager
from openai import OpenAI


def init_foundry_full_session(app_name: str = "afet-asistan"):
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

    chat_model = mgr.catalog.get_model("phi-3.5-mini")
    if chat_model is None:
        raise RuntimeError("phi-3.5-mini modeli katalogda bulunamadi")
    if not chat_model.is_cached:
        chat_model.download()
    chat_model.load()

    client = OpenAI(base_url=base_url + "/v1", api_key=api_key)
    return client, emb_model.id, chat_model.id
