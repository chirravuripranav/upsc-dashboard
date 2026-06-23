import requests

token = "8923503008:AAEbH79aNXG43xeg9pwvIjVsK8RpxqYQE2I"
url = f"https://api.telegram.org/bot{token}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    print(data)
except Exception as e:
    print(f"Error: {e}")
