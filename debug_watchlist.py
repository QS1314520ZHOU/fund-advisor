import requests
import json

payload = {"code": "014943", "name": "Test Fund"}
r = requests.post('http://localhost:8000/watchlist/add', json=payload)
print(f"Status: {r.status_code}")
try:
    print(json.dumps(r.json(), indent=2))
except:
    print(r.text)
