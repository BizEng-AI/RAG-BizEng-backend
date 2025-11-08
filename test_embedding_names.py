"""
Test different embedding deployment names
"""
from openai import AzureOpenAI

api_key = "DuQJzDcQmb9siNeUiiUsgaENRgewWHd9FLM4dJd0FJdQe9SAulRhJQQJ99BJACfhMk5XJ3w3AAAAACOGDSnb"
endpoint = "https://sanja-mh654t02-swedencentral.cognitiveservices.azure.com/"
api_version = "2024-02-15-preview"

# Test different embedding deployment names
deployment_names = [
    "embedding-small",
    "text-embedding-3-small",
    "text-embedding-ada-002",
    "embedding",
    "embeddings",
    "ada",
    "text-embedding-3-large",
]

print("=" * 70)
print("TESTING EMBEDDING DEPLOYMENT NAMES")
print("=" * 70)
print()

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint
)

for deployment in deployment_names:
    print(f"Testing deployment: {deployment}")
    try:
        response = client.embeddings.create(
            model=deployment,
            input="Test sentence"
        )

        embedding = response.data[0].embedding
        print(f"  ✅✅✅ SUCCESS!")
        print(f"     Deployment: {deployment}")
        print(f"     Dimension: {len(embedding)}")
        print(f"     Model: {response.model}")
        print()
        print("=" * 70)
        print(f"WORKING EMBEDDING DEPLOYMENT: {deployment}")
        print("=" * 70)
        break

    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "DeploymentNotFound" in error_str:
            print(f"  ❌ Not Found")
        else:
            print(f"  ❌ {error_str[:60]}")
    print()

print("\nIf none worked, check Azure Portal > Deployments for the exact name")

