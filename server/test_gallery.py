import urllib.request
import urllib.error

try:
    with urllib.request.urlopen("http://localhost:8000/gallery") as response:
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} {e.reason}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
