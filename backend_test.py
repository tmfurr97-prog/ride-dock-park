"""
Backend tests for DriveShare & Dock "Legal Armor" features:
1. ToS Acceptance on Registration
2. ToS Acceptance on Booking
3. RV Listing requires Proof of Insurance
4. Insurance Gate (awaiting_insurance_review + accept/reject)

Uses public REACT_APP_BACKEND_URL and admin credentials from
/app/memory/test_credentials.md.
"""
import os
import sys
import uuid
import requests
from datetime import datetime, timedelta

FRONTEND_ENV = "/app/frontend/.env"
BACKEND_URL = None
with open(FRONTEND_ENV) as f:
    for line in f:
        line = line.strip()
        for key in ("REACT_APP_BACKEND_URL=", "EXPO_PUBLIC_BACKEND_URL="):
            if line.startswith(key):
                BACKEND_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
        if BACKEND_URL:
            break
if not BACKEND_URL:
    print("FATAL: could not read BACKEND_URL from frontend/.env")
    sys.exit(1)

API = f"{BACKEND_URL.rstrip('/')}/api"
print(f"API base: {API}")

ADMIN_EMAIL = "admin@driveshare.com"
ADMIN_PASSWORD = "Admin123!"

results = []

def record(name, ok, detail=""):
    results.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} :: {detail}")

def uniq_email(prefix="user"):
    return f"{prefix}+{uuid.uuid4().hex[:10]}@driveshare-test.com"

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. ToS Acceptance on Registration
# ---------------------------------------------------------------------------
print("\n=== 1. ToS Acceptance on Registration ===")

email_a = uniq_email("reg_notos")
r = requests.post(f"{API}/auth/register", json={
    "email": email_a,
    "password": "StrongPass!23",
    "name": "Alice Reg",
    "phone": "555-0101",
})
try:
    detail = r.json().get("detail", "")
except Exception:
    detail = r.text
ok = r.status_code == 400 and "Terms of Service" in str(detail)
record("1a register WITHOUT accepted_tos -> 400", ok,
       f"status={r.status_code} detail={detail!r}")

email_b = uniq_email("reg_tosfalse")
r = requests.post(f"{API}/auth/register", json={
    "email": email_b,
    "password": "StrongPass!23",
    "name": "Bob Reg",
    "phone": "555-0102",
    "accepted_tos": False,
})
try:
    detail = r.json().get("detail", "")
except Exception:
    detail = r.text
ok = r.status_code == 400 and "Terms of Service" in str(detail)
record("1b register with accepted_tos=false -> 400", ok,
       f"status={r.status_code} detail={detail!r}")

email_c = uniq_email("reg_ok")
r = requests.post(f"{API}/auth/register", json={
    "email": email_c,
    "password": "StrongPass!23",
    "name": "Carol Ready",
    "phone": "555-0103",
    "accepted_tos": True,
})
ok = False
detail = ""
if r.status_code == 200:
    data = r.json()
    ok = "token" in data and "user" in data and data["user"].get("email") == email_c
    detail = f"token_present={'token' in data} user_email={data.get('user',{}).get('email')}"
else:
    detail = f"status={r.status_code} body={r.text[:200]}"
record("1c register with accepted_tos=true -> 200", ok, detail)


# ---------------------------------------------------------------------------
# Admin login
# ---------------------------------------------------------------------------
print("\n=== Admin login ===")
admin_token = None
admin_user_id = None
r = requests.post(f"{API}/auth/login", json={
    "email": ADMIN_EMAIL,
    "password": ADMIN_PASSWORD,
})
if r.status_code == 200:
    admin_token = r.json()["token"]
    admin_user_id = r.json()["user"]["id"]
    record("admin login", True, f"user_id={admin_user_id}")
else:
    record("admin login", False, f"status={r.status_code} body={r.text[:300]}")


# ---------------------------------------------------------------------------
# 2. ToS Acceptance on Booking
# ---------------------------------------------------------------------------
print("\n=== 2. ToS Acceptance on Booking ===")

