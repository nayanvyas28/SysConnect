import requests
try:
    r = requests.get("http://127.0.0.1:8001/dashboard")
    print("Dashboard Response:", r.status_code)
except Exception as e:
    print("Dashboard Failed:", e)

try:
    r = requests.get("http://127.0.0.1:8001/gallery")
    print("Gallery Response:", r.status_code)
except Exception as e:
    print("Gallery Failed:", e)
