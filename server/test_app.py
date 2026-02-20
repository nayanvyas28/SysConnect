from fastapi.testclient import TestClient
from main import app
import traceback

try:
    with TestClient(app) as client:
        response = client.get("/dashboard")
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error Content: {response.text}")
except Exception as e:
    traceback.print_exc()