fresh_guest_token = None
fresh_guest_id = None
fresh_guest_email = uniq_email("guest")
if admin_token:
    r = requests.post(f"{API}/auth/register", json={
        "email": fresh_guest_email,
        "password": "StrongPass!23",
        "name": "Guest Gamma",
        "phone": "555-0200",
        "accepted_tos": True,
    })
    if r.status_code == 200:
        fresh_guest_token = r.json()["token"]
        fresh_guest_id = r.json()["user"]["id"]
        vr = requests.patch(
            f"{API}/admin/users/{fresh_guest_id}/verify",
            headers=auth_headers(admin_token),
        )
        record("register+verify fresh guest", vr.status_code == 200,
               f"verify_status={vr.status_code} body={vr.text[:200]}")
    else:
        record("register+verify fresh guest", False,
               f"register_status={r.status_code} body={r.text[:200]}")

public_listings = requests.get(f"{API}/listings").json()
land_or_storage_listing = None
# IMPORTANT: seeded land/storage listings carry synthetic owner_ids like "seed_user_5"
# which are NOT valid Mongo ObjectIds, so the booking endpoint crashes
# (host lookup uses ObjectId(listing["owner_id"])). We therefore create a
# fresh land_stay listing as admin so that owner_id is a valid ObjectId.
for l in public_listings:
    if l.get("category") in ("land_stay", "vehicle_storage") and l.get("owner_id") != fresh_guest_id:
        try:
            from bson import ObjectId as _OID
            _OID(l.get("owner_id"))
        except Exception:
            continue
        land_or_storage_listing = l
        break

if admin_token and not land_or_storage_listing:
    r = requests.post(f"{API}/listings",
        headers=auth_headers(admin_token),
        json={
            "category": "land_stay",
            "title": "Test Lakeside Campsite for ToS booking",
            "description": "Forested site, fire ring, composting toilet.",
            "price": 65.0,
            "location": "Bend, OR",
            "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD"],
            "amenities": {"water_hookup": True, "electric_hookup": False},
            "is_long_term": False,
        }
    )
    if r.status_code == 200:
        land_or_storage_listing = r.json()


today = datetime.utcnow().date()
start_date = (today + timedelta(days=10)).isoformat()
end_date = (today + timedelta(days=12)).isoformat()

if fresh_guest_token and land_or_storage_listing:
    # 2a: no tos_accepted
    r = requests.post(f"{API}/bookings",
        headers=auth_headers(fresh_guest_token),
        json={
            "listing_id": land_or_storage_listing["id"],
            "start_date": start_date,
            "end_date": end_date,
            "selected_add_ons": [],
        }
    )
    try:
        detail = r.json().get("detail", "")
    except Exception:
        detail = r.text
    ok = r.status_code == 400 and "Terms of Service" in str(detail)
    record("2a booking WITHOUT tos_accepted -> 400", ok,
           f"status={r.status_code} detail={detail!r}")

    # 2b: tos_accepted=false
    r = requests.post(f"{API}/bookings",
        headers=auth_headers(fresh_guest_token),
        json={
            "listing_id": land_or_storage_listing["id"],
            "start_date": start_date,
            "end_date": end_date,
            "tos_accepted": False,
            "selected_add_ons": [],
        }
    )
    try:
        detail = r.json().get("detail", "")
    except Exception:
        detail = r.text
    ok = r.status_code == 400 and "Terms of Service" in str(detail)
    record("2b booking with tos_accepted=false -> 400", ok,
           f"status={r.status_code} detail={detail!r}")

    # 2c: tos_accepted=true
    r = requests.post(f"{API}/bookings",
        headers=auth_headers(fresh_guest_token),
        json={
            "listing_id": land_or_storage_listing["id"],
            "start_date": start_date,
            "end_date": end_date,
            "tos_accepted": True,
            "selected_add_ons": [],
        }
    )
    ok = r.status_code == 200
    if ok:
        data = r.json()
        gate_ok = data.get("status") == "pending"
        record("2c booking tos_accepted=true -> 200 (land/storage)",
               ok and gate_ok,
               f"http={r.status_code} booking_status={data.get('status')} insurance_required={data.get('insurance_required')}")
        record("4g land/storage booking status='pending' (not awaiting_insurance_review)",
               gate_ok,
               f"booking_status={data.get('status')}")
    else:
        record("2c booking tos_accepted=true -> 200", False,
               f"status={r.status_code} body={r.text[:300]}")
        record("4g land/storage booking status='pending'", False, "2c failed")
