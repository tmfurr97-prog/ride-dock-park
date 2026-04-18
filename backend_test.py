"""
Backend tests for DriveShare & Dock — focusing on 3 new tasks:
1. Boat Rentals & Docks category validation (POST /api/listings)
2. Booking fee calculation with add-ons + commission (POST /api/bookings)
3. Seeded boat listing fetchable via GET /api/listings?category=boat_rental
"""
import os
import sys
import json
import uuid
import requests
from datetime import datetime, timedelta

BASE_URL = "https://forest-dock.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@driveshare.com"
ADMIN_PASSWORD = "Admin123!"

results = []  # list of (name, ok, details)


def log(name, ok, details=""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {details}" if details else ""))
    results.append((name, ok, details))


def post(path, json_body=None, token=None, params=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(f"{BASE_URL}{path}", json=json_body, headers=headers, params=params, timeout=30)


def get(path, token=None, params=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=30)


def patch(path, token=None, params=None, json_body=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.patch(f"{BASE_URL}{path}", headers=headers, params=params, json=json_body, timeout=30)


# ======================================================
# Step 0: Admin login
# ======================================================
def admin_login():
    r = post("/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        log("Admin login", False, f"status={r.status_code} body={r.text}")
        return None, None
    data = r.json()
    log("Admin login", True, f"user_id={data['user']['id']}")
    return data["token"], data["user"]


# ======================================================
# Task 3: GET /api/listings?category=boat_rental seeded
# ======================================================
def test_seeded_boat_listing():
    r = get("/listings", params={"category": "boat_rental"})
    if r.status_code != 200:
        log("GET boat_rental listings", False, f"status={r.status_code}")
        return None
    lst = r.json()
    if not isinstance(lst, list) or len(lst) == 0:
        log("GET boat_rental listings returns >=1", False, f"got {lst}")
        return None
    # Look for seeded pontoon
    pontoon = None
    for item in lst:
        if "Blue Water Pontoon" in item.get("title", ""):
            pontoon = item
            break
    if not pontoon:
        log("Seeded 'Blue Water Pontoon' present", False, f"titles: {[i.get('title') for i in lst]}")
        return None

    # verify schema fields
    issues = []
    if pontoon.get("price") != 450 and pontoon.get("price") != 450.0:
        issues.append(f"price={pontoon.get('price')}")
    if not pontoon.get("is_long_term"):
        issues.append(f"is_long_term={pontoon.get('is_long_term')}")
    amen = pontoon.get("amenities", {}) or {}
    if amen.get("life_jackets_count") != 10:
        issues.append(f"life_jackets_count={amen.get('life_jackets_count')}")
    add_ons = amen.get("add_ons", {}) or {}
    for key in ["trailer", "wakeboard_tower", "fishing_gear", "bimini_top"]:
        if key not in add_ons:
            issues.append(f"missing add_on:{key}")
    if issues:
        log("Seeded Blue Water Pontoon schema", False, ", ".join(issues))
        return pontoon
    log("Seeded Blue Water Pontoon present w/ correct schema", True,
        f"price={pontoon['price']}, life_jackets={amen.get('life_jackets_count')}, add_ons={list(add_ons.keys())}")
    return pontoon


# ======================================================
# Task 1: POST /api/listings boat_rental — negatives + happy
# ======================================================
def boat_payload_base():
    return {
        "category": "boat_rental",
        "title": "Test Boat",
        "description": "Test",
        "price": 400.00,
        "location": "Test Lake",
        "images": ["data:image/png;base64,iVBORw0KGgo="],
        "amenities": {
            "boat_type": "Pontoon",
            "length": 22.0,
            "horsepower": 115,
            "capacity": 6,
            "has_dock": True,
            "insurance_proof": "data:image/jpeg;base64,xxx",
            "security_deposit": 400.00,
            "life_jackets_count": 6,
            "add_ons": {
                "trailer": {"available": True, "price_per_day": 50.00, "included_free": False},
                "bimini_top": {"available": True, "price_per_day": 0.00, "included_free": True},
            },
        },
        "is_long_term": True,
    }


def test_boat_validation(admin_token):
    # a. Missing insurance_proof
    p = boat_payload_base()
    p["amenities"].pop("insurance_proof")
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and "insurance" in r.text.lower()
    log("Neg: missing insurance_proof → 400", ok, f"status={r.status_code} body={r.text[:200]}")

    # b. security_deposit = 0
    p = boat_payload_base()
    p["amenities"]["security_deposit"] = 0
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and "deposit" in r.text.lower()
    log("Neg: security_deposit=0 → 400", ok, f"status={r.status_code} body={r.text[:200]}")

    # b2. missing security_deposit
    p = boat_payload_base()
    p["amenities"].pop("security_deposit")
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and "deposit" in r.text.lower()
    log("Neg: missing security_deposit → 400", ok, f"status={r.status_code} body={r.text[:200]}")

    # c. life_jackets_count missing
    p = boat_payload_base()
    p["amenities"].pop("life_jackets_count")
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and "life jacket" in r.text.lower()
    log("Neg: missing life_jackets_count → 400", ok, f"status={r.status_code} body={r.text[:200]}")

    # d. life_jackets < capacity
    p = boat_payload_base()
    p["amenities"]["capacity"] = 8
    p["amenities"]["life_jackets_count"] = 2
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and ("at least" in r.text.lower() or "capacity" in r.text.lower())
    log("Neg: life_jackets(2) < capacity(8) → 400", ok, f"status={r.status_code} body={r.text[:200]}")

    # e. Invalid category string
    p = boat_payload_base()
    p["category"] = "foo"
    r = post("/listings", p, token=admin_token)
    ok = r.status_code == 400 and "category" in r.text.lower()
    log("Neg: invalid category 'foo' → 400", ok, f"status={r.status_code} body={r.text[:200]}")


def test_boat_happy(admin_token):
    p = boat_payload_base()
    r = post("/listings", p, token=admin_token)
    if r.status_code != 200:
        log("Happy: create boat_rental listing", False, f"status={r.status_code} body={r.text[:300]}")
        return None
    data = r.json()
    ok = (
        data.get("id")
        and data.get("category") == "boat_rental"
        and data.get("is_long_term") is True
    )
    log("Happy: create boat_rental listing", ok,
        f"id={data.get('id')} category={data.get('category')} is_long_term={data.get('is_long_term')}")
    return data


# ======================================================
# Task 2: Booking with add-ons
# ======================================================
def get_or_create_verified_guest(admin_token):
    """Register a new user, then admin-verify them."""
    uid = uuid.uuid4().hex[:8]
    email = f"guest_{uid}@example.com"
    password = "GuestPass123!"
    payload = {
        "email": email,
        "password": password,
        "name": f"Guest {uid}",
        "phone": "555-0100",
    }
    r = post("/auth/register", payload)
    if r.status_code != 200:
        log("Register new guest", False, f"status={r.status_code} body={r.text[:200]}")
        return None, None
    data = r.json()
    guest_token = data["token"]
    guest_id = data["user"]["id"]
    log("Register new guest", True, f"email={email} id={guest_id}")

    # Admin verify
    r = patch(f"/admin/users/{guest_id}/verify", token=admin_token)
    if r.status_code != 200:
        log("Admin verify guest", False, f"status={r.status_code} body={r.text[:200]}")
        return None, None
    log("Admin verify guest", True)

    # Re-login to get a fresh token reflecting verification
    r = post("/auth/login", {"email": email, "password": password})
    if r.status_code == 200:
        guest_token = r.json()["token"]
    return guest_token, guest_id


def test_booking_with_add_ons(admin_token, guest_token, guest_id, boat_listing):
    if not boat_listing:
        log("Booking: setup (boat listing created)", False, "No listing to book")
        return
    listing_id = boat_listing["id"]

    start = datetime.utcnow().date() + timedelta(days=10)
    end = start + timedelta(days=3)
    payload = {
        "listing_id": listing_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "selected_add_ons": ["trailer", "bimini_top"],
    }
    r = post("/bookings", payload, token=guest_token)
    if r.status_code != 200:
        log("POST booking with add-ons", False, f"status={r.status_code} body={r.text[:300]}")
        return
    b = r.json()

    def chk(name, cond, details=""):
        log(f"Booking: {name}", bool(cond), details if not cond else "")

    chk("days == 3", b.get("days") == 3, f"got {b.get('days')}")
    chk("base_subtotal == 400*3 = 1200",
        abs(float(b.get("base_subtotal", 0)) - 1200.0) < 0.01,
        f"got {b.get('base_subtotal')}")
    chk("add_ons has 2 entries",
        isinstance(b.get("add_ons"), list) and len(b["add_ons"]) == 2,
        f"got {b.get('add_ons')}")
    add_ons = b.get("add_ons", []) or []
    trailer = next((a for a in add_ons if a.get("key") == "trailer"), None)
    bimini = next((a for a in add_ons if a.get("key") == "bimini_top"), None)
    chk("trailer line_total == 150",
        trailer and abs(float(trailer.get("line_total", 0)) - 150.0) < 0.01,
        f"got {trailer}")
    chk("bimini line_total == 0",
        bimini and abs(float(bimini.get("line_total", 0)) - 0.0) < 0.01,
        f"got {bimini}")
    chk("add_ons_subtotal == 150",
        abs(float(b.get("add_ons_subtotal", 0)) - 150.0) < 0.01,
        f"got {b.get('add_ons_subtotal')}")
    rate = float(b.get("platform_fee_rate", 0))
    chk("platform_fee_rate is 0.10 or 0.15", rate in (0.10, 0.15), f"got {rate}")
    expected_rental_fee = round(1200.0 * rate, 2)
    chk(f"platform_rental_fee == base*rate ({expected_rental_fee})",
        abs(float(b.get("platform_rental_fee", 0)) - expected_rental_fee) < 0.01,
        f"got {b.get('platform_rental_fee')}")
    chk("platform_add_on_fee == 15 (10% of 150)",
        abs(float(b.get("platform_add_on_fee", 0)) - 15.0) < 0.01,
        f"got {b.get('platform_add_on_fee')}")
    expected_fee_total = round(expected_rental_fee + 15.0, 2)
    chk(f"platform_fee_total == {expected_fee_total}",
        abs(float(b.get("platform_fee_total", 0)) - expected_fee_total) < 0.01,
        f"got {b.get('platform_fee_total')}")
    expected_payout = round(1200 + 150 - expected_fee_total, 2)
    chk(f"host_payout == {expected_payout}",
        abs(float(b.get("host_payout", 0)) - expected_payout) < 0.01,
        f"got {b.get('host_payout')}")
    chk("security_deposit == 400",
        abs(float(b.get("security_deposit", 0)) - 400.0) < 0.01,
        f"got {b.get('security_deposit')}")
    chk("total_price == base + add_ons + deposit = 1750",
        abs(float(b.get("total_price", 0)) - (1200 + 150 + 400)) < 0.01,
        f"got {b.get('total_price')}")

    print("\nBooking response:")
    print(json.dumps(b, indent=2, default=str))


def main():
    admin_token, admin_user = admin_login()
    if not admin_token:
        print("FATAL: cannot login admin")
        sys.exit(1)

    test_seeded_boat_listing()
    test_boat_validation(admin_token)
    boat_listing = test_boat_happy(admin_token)

    guest_token, guest_id = get_or_create_verified_guest(admin_token)
    if guest_token:
        test_booking_with_add_ons(admin_token, guest_token, guest_id, boat_listing)

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n====== {passed}/{total} tests passed ======")
    failed = [r for r in results if not r[1]]
    if failed:
        print("Failed:")
        for name, _, details in failed:
            print(f"  - {name} :: {details}")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
