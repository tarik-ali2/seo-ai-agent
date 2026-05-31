import requests, json, time

BASE = "http://localhost:8000"

r = requests.post(f"{BASE}/api/auth/login", data={"username": "lpmoon", "password": "lpmoon123"})
token = r.json().get("access_token")
print("Token:", token[:30] + "..." if token else "FAILED - login")
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Start endpoint now returns audit_id
r = requests.post(f"{BASE}/api/competitor/start", headers=headers, json={
    "our_url": "https://bechdu.in",
    "competitor_url": "https://www.cashify.in"
})
resp = r.json()
print("\nStart response:", json.dumps(resp, indent=2))

audit_id = resp.get("audit_id")
if not audit_id:
    print("ERROR: No audit_id returned!")
    exit(1)

print(f"\nPolling status for audit {audit_id}...")
for i in range(60):
    time.sleep(5)
    sr = requests.get(f"{BASE}/api/audit/{audit_id}/status", headers=headers).json()
    print(f"  [{i*5}s] status={sr['status']} progress={sr.get('progress')}% msg={sr.get('progress_message','')}")
    if sr["status"] in ("completed", "failed"):
        break

if sr["status"] == "completed":
    print("\nFetching results...")
    rr = requests.get(f"{BASE}/api/audit/{audit_id}/results", headers=headers).json()
    sugg = rr.get("suggestions", {})
    print("our_domain:", sugg.get("our_domain"))
    print("competitor_domain:", sugg.get("competitor_domain"))
    print("verdict:", sugg.get("verdict"))
    print("keyword_gap count:", len(sugg.get("keyword_gap", [])))
    print("opportunities count:", len(sugg.get("opportunities", [])))
    print("\nSUCCESS! All data retrieved correctly.")
else:
    print("FAILED:", sr.get("progress_message"))