else:
    record("2a/b/c ToS on booking", False,
           f"prereq missing: fresh_guest_token={bool(fresh_guest_token)} land_or_storage_listing={bool(land_or_storage_listing)}")
    record("4g land/storage booking status='pending'", False,
           "skipped - no land_stay/vehicle_storage listing found")


# ---------------------------------------------------------------------------
# 3. RV Listing requires Proof of Insurance
# ---------------------------------------------------------------------------
print("\n=== 3. RV Listing requires Proof of Insurance ===")

rv_listing_id = None
if admin_token:
    base_rv_payload = {
        "category": "rv_rental",
        "title": "Test Class C RV - Luxury Adventure",
        "description": "Well-maintained Class C motorhome sleeps 6, full kitchen and bathroom.",
        "price": 225.0,
        "location": "Bozeman, MT",
        "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/placeholder"],
        "is_long_term": False,
    }

    # 3a: no insurance_proof
    payload_no_ins = dict(base_rv_payload)
    payload_no_ins["amenities"] = {"sleeps": 6, "length_ft": 28}
    r = requests.post(f"{API}/listings",
        headers=auth_headers(admin_token),
        json=payload_no_ins,
    )
    try:
        detail = r.json().get("detail", "")
    except Exception:
        detail = r.text
    ok = r.status_code == 400 and "insurance" in str(detail).lower() and "rv" in str(detail).lower()
    record("3a RV listing WITHOUT insurance_proof -> 400", ok,
           f"status={r.status_code} detail={detail!r}")

    # 3b: with insurance_proof
    payload_ins = dict(base_rv_payload)
    payload_ins["title"] = "Test Class C RV - With Insurance"
    payload_ins["amenities"] = {
        "sleeps": 6,
        "length_ft": 28,
        "insurance_proof": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/ins-ok",
    }
    r = requests.post(f"{API}/listings",
        headers=auth_headers(admin_token),
        json=payload_ins,
    )
    ok = r.status_code == 200
    detail = ""
    if ok:
        data = r.json()
        rv_listing_id = data.get("id")
        ok = bool(rv_listing_id) and data.get("category") == "rv_rental"
        detail = f"id={rv_listing_id} category={data.get('category')}"
    else:
        detail = f"status={r.status_code} body={r.text[:200]}"
    record("3b RV listing WITH insurance_proof -> 200", ok, detail)
else:
    record("3a/b RV listing insurance gate", False, "admin_token missing")


# ---------------------------------------------------------------------------
# 4. Insurance Gate on RV booking
# ---------------------------------------------------------------------------
print("\n=== 4. Insurance Gate on RV bookings ===")

record("4a RV listing ready (id present)", bool(rv_listing_id),
       f"rv_listing_id={rv_listing_id}")

