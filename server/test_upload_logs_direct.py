import requests
from datetime import datetime, timezone
dt = datetime.now(timezone.utc)

payload = [{
    "log_type": "window",
    "content": {"title": "Test Window", "duration": 45},
    "timestamp": dt.isoformat()
}]

try:
    r = requests.post(
        "http://127.0.0.1:8000/agent/upload/logs", 
        params={"hostname": "TEST-AGENT-001"},
        json=payload
    )
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Request Failed: {e}")
