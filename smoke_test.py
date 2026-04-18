#!/usr/bin/env python3
"""Quick regression smoke test after major dependency upgrade."""
import requests
import uuid
import sys

BASE = "https://forest-dock.preview.emergentagent.com/api"
results = []

def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}: {name} | {detail}")

# Test 1: Admin login
try:
    r = requests.post(f"{BASE}/auth/login",
                      json={"email": "admin@driveshare.com", "password": "Admin123!"},
                      timeout=30)
    ok = r.status_code == 200 and "token" in (r.json() if r.headers.get("content-type","").startswith("application/json") else {})
    record("1. POST /auth/login admin", ok, f"status={r.status_code} body_keys={list(r.json().keys()) if r.status_code==200 else r.text[:200]}")
except Exception as e:
    record("1. POST /auth/login admin", False, f"exc={e}")

# Test 2: GET /listings - at least 6 including Blue Water Pontoon
try:
    r = requests.get(f"{BASE}/listings", timeout=30)
    if r.status_code == 200:
        data = r.json()
        titles = [l.get("title","") for l in data]
        has_blue = any("Blue Water Pontoon" in t for t in titles)
        ok = len(data) >= 6 and has_blue
        record("2. GET /listings (>=6, Blue Water Pontoon)", ok,
               f"count={len(data)} has_blue={has_blue} sample_titles={titles[:8]}")
    else:
        record("2. GET /listings", False, f"status={r.status_code} body={r.text[:200]}")
except Exception as e:
    record("2. GET /listings", False, f"exc={e}")

# Test 3: GET /listings?category=boat_rental - at least 1
try:
    r = requests.get(f"{BASE}/listings", params={"category": "boat_rental"}, timeout=30)
    if r.status_code == 200:
        data = r.json()
        ok = len(data) >= 1 and all(l.get("category") == "boat_rental" for l in data)
        record("3. GET /listings?category=boat_rental (>=1)", ok,
               f"count={len(data)} categories={list({l.get('category') for l in data})}")
    else:
        record("3. GET /listings?category=boat_rental", False, f"status={r.status_code}")
except Exception as e:
    record("3. GET /listings?category=boat_rental", False, f"exc={e}")

# Test 4: Register with fresh email + accepted_tos=true
fresh_email = f"smoke_{uuid.uuid4().hex[:10]}@example.com"
try:
    r = requests.post(f"{BASE}/auth/register",
                      json={"email": fresh_email, "password": "SmokeTest123!",
                            "name": "Smoke Regression", "phone": "555-0100",
                            "accepted_tos": True},
                      timeout=30)
    ok = r.status_code == 200 and "token" in r.json()
    record("4. POST /auth/register (accepted_tos=true)", ok,
           f"status={r.status_code} email={fresh_email}")
except Exception as e:
    record("4. POST /auth/register (accepted_tos=true)", False, f"exc={e}")

# Test 5: Register without accepted_tos -> 400
fresh_email2 = f"smoke_{uuid.uuid4().hex[:10]}@example.com"
try:
    r = requests.post(f"{BASE}/auth/register",
                      json={"email": fresh_email2, "password": "SmokeTest123!",
                            "name": "Smoke No ToS", "phone": "555-0101"},
                      timeout=30)
    ok = r.status_code == 400
    record("5. POST /auth/register (no accepted_tos -> 400)", ok,
           f"status={r.status_code} body={r.text[:200]}")
except Exception as e:
    record("5. POST /auth/register (no accepted_tos)", False, f"exc={e}")

print("\n=== SMOKE TEST SUMMARY ===")
passed = sum(1 for _,ok,_ in results if ok)
print(f"Passed: {passed}/{len(results)}")
for name, ok, detail in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
sys.exit(0 if passed == len(results) else 1)
