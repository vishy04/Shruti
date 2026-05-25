import os
import modal

app = modal.App("secret-dumper")

@app.function(secrets=[modal.Secret.from_name("shruti-secrets")])
def dump_secrets():
    print("=== DEPLOYED DASHBOARD SECRETS IN 'shruti-secrets' ===")
    for key in sorted(os.environ.keys()):
        val = os.environ[key]
        if key in ["WHATSAPP_APP_SECRET", "WHATSAPP_ACCESS_TOKEN", "GOOGLE_GENAI_API_KEY", "GROQ_API_KEY", "PINECONE_API_KEY"]:
            print(f"{key}: len={len(val)}, preview={val[:4]}...{val[-4:] if len(val) > 4 else ''}")
        elif "JSON" in key or "KEY" in key or "SECRET" in key or "TOKEN" in key or "PASSWORD" in key:
            print(f"{key}: len={len(val)}, preview={val[:4]}...{val[-4:] if len(val) > 4 else ''}")
        else:
            print(f"{key}: {val}")

if __name__ == "__main__":
    with app.run():
        dump_secrets.remote()
