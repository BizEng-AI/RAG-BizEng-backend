"""
List all available deployments in your Azure OpenAI account
This will help us find the correct deployment names
"""
import requests
from settings import AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION

print("=" * 70)
print("LISTING AZURE OPENAI DEPLOYMENTS")
print("=" * 70)
print()

# Clean endpoint (remove /openai/ if present)
base_endpoint = AZURE_OPENAI_ENDPOINT.rstrip('/')
if base_endpoint.endswith('/openai'):
    base_endpoint = base_endpoint[:-7]

# List deployments endpoint
url = f"{base_endpoint}/openai/deployments?api-version={AZURE_OPENAI_API_VERSION}"

print(f"Endpoint: {base_endpoint}")
print(f"API Version: {AZURE_OPENAI_API_VERSION}")
print()

headers = {
    "api-key": AZURE_OPENAI_KEY
}

try:
    print("Fetching deployments...")
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()
        deployments = data.get('data', [])

        if not deployments:
            print("⚠️  No deployments found or empty response")
            print(f"Response: {data}")
        else:
            print(f"✅ Found {len(deployments)} deployment(s):")
            print()

            for dep in deployments:
                name = dep.get('id', 'N/A')
                model = dep.get('model', 'N/A')
                status = dep.get('status', 'N/A')
                created = dep.get('created_at', 'N/A')

                print(f"  📦 Deployment Name: {name}")
                print(f"     Model: {model}")
                print(f"     Status: {status}")
                print(f"     Created: {created}")
                print()
    else:
        print(f"❌ Failed to list deployments")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Trying alternative method...")

    # Try a different API version
    for api_ver in ["2024-10-21", "2024-08-01-preview", "2024-06-01", "2023-05-15"]:
        try:
            url = f"{base_endpoint}/openai/deployments?api-version={api_ver}"
            print(f"  Trying API version: {api_ver}")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Success with {api_ver}!")
                data = response.json()
                deployments = data.get('data', [])
                for dep in deployments:
                    print(f"    - {dep.get('id')} ({dep.get('model')})")
                break
            else:
                print(f"    Status: {response.status_code}")
        except:
            pass

print()
print("=" * 70)
print("Update your .env file with the correct deployment names shown above")
print("=" * 70)

