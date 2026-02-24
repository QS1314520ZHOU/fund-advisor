import requests
import json

try:
    r = requests.get('http://localhost:8000/openapi.json')
    if r.status_code == 200:
        openapi = r.json()
        path_info = openapi['paths'].get('/watchlist/add', {})
        print("Path info for /watchlist/add:")
        print(json.dumps(path_info, indent=2))
        
        # Also look for the schema
        schema_ref = path_info['post']['requestBody']['content']['application/json']['schema']['$ref']
        schema_name = schema_ref.split('/')[-1]
        schema = openapi['components']['schemas'].get(schema_name, {})
        print(f"\nSchema {schema_name}:")
        print(json.dumps(schema, indent=2))
    else:
        print(f"Failed to fetch openapi.json: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
