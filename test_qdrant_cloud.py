"""
Test Qdrant Cloud connection
"""
import requests

QDRANT_URL = "https://bizeng-cluster-3f7c04d8-1cbf-4c2b-8cd7-f6b7b3e75b0c.eu-central-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.JqQKtcPaZgl-zLwfngmGn-f5oAzghkNtZP6Tv1EfHKY"

print(f"Testing connection to: {QDRANT_URL}")
print(f"Using API key: {QDRANT_API_KEY[:20]}...")

try:
    response = requests.get(
        f"{QDRANT_URL}/collections",
        headers={"api-key": QDRANT_API_KEY},
        timeout=10
    )

    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200:
        print("\n✅ SUCCESS! Connection working!")
        collections = response.json()
        print(f"Collections: {collections}")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")

