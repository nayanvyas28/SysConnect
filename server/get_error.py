import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/dashboard')
    print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"Error code: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Other error: {e}")