booking_id_1 = None
booking_id_2 = None
if rv_listing_id and fresh_guest_token:
    # 4b
    r = requests.post(f"{API}/bookings",
        headers=auth_headers(fresh_guest_token),
        json={
            "listing_id": rv_listing_id,
            "start_date": start_date,
            "end_date": end_date,
            "selected_add_ons": [],
            "tos_accepted": True,
        }
    )
    ok = r.status_code == 200
    detail = ""
    if ok:
        data = r.json()
        booking_id_1 = data.get("id")
        status_ok = data.get("status") == "awaiting_insurance_review"
        ins_ok = data.get("insurance_accepted") is False
        ok = status_ok and ins_ok
        detail = f"booking_id={booking_id_1} status={data.get('status')} insurance_accepted={data.get('insurance_accepted')}"
    else:
        detail = f"status={r.status_code} body={r.text[:300]}"
    record("4b RV booking -> status=awaiting_insurance_review, insurance_accepted=false",
           ok, detail)

    # 4c: non-host cannot accept
    if booking_id_1:
        r = requests.patch(f"{API}/bookings/{booking_id_1}/accept-insurance",
            headers=auth_headers(fresh_guest_token))
        ok = r.status_code == 403
        try:
            detail = r.json().get("detail", "")
        except Exception:
            detail = r.text
        record("4c non-host accept-insurance -> 403", ok,
               f"status={r.status_code} detail={detail!r}")

    # 4d: host accepts
    if booking_id_1 and admin_token:
        r = requests.patch(f"{API}/bookings/{booking_id_1}/accept-insurance",
            headers=auth_headers(admin_token))
        ok = r.status_code == 200
        detail_json = {}
        try:
            detail_json = r.json()
        except Exception:
            pass
        if ok:
            ok = detail_json.get("status") == "confirmed"
        record("4d host accept-insurance -> 200 status=confirmed", ok,
               f"http={r.status_code} body={detail_json or r.text[:200]}")

        rh = requests.get(f"{API}/bookings/host", headers=auth_headers(admin_token))
        matched = None
        if rh.status_code == 200:
            for b in rh.json():
                if b.get("id") == booking_id_1:
                    matched = b
                    break
        verify_ok = bool(matched) and matched.get("status") == "confirmed" and matched.get("insurance_accepted") is True
        record("4d-verify GET /bookings/host shows confirmed & insurance_accepted=true",
               verify_ok,
               f"matched={bool(matched)} status={matched.get('status') if matched else None} ins_accepted={matched.get('insurance_accepted') if matched else None}")

    # 4e second booking then reject
    r = requests.post(f"{API}/bookings",
        headers=auth_headers(fresh_guest_token),
        json={
            "listing_id": rv_listing_id,
            "start_date": (today + timedelta(days=20)).isoformat(),
            "end_date": (today + timedelta(days=22)).isoformat(),
            "selected_add_ons": [],
            "tos_accepted": True,
        }
    )
    if r.status_code == 200:
        booking_id_2 = r.json().get("id")
        record("4e create second RV booking (awaiting_insurance_review)",
               r.json().get("status") == "awaiting_insurance_review",
               f"booking_id={booking_id_2} status={r.json().get('status')}")
    else:
        record("4e create second RV booking", False,
               f"status={r.status_code} body={r.text[:300]}")

    if booking_id_2 and admin_token:
        r = requests.patch(f"{API}/bookings/{booking_id_2}/reject-insurance",
            headers=auth_headers(admin_token))
        ok = r.status_code == 200
        detail_json = {}
        try:
            detail_json = r.json()
        except Exception:
            pass
        if ok:
            ok = detail_json.get("status") == "cancelled"
        record("4e host reject-insurance -> 200 status=cancelled", ok,
               f"http={r.status_code} body={detail_json or r.text[:200]}")

        # 4f
        r = requests.patch(f"{API}/bookings/{booking_id_2}/accept-insurance",
            headers=auth_headers(admin_token))
        try:
            detail = r.json().get("detail", "")
        except Exception:
            detail = r.text
        ok = r.status_code == 400
        record("4f accept-insurance on cancelled booking -> 400", ok,
               f"status={r.status_code} detail={detail!r}")
else:
    record("4b-f RV insurance-gate booking flow", False,
           f"prereq missing: rv_listing_id={bool(rv_listing_id)} fresh_guest_token={bool(fresh_guest_token)}")


# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
print(f"\nTotal: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
