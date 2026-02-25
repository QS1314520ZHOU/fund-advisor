import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_fee_calculate():
    print("Testing /fee/calculate...")
    async with httpx.AsyncClient() as client:
        params = {"amount": 100000, "years": 5, "rate": 1.5}
        try:
            response = await client.get(f"{BASE_URL}/fee/calculate", params=params)
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["success"] is True
            assert "fee_loss" in data["data"]
            print("✅ Fee calculation test passed")
        except Exception as e:
            print(f"❌ Fee calculation test failed: {e}")

async def test_notifications():
    print("\nTesting /notifications...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/notifications")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            assert data["success"] is True
            print("✅ Notifications test passed")
        except Exception as e:
            print(f"❌ Notifications test failed: {e}")

async def main():
    print("Starting API Verification...")
    await test_fee_calculate()
    await test_notifications()
    print("\nVerification Finished.")

if __name__ == "__main__":
    asyncio.run(main())
