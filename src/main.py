from pathlib import Path
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
    .add_local_python_source("src")
)

env_path = Path(__file__).parent.parent / ".env"
secrets = [modal.Secret.from_dotenv(env_path)]
