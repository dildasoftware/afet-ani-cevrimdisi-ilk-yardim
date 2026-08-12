from foundry_local_sdk import Configuration, FoundryLocalManager

# ------------------------------------------------------------------ #
# 1. SDK'yı başlat + web servisini aç                                 #
# ------------------------------------------------------------------ #
config = Configuration(
    app_name="afet-asistan",
    web=Configuration.WebService(),   # rastgele port
)
FoundryLocalManager.initialize(config)
mgr = FoundryLocalManager.instance
mgr.start_web_service()

base_url = mgr.urls[0]
api_key  = "foundry-local"
print(f"Foundry Local endpoint: {base_url}")

# ------------------------------------------------------------------ #
# 2. phi-3.5-mini ile sohbet testi                                    #
# ------------------------------------------------------------------ #
chat_model = mgr.catalog.get_model("phi-3.5-mini")
if chat_model is None:
    print("CHAT TEST BASARISIZ: phi-3.5-mini modeli katalogda bulunamadi.")
else:
    print(f"phi-3.5-mini bulundu: id={chat_model.id}, cached={chat_model.is_cached}")
    if not chat_model.is_cached:
        print("Indiriliyor (phi-3.5-mini)... Bu biraz zaman alabilir.")
        def prog(p):
            print(f"  indirme: {p:.1f}%", end="\r", flush=True)
        chat_model.download(progress_callback=prog)
        print()
    chat_model.load()
    print("phi-3.5-mini yuklendi.")

    from openai import OpenAI
    client = OpenAI(base_url=base_url + "/v1", api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=chat_model.id,
            messages=[{"role": "user", "content": "Merhaba, bir cümlede kendini tanıt."}]
        )
        print("CHAT TEST:", resp.choices[0].message.content)
    except Exception as e:
        print("CHAT TEST BASARISIZ:", e)

# ------------------------------------------------------------------ #
# 3. qwen3-embedding-0.6b ile embedding testi                         #
# ------------------------------------------------------------------ #
try:
    emb_model = mgr.catalog.get_model("qwen3-embedding-0.6b")
    if emb_model is None:
        raise RuntimeError("qwen3-embedding-0.6b katalogda bulunamadi")
    print(f"Embedding modeli bulundu: id={emb_model.id}, cached={emb_model.is_cached}")
    if not emb_model.is_cached:
        print("Indiriliyor (qwen3-embedding-0.6b)...")
        def prog_emb(p):
            print(f"  indirme: {p:.1f}%", end="\r", flush=True)
        emb_model.download(progress_callback=prog_emb)
        print()
    emb_model.load()
    print("qwen3-embedding-0.6b yuklendi.")

    from openai import OpenAI as OAI
    emb_client = OAI(base_url=base_url + "/v1", api_key=api_key)
    emb = emb_client.embeddings.create(
        model=emb_model.id,
        input=["kanama kontrolü nasıl yapılır"]
    )
    print("EMBEDDING TEST: basarili, vektor uzunlugu =", len(emb.data[0].embedding))
except Exception as e:
    print("EMBEDDING TEST BASARISIZ:", e)
