"""
Exhaustive scan: tests every project × every region × best available model.
Patches .env automatically when a working combo is found.
Run: python fix_wml.py
"""
import sys, io, os, requests, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("IBM_API_KEY", "")
if not API_KEY:
    print("ERROR: IBM_API_KEY not set in .env"); sys.exit(1)

# ── Auth ──────────────────────────────────────────────────────────────────────
tok = requests.post("https://iam.cloud.ibm.com/identity/token",
    data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":API_KEY},
    headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=15)
if tok.status_code != 200:
    print("Auth failed:", tok.text[:200]); sys.exit(1)
TOKEN   = tok.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print("Auth: OK\n")

# ── Get all projects ──────────────────────────────────────────────────────────
proj_resp = requests.get("https://api.dataplatform.cloud.ibm.com/v2/projects?limit=100",
    headers=HEADERS, timeout=15)
projects = proj_resp.json().get("resources", [])
print(f"Projects found: {len(projects)}")
for p in projects:
    print(f"  - {p['entity']['name']}  ({p['metadata']['guid']})")
print()

# ── All regions to try ────────────────────────────────────────────────────────
REGIONS = ["us-south", "eu-de", "eu-gb", "jp-tok", "au-syd", "ca-tor", "br-sao"]

# ── Preferred models (in priority order) ─────────────────────────────────────
PREFERRED_MODELS = [
    "ibm/granite-3-2-8b-instruct",
    "ibm/granite-3-1-8b-instruct",
    "ibm/granite-3-0-8b-instruct",
    "ibm/granite-13b-instruct-v2",
    "ibm/granite-13b-instruct-v1",
    "ibm/granite-3-1-8b-base",
    "ibm/granite-4-h-small",
    "ibm/granite-7b-lab",
    "meta-llama/llama-3-3-70b-instruct",
    "meta-llama/llama-3-1-8b",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
]

print("="*64)
print("Testing all region × project combinations...")
print("="*64)

working = None
for region in REGIONS:
    base = f"https://{region}.ml.cloud.ibm.com"

    # First: get available models in this region (no project needed)
    models_resp = requests.get(
        f"{base}/ml/v1/foundation_model_specs?version=2023-05-29&limit=200",
        headers=HEADERS, timeout=10)
    if models_resp.status_code != 200:
        print(f"\n[{region}] Cannot list models ({models_resp.status_code}) — skipping")
        continue

    region_models = [m["model_id"] for m in models_resp.json().get("resources", [])]
    # Pick best model available in this region
    model = next((m for m in PREFERRED_MODELS if m in region_models), None)
    if not model:
        print(f"\n[{region}] No suitable model found — skipping")
        continue

    print(f"\n[{region}] model={model}")

    for p in projects:
        pid   = p["metadata"]["guid"]
        pname = p["entity"]["name"]

        resp = requests.post(
            f"{base}/ml/v1/text/generation?version=2023-05-29",
            headers=HEADERS,
            json={"model_id": model, "input": "Hi", "parameters": {"max_new_tokens": 5}, "project_id": pid},
            timeout=20)

        if resp.status_code == 200:
            text = resp.json().get("results", [{}])[0].get("generated_text", "").strip()
            print(f"  ✅  '{pname}' -> WORKS!  reply={repr(text[:60])}")
            working = {"url": base, "project_id": pid, "project_name": pname,
                       "model": model, "region": region}
            break
        else:
            body   = resp.json()
            err    = body.get("errors", [{}])[0]
            code   = err.get("code", str(resp.status_code))
            detail = err.get("message", "")[:70]
            print(f"  ❌  '{pname}' -> {code}: {detail}")

    if working:
        break

# ── Result ────────────────────────────────────────────────────────────────────
print("\n" + "="*64)
if working:
    print("SUCCESS! Patching .env with working configuration...")
    env_path = ".env"
    content  = open(env_path, encoding="utf-8").read()
    content  = re.sub(r"^IBM_WATSONX_URL=.*$",  f"IBM_WATSONX_URL={working['url']}",         content, flags=re.M)
    content  = re.sub(r"^IBM_PROJECT_ID=.*$",   f"IBM_PROJECT_ID={working['project_id']}",    content, flags=re.M)
    content  = re.sub(r"^GRANITE_MODEL_ID=.*$", f"GRANITE_MODEL_ID={working['model']}",       content, flags=re.M)
    open(env_path, "w", encoding="utf-8").write(content)

    print(f"\n  IBM_WATSONX_URL  = {working['url']}")
    print(f"  IBM_PROJECT_ID   = {working['project_id']}  ({working['project_name']})")
    print(f"  GRANITE_MODEL_ID = {working['model']}")
    print("\n.env patched! Now restart:  python app.py")
else:
    print("No working combination found across all regions.")
    print()
    print("Root cause: None of your 3 projects are linked to an active WML service.")
    print()
    print("REQUIRED ACTION (3 minutes):")
    print()
    print("  1. Go to https://dataplatform.cloud.ibm.com")
    print("  2. Open any project (e.g. 'Ritika's sandbox')")
    print("  3. Click  Manage  tab  ->  Services & integrations")
    print("  4. Click  Associate service  ->  select 'watsonx.ai Runtime-nx'")
    print("  5. Click  Associate")
    print("  6. Run:  python fix_wml.py")
    print()
    print("  If you don't see 'watsonx.ai Runtime-nx' in the list:")
    print("  -> Go to https://cloud.ibm.com/resources")
    print("  -> Click on 'watsonx.ai Runtime-nx'")
    print("  -> Click 'Launch in IBM Cloud Pak for Data'")
    print("  -> This wakes it up, then retry step 3 above")
