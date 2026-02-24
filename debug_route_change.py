import requests
import json

print("Testing OLD route /watchlist/add...")
r = requests.post('http://localhost:8000/watchlist/add', json={"code": "014943", "name": "Test"})
print(f"Status: {r.status_code}")

print("\nTesting NEW route /watchlist/add_debug_123...")
r2 = requests.post('http://localhost:8000/watchlist/add_debug_123', json={"code": "014943", "name": "Test"})
print(f"Status: {r2.status_code}")
try:
    print(r2.json())
except:
    print(r2.text)
