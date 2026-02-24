import requests
import json

def test_phase2_endpoints():
    base_url = "http://localhost:8000/v1"
    
    # 1. Test Market Hotspots (Enhanced)
    print("Testing /v1/market/hotspots...")
    try:
        res = requests.get(f"{base_url}/market/hotspots")
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                sentiment = data.get('sentiment', {})
                print(f"SUCCESS: Market Sentiment: {sentiment.get('fear_greed')} (Score: {sentiment.get('score')})")
                print(f"Breadth: Up {sentiment.get('breadth', {}).get('up')} / Down {sentiment.get('breadth', {}).get('down')}")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"FAILED: {res.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

    # 2. Test Sector Analyze (Deep Dive)
    print("\nTesting /v1/sectors/半导体/analyze...")
    try:
        res = requests.get(f"{base_url}/sectors/半导体/analyze")
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'success':
                info = data.get('data', {})
                print(f"SUCCESS: Sector: {info.get('sector')}")
                print(f"Sentiment: {info.get('sentiment', {}).get('sentiment')} (Ratio: {info.get('sentiment', {}).get('ratio')})")
                print(f"AI Prediction Preview: {info.get('prediction', {}).get('prediction', '')[:100]}...")
            else:
                print(f"API Error: {data.get('message')}")
        else:
            print(f"FAILED: {res.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_phase2_endpoints()
