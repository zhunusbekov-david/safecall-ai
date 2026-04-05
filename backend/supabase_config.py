import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key) if url and key else None

if supabase:
    print("✅ Supabase подключен успешно")
else:
    print("❌ Ошибка подключения к Supabase")