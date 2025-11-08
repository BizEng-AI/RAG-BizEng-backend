"""
Test different API versions to find which one works
"""
from openai import AzureOpenAI
from settings import AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT

print("=" * 70)
print("TESTING DIFFERENT API VERSIONS")
print("=" * 70)
print()

# Common API versions to try
api_versions = [
    "2024-10-21",
    "2024-08-01-preview",
    "2024-06-01",
    "2024-02-15-preview",
    "2023-12-01-preview",
    "2023-05-15"
]

chat_deployment = "gpt-35-turbo"
test_message = "Say 'OK' if you can hear me."

for api_version in api_versions:
    print(f"Testing API version: {api_version}")
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=api_version,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        response = client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {"role": "user", "content": test_message}
            ],
            max_tokens=10
        )

        print(f"  ✅ SUCCESS with {api_version}!")
        print(f"     Response: {response.choices[0].message.content}")
        print(f"     Model: {response.model}")
        print()
        print("=" * 70)
        print(f"USE THIS API VERSION: {api_version}")
        print("=" * 70)
        break

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"  ❌ 404 - Not Found")
        elif "401" in error_msg:
            print(f"  ❌ 401 - Authentication Error")
        elif "DeploymentNotFound" in error_msg or "deployment" in error_msg.lower():
            print(f"  ❌ Deployment not found")
        else:
            print(f"  ❌ {error_msg[:80]}")
    print()

print("\nIf none worked, the deployment name 'gpt-35-turbo' might be incorrect.")

