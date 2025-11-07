"""
Test different endpoint formats and deployment names
"""
from openai import AzureOpenAI

api_key = "DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb"
api_version = "2024-02-15-preview"

# Test different endpoint formats
endpoints = [
    "https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/",
    "https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/openai/",
    "https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com",
]

# Test different deployment names
deployment_names = [
    "gpt-35-turbo",
    "gpt-4",
    "gpt35turbo",
    "gpt-3.5-turbo",
]

print("=" * 70)
print("TESTING ENDPOINT FORMATS AND DEPLOYMENT NAMES")
print("=" * 70)
print()

found_working = False

for endpoint in endpoints:
    for deployment in deployment_names:
        print(f"Testing: {endpoint} | Deployment: {deployment}")
        try:
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )

            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )

            print(f"  ✅✅✅ SUCCESS!")
            print(f"     Endpoint: {endpoint}")
            print(f"     Deployment: {deployment}")
            print(f"     Response: {response.choices[0].message.content}")
            print()
            print("=" * 70)
            print("WORKING CONFIGURATION FOUND:")
            print(f"  AZURE_OPENAI_ENDPOINT={endpoint}")
            print(f"  AZURE_OPENAI_CHAT_DEPLOYMENT={deployment}")
            print("=" * 70)
            found_working = True
            break

        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                print(f"  ❌ 404 Not Found")
            elif "401" in error_str or "403" in error_str:
                print(f"  ❌ Auth Error")
            else:
                print(f"  ❌ {error_str[:60]}")
        print()

    if found_working:
        break

if not found_working:
    print("\n⚠️  No working configuration found!")
    print("\nPlease check Azure Portal:")
    print("1. Go to Azure OpenAI Studio")
    print("2. Click on 'Deployments' tab")
    print("3. Check the EXACT deployment name shown there")
    print("4. Copy it exactly (including hyphens, case, etc.)")

