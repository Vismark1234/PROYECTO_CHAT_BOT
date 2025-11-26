import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL and Key must be set in environment variables")

supabase: Client = create_client(url, key)

def fetch_table_data(table_name: str):
    """Fetch all data from a table."""
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
        return []

def update_embedding(table_name: str, row_id: int, embedding: list):
    """Update embedding for a specific row."""
    try:
        supabase.table(table_name).update({"embedding": embedding}).eq("id", row_id).execute()
    except Exception as e:
        print(f"Error updating embedding for {table_name} id {row_id}: {e}")
