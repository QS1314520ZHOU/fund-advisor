
import requests
import json

API_BASE = "http://localhost:8000"

def test_comparison():
    print("Testing /v1/compare...")
    payload = {
        "codes": ["000001", "000002"]
    }
    try:
        res = requests.post(f"{API_BASE}/v1/compare", json=payload)
        data = res.json()
        if data.get("status") == "success":
            print("✅ Comparison success")
            print(f"   Similarity: {data.get('similarity', {}).get('overlap_ratio')}%")
        else:
            print(f"❌ Comparison failed: {data.get('message')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_diagnose_pro():
    print("\nTesting /v1/diagnose/pro...")
    payload = {
        "funds": [
            {"code": "000001", "weight": 60},
            {"code": "004747", "weight": 40}
        ]
    }
    try:
        res = requests.post(f"{API_BASE}/v1/diagnose/pro", json=payload)
        data = res.json()
        if data.get("status") == "success":
            print("✅ Diagnostics Pro success")
            print(f"   Allocation: {data.get('data', {}).get('allocation')}")
            print(f"   Scenarios: {len(data.get('data', {}).get('scenarios', []))}")
        else:
            print(f"❌ Diagnostics Pro failed: {data.get('message')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_comparison()
    test_diagnose_pro()
