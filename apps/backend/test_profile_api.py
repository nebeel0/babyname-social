"""Quick script to test profile API persistence."""
import asyncio
import httpx

async def test_profile():
    base_url = "http://127.0.0.1:8001"

    test_profile = {
        "user_id": "test-user-123",
        "ethnicity": "White",
        "age": 30,
        "current_state": "CA",
        "current_city": "San Francisco",
        "country": "US",
        "partner_ethnicity": "Asian",
        "existing_children_names": ["Alice", "Bob"],
        "family_surnames": ["Smith", "Johnson"],
        "cultural_importance": 4,
        "uniqueness_preference": 5,
        "traditional_vs_modern": 3,
        "nickname_friendly": True,
        "religious_significance": False,
        "avoid_discrimination_risk": True,
        "pronunciation_simplicity": 5,
        "preferred_name_length": "medium",
        "preferred_origins": ["English", "French"],
        "disliked_sounds": ["harsh-k"],
    }

    async with httpx.AsyncClient() as client:
        print("1. Testing profile creation...")
        response = await client.post(f"{base_url}/api/v1/profiles/", json=test_profile)
        print(f"   Status: {response.status_code}")
        if response.status_code == 201:
            print(f"   Created: {response.json()}")
        elif response.status_code == 400:
            print(f"   Already exists (this is ok), trying to get existing...")
        else:
            print(f"   Error: {response.text}")
            return

        print("\n2. Testing profile retrieval...")
        response = await client.get(f"{base_url}/api/v1/profiles/test-user-123")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Retrieved: {response.json()}")
        elif response.status_code == 404:
            print("   ❌ NOT FOUND - Profile was not persisted!")
        else:
            print(f"   Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_profile())
