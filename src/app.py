from modal import secret
import modal

app = modal.App("shruti")

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("ffmpeg")
    .uv_pip_install(
        "fastapi",
        "google-auth",
        "google-genai",
        "gspread",
        "groq",
        "httpx",
        "modal",
        "pinecone",
        "pydub",
        "python-dotenv",
        "websockets",
    )
)

secrets = [modal.Secret.from_name("shruti-secrets")]


