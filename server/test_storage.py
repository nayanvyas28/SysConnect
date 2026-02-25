import os
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

try:
    response = supabase.storage.get_bucket('sysconnect-images')
    print("Storage is accessible:", response)
except Exception as e:
    print("Error querying storage:", e)
    traceback.print_exc()

import requests
print("Pinging:", url)
try:
    r = requests.get(url + "/rest/v1/", timeout=5)
    print("REST GET status:", r.status_code)
except Exception as e:
    print("REST Error:", e)
