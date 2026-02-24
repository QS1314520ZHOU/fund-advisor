import requests
import json

r = requests.get('http://localhost:8000/openapi.json')
openapi = r.json()
schema = openapi['components']['schemas'].get('WatchlistAddRequest', {})
print(f"Schema Name: WatchlistAddRequest")
print(f"Required fields: {schema.get('required', [])}")
for prop, details in schema.get('properties', {}).items():
    print(f"Field: {prop}, Type: {details.get('type')}, Title: {details.get('title')}")
