import urllib.request

try:
    with urllib.request.urlopen("http://localhost:8000/dashboard") as response:
        html = response.read().decode('utf-8')
        print(html)
except Exception as e:
    print(f"Error: {e}")
