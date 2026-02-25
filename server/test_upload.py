import requests
import asyncio
import os
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000"

async def test_all():
    print("1. Testing Agent Registration...")
    agent_data = {
        "hostname": "TEST-AGENT-001",
        "ip_address": "192.168.1.100"
    }
    try:
        r = requests.post(f"{BASE_URL}/agent/register", json=agent_data)
        print(f"Agent Register Response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Agent Register Failed: {e}")

    print("\n2. Testing Log Upload...")
    logs_data = [
        {
            "log_type": "window",
            "content": {"title": "Test Window", "duration": 45},
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "log_type": "url",
            "content": {"url": "https://example.com"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    try:
        r = requests.post(
            f"{BASE_URL}/agent/upload/logs", 
            params={"hostname": "TEST-AGENT-001"},
            json=logs_data
        )
        print(f"Log Upload Response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Log Upload Failed: {e}")

    print("\n3. Testing Screenshot Upload...")
    try:
        # Create a dummy image file
        with open("dummy_test.jpg", "wb") as f:
            f.write(os.urandom(1024 * 10)) # 10KB junk data
            
        with open("dummy_test.jpg", "rb") as f:
            files = {"file": ("dummy_test.jpg", f, "image/jpeg")}
            data = {"hostname": "TEST-AGENT-001"}
            r = requests.post(f"{BASE_URL}/agent/upload/screenshot", data=data, files=files)
            print(f"Screenshot Upload Response: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Screenshot Upload Failed: {e}")
    finally:
        if os.path.exists("dummy_test.jpg"):
            os.remove("dummy_test.jpg")

if __name__ == "__main__":
    asyncio.run(test_all())
