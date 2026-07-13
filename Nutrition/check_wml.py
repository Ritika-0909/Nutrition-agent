"""
Scans your IBM Cloud account for all Watson AI / WML resource instances
and tests which project+region combination can actually run inference.
Run: python check_wml.py
"""
import sys, io, os, requests, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("IBM_API_KEY", "")
if not API_KEY:
    print("ERROR: IBM_API_KEY not set in .env")
    sys.exit(1)

# ── Step 1: Get IAM token ────────────────────────────────────────────────────
print("Authenticating with IBM Cloud IAM...")
tok = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": API_KEY},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=15,
)
if tok.status_code != 200:
    print("Auth failed:", tok.text[:200])
    sys.exit(1)
TOKEN = tok.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print("Auth: OK\n")

# ── Step 2: List all resource instances ─────────────────────────────────────
print("Scanning resource instances...")
r = requests.get(
    "https://resource-controller.cloud.ibm.com/v2/resource_instances?limit=100",
    headers=HEADERS, timeout=15
)
resources = r.json().get("resources", [])
print(f"Total resources found: {len(resources)}\n")

wml_instances = []
for res in resources:
    name  = res.get("name", "")
    state = res.get("state", "")
    crn   = res.get("crn", "")
    parts = crn.split(":")
    svc   = parts[4] if len(parts) > 4 else ""
    region = res.get("region_id", parts[5] if len(parts) > 5 else "?")

    is_wml = any(k in svc.lower() for k in ["pm-20", "data-science", "watson-studio",
                                              "machine-learning", "wml"])
    if is_wml:
        wml_instances.append({"name": name, "state": state, "svc": svc,
                               "region": region, "crn": crn})
        status_icon = "✅" if state == "active" else "❌"
        print(f"  {status_icon} [{state:10}] {name}")
        print(f"              service: {svc}")
        print(f"              region:  {region}")
        print()

if not wml_instances:
    print("No Watson ML instances found under this API key.")
    print("\nTo create one:")
    print("  1. Go to https://cloud.ibm.com/catalog/services/watson-machine-learning")
    print("  2. Select the Lite (free) plan")
    print("  3. Click Create")
    print("  4. Then re-run this script")
    sys.exit(0)

# ── Step 3: Test inference on each active region ─────────────────────────────
REGIONS = ["us-south", "eu-de", "eu-gb", "jp-tok", "au-syd"]
PROJECT_ID = os.getenv("IBM_PROJECT_ID", "")
MODEL      = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-1-8b-base")

print("\n" + "="*60)
print("Testing inference endpoints...")
print(f"Project ID: {PROJECT_ID}")
print(f"Model:      {MODEL}")
print("="*60)

working_url = None
for region in REGIONS:
    url = f"https://{region}.ml.cloud.ibm.com"
    test_url = f"{url}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "model_id": MODEL,
        "input": "Hello",
        "parameters": {"max_new_tokens": 5},
        "project_id": PROJECT_ID,
    }
    try:
        resp = requests.post(test_url, headers=HEADERS, json=payload, timeout=15)
        if resp.status_code == 200:
            print(f"  ✅ {region}: WORKING!")
            working_url = url
            result = resp.json()
            generated = result.get("results", [{}])[0].get("generated_text", "")
            print(f"     Test response: {repr(generated[:80])}")
            break
        elif resp.status_code == 404:
            # Try listing supported models for this region
            models_resp = requests.get(
                f"{url}/ml/v1/foundation_model_specs?version=2023-05-29&project_id={PROJECT_ID}",
                headers=HEADERS, timeout=10
            )
            if models_resp.status_code == 200:
                models = [m["model_id"] for m in models_resp.json().get("resources", [])]
                granite_models = [m for m in models if "granite" in m.lower()]
                print(f"  ⚠️  {region}: Project accessible, model '{MODEL}' not found")
                if granite_models:
                    print(f"     Available Granite models: {granite_models[:5]}")
                    print(f"     --> Try: GRANITE_MODEL_ID={granite_models[0]} in .env")
                    working_url = f"CHANGE_MODEL:{granite_models[0]}:{url}"
            else:
                print(f"  ❌ {region}: {resp.status_code} — {resp.text[:100]}")
        elif resp.status_code == 403:
            body = resp.json()
            err_code = body.get("errors", [{}])[0].get("code", "")
            if err_code == "invalid_instance_status_error":
                print(f"  ❌ {region}: WML instance INACTIVE")
            else:
                print(f"  ❌ {region}: 403 — {err_code}")
        else:
            print(f"  ❌ {region}: {resp.status_code} — {resp.text[:120]}")
    except Exception as ex:
        print(f"  ❌ {region}: connection error — {ex}")

print()
if working_url and not working_url.startswith("CHANGE_MODEL"):
    print("="*60)
    print("ACTION: Update your .env with these working values:")
    print(f"  IBM_WATSONX_URL={working_url}")
    print(f"  IBM_PROJECT_ID={PROJECT_ID}")
    print(f"  GRANITE_MODEL_ID={MODEL}")
    print("Then restart: python app.py")
elif working_url and working_url.startswith("CHANGE_MODEL"):
    _, new_model, new_url = working_url.split(":", 2)
    print("="*60)
    print("ACTION: Update your .env with these values:")
    print(f"  IBM_WATSONX_URL={new_url}")
    print(f"  IBM_PROJECT_ID={PROJECT_ID}")
    print(f"  GRANITE_MODEL_ID={new_model}")
    print("Then restart: python app.py")
else:
    print("="*60)
    print("No working endpoint found.")
    print()
    print("Most likely cause: Your WML service instance is INACTIVE.")
    print()
    print("To fix:")
    print("  1. Go to https://cloud.ibm.com/resources")
    print("  2. Find 'Watson Machine Learning' in the list")
    print("  3. Click the 3-dot menu -> Resume  (or upgrade plan)")
    print("  4. Wait 2 minutes, then run: python check_wml.py again")
    print()
    print("  OR create a fresh WML instance:")
    print("  1. Go to https://cloud.ibm.com/catalog/services/watson-machine-learning")
    print("  2. Choose Lite (free) plan, click Create")
    print("  3. In your Watsonx project: Manage -> Services -> Add WML service")
    print("  4. Run: python check_wml.py again")
