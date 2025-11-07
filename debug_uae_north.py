"""
Debug UAE North endpoint - try different configurations
"""
from openai import AzureOpenAI

embed_key = "9fyw2LxxdqRgay7cAuK84FXP7TwWMm1HC2QOMy5u5oeKKVt8lyTdJQQJ99BJACF24PCXJ3w3AAAAACOGMrGx"
embed_deployment = "text-embedding-3-small"

# Try different endpoint formats
endpoints = [
    "https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com/",
    "https://sanja-mh6697hv-uaenorth.cognitiveservices.azure.com",
    "https://sanja-mh6697hv-uaenorth.openai.azure.com/",
    "https://sanja-mh6697hv-uaenorth.openai.azure.com",
]

# Try different API versions
api_versions = [
    "2024-02-15-preview",
    "2024-08-01-preview",
    "2023-05-15",
]

print("=" * 70)
print("DEBUGGING UAE NORTH EMBEDDINGS")
print("=" * 70)
print()

for endpoint in endpoints:
    for api_version in api_versions:
        print(f"Testing: {endpoint} | API v{api_version}")
        try:
            client = AzureOpenAI(
                api_key=embed_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )

            response = client.embeddings.create(
                model=embed_deployment,
                input="Test"
            )

            print(f"  ✅✅✅ SUCCESS!")
            print(f"     Endpoint: {endpoint}")
            print(f"     API Version: {api_version}")
            print(f"     Deployment: {embed_deployment}")
            print(f"     Dimension: {len(response.data[0].embedding)}")
            print()
            print("=" * 70)
            print(f"WORKING CONFIGURATION:")
            print(f"AZURE_OPENAI_EMBEDDING_ENDPOINT={endpoint}")
            print(f"AZURE_OPENAI_API_VERSION={api_version}")
            print("=" * 70)
            exit(0)

        except Exception as e:
            error_str = str(e)
            if "401" in error_str:
                print(f"  ❌ 401 Auth Error")
            elif "404" in error_str:
                print(f"  ❌ 404 Not Found")
            else:
                print(f"  ❌ {error_str[:60]}")
        print()

print("\n⚠️  No working configuration found!")
print("\nPossible issues:")
print("1. The API key might be incorrect - please double-check in Azure Portal")
print("2. The deployment name might be different")
print("3. The resource might be in a different region")
print("\nPlease verify in Azure Portal:")
print("- Resource: sanja-mh6697hv-uaenorth")
print("- Keys and Endpoint section")
print("- Deployments tab for exact deployment name")

