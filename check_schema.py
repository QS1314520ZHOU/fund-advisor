import requests
import json

r = requests.get('http://localhost:8000/openapi.json')
openapi = r.json()
schema = openapi['components']['schemas']['WatchlistAddRequest']
print(json.dumps(schema, indent=2))
