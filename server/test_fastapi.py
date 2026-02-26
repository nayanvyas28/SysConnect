import traceback
from fastapi.testclient import TestClient
from main import app

print("Testing dashboard:")
try:
    client = TestClient(app)
    response = client.get("/dashboard")
    print("Status:", response.status_code)
    if response.status_code == 500:
        print(response.text)
except Exception as e:
    traceback.print_exc()
