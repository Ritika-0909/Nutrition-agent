"""
Checks the IBM Cloud WML instance status and reactivation options.
Run: python check_wml_status.py
"""
import sys, io, os, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("IBM_API_KEY", "")
tok = requests.post("https://iam.cloud.ibm.com/identity/token",
    data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":API_KEY},
    headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=15)
TOKEN   = tok.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print("Auth: OK\n")

# List resource instances — find WML
resp = requests.get(
    "https://resource-controller.cloud.ibm.com/v2/resource_instances?limit=100",
    headers=HEADERS, timeout=15)
resources = resp.json().get("resources", [])

print("All WML / Watson AI instances:")
print("-" * 70)
for r in resources:
    crn   = r.get("crn","")
    parts = crn.split(":")
    svc   = parts[4] if len(parts)>4 else ""
    if not any(k in svc.lower() for k in ["pm-20","data-science","watson-studio","machine-learning"]):
        continue
    name   = r.get("name","")
    state  = r.get("state","")
    guid   = r.get("guid","")
    region = r.get("region_id", parts[5] if len(parts)>5 else "?")
    plan   = r.get("resource_plan_id","")
    icon   = "✅" if state=="active" else "❌"
    print(f"  {icon}  {name}")
    print(f"      state:  {state}")
    print(f"      guid:   {guid}")
    print(f"      region: {region}")
    print(f"      plan:   {plan}")
    print(f"      svc:    {svc}")

    # If WML instance is inactive, show the resume URL
    if state != "active" and "pm-20" in svc:
        print(f"\n  *** THIS IS THE INACTIVE WML INSTANCE ***")
        print(f"  To reactivate:")
        print(f"    1. Open: https://cloud.ibm.com/resources")
        print(f"    2. Click on '{name}'")
        print(f"    3. The plan is likely expired — upgrade to a paid/lite plan")
        print(f"       OR create a NEW Watson Machine Learning (Lite) instance:")
        print(f"       https://cloud.ibm.com/catalog/services/watson-machine-learning")
        print(f"    4. Associate the new instance with your project:")
        print(f"       dataplatform.cloud.ibm.com -> Ritika's sandbox")
        print(f"       -> Manage -> Services & integrations -> Associate service")
        print(f"    5. Run: python fix_wml.py")
    print()

print("-" * 70)
print("\nSUMMARY:")
print("The sandbox project (25fcf521) is in us-south and has WML instance")
print("8ff7945f linked — but that WML instance is INACTIVE.")
print()
print("FASTEST FIX:")
print("  1. Open https://cloud.ibm.com/catalog/services/watson-machine-learning")
print("  2. Select 'Lite' plan (free)")
print("  3. Select region: 'Dallas (us-south)'")
print("  4. Click Create")
print("  5. Then in your project (dataplatform.cloud.ibm.com):")
print("     Ritika's sandbox -> Manage -> Services & integrations")
print("     -> Associate service -> select your new WML instance")
print("  6. Run: python fix_wml.py")
