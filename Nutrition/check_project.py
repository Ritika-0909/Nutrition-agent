"""Quick script to find valid IBM Watsonx project IDs under your API key."""
import sys, io, os, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("IBM_API_KEY", "")
if not api_key:
    print("ERROR: IBM_API_KEY not set in .env")
    sys.exit(1)

print("Step 1: Authenticating with IBM Cloud IAM...")
resp = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=15,
)
if resp.status_code != 200:
    print(f"Auth failed ({resp.status_code}): {resp.text[:200]}")
    sys.exit(1)

token = resp.json()["access_token"]
print("Auth: OK")

print("\nStep 2: Listing your IBM Watsonx projects...")
resp2 = requests.get(
    "https://api.dataplatform.cloud.ibm.com/v2/projects",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    timeout=15,
)
print(f"Projects API status: {resp2.status_code}")
data = resp2.json()
projects = data.get("resources", [])

if projects:
    print(f"\nFound {len(projects)} project(s) under your API key:")
    print("-" * 60)
    for p in projects:
        name = p.get("entity", {}).get("name", "Unknown")
        pid  = p.get("metadata", {}).get("guid", "Unknown")
        print(f"  Name: {name}")
        print(f"  ID:   {pid}")
        print(f"  --> Set IBM_PROJECT_ID={pid} in your .env")
        print()
else:
    print("\nNo existing projects found. You need to create one:")
    print("  1. Go to https://dataplatform.cloud.ibm.com")
    print("  2. Click 'New project' -> 'Create an empty project'")
    print("  3. Add your Watson Machine Learning service to the project")
    print("  4. Copy the Project ID from Manage -> General tab")
    print("  5. Set IBM_PROJECT_ID=<id> in your .env file")
    print(f"\nRaw response: {json.dumps(data, indent=2)[:400]}")
