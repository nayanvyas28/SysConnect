import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

try:
    response = supabase.table('agents').select('*').limit(1).execute()
    print("Agents table exists:", response.data)
except Exception as e:
    print("Error querying agents:", e)

try:
    response = supabase.table('activity_logs').select('*').limit(1).execute()
    print("ActivityLogs table exists:", response.data)
except Exception as e:
    print("Error querying activity_logs:", e)
