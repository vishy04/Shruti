import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# env key might be gone, me use empty string fallback so url and key not none.
url: str = os.environ.get("SUPABASE_URL") or ""
key: str = os.environ.get("SUPABASE_KEY") or ""

supabase: Client = create_client(url, key)

