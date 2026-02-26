import requests
try:
    r = requests.get("http://127.0.0.1:8000/dashboard")
    print("Dashboard Response:", r.status_code)
    # Check if TEST-AGENT-001 or any agent is online
    if "Online" in r.text:
       print("SUCCESS: Found 'Online' agents in dashboard!")
    else:
       print("No 'Online' agents found. The client might not be connected properly.")
except Exception as e:
    print("Dashboard Failed:", e)
