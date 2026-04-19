"""Backend tests for the 4 new 'Heist' features:
1. Listing schema accepts new fields (house_rules, accepts_hourly, hourly_rate, max_rv_length)
2. Universal Host Approval - Land/Storage bookings start as awaiting_host_approval
3. PATCH /api/bookings/{id}/approve
4. PATCH /api/bookings/{id}/decline
5. Hourly Booking Math
"""
import os
import sys
import time
import uuid
import requests
from datetime import datetime, timedelta

BASE_URL = "https://forest-dock.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@driveshare.com"
ADMIN_PASSWORD = "Admin123!"

results = []

def log(status, name, detail=""):
    symbol = "PASS" if status else "FAIL"
    results.append((status, name, detail))
    print(f"[{symbol}] {name}{(' — ' + detail) if detail else ''}")

def must(cond, name, detail=""):
    log(bool(cond), name, detail)
    if not cond:
        return False
    return True

def post(path, **kw):
    return requests.post(f"{BASE_URL}{path}", timeout=30, **kw)

def get(path, **kw):
    return requests.get(f"{BASE_URL}{path}", timeout=30, **kw)

def patch(path, **kw):
    return requests.patch(f"{BASE_URL}{path}", timeout=30, **kw)

def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Setup: admin login ----------
print("\n=== Setup: Admin login ===")
r = post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
if r.status_code != 200:
    print(f"FATAL: admin login failed {r.status_code} {r.text}")
    sys.exit(1)
admin_token = r.json()["token"]
admin_user = r.json()["user"]
admin_id = admin_user["id"]
print(f"Admin id={admin_id}")

# ---------- Register + verify a separate guest ----------
print("\n=== Setup: Guest register + verify ===")
guest_email = f"heist_guest_{uuid.uuid4().hex[:10]}@example.com"
r = post("/auth/register", json={
    "email": guest_email,
    "password": "GuestPass123!",
    "name": "Hayden Guest",
    "phone": "555-0199",
    "accepted_tos": True,
})
must(r.status_code == 200, "Register fresh guest", f"{r.status_code} {r.text[:200]}")
guest_token = r.json()["token"]
guest_id = r.json()["user"]["id"]

# admin-verify the guest
r = patch(f"/admin/users/{guest_id}/verify", headers=bearer(admin_token))
must(r.status_code == 200, "Admin verifies guest", f"{r.status_code} {r.text[:200]}")


# ======================================================================
# 1. Listing schema accepts new fields
# ======================================================================
print("\n=== 1. Listing schema accepts new fields ===")

# 1a: land_stay with all new fields
land_payload = {
    "category": "land_stay",
    "title": f"Riverside Meadow Hookup Site — {uuid.uuid4().hex[:6]}",
    "description": "50-amp full-hookup pad on 2 acres near the river. Pet friendly.",
    "price": 45.00,
    "location": "Asheville, NC",
    "images": ["data:image/jpeg;base64,/9j/placeholder"],
    "amenities": {"hookups": "50A", "water": True, "sewer": True},
    "house_rules": "No smoking. Quiet hours 10pm-7am.",
    "accepts_hourly": True,
    "hourly_rate": 15.00,
    "max_rv_length": 32.0,
}
r = post("/listings", json=land_payload, headers=bearer(admin_token))
ok = must(r.status_code == 200, "1a POST land_stay with new fields -> 200", f"{r.status_code} {r.text[:300]}")
land_listing = r.json() if ok else {}
land_listing_id = land_listing.get("id")

if ok:
    must(land_listing.get("house_rules") == "No smoking. Quiet hours 10pm-7am.",
         "1b house_rules persisted", str(land_listing.get("house_rules")))
    must(land_listing.get("accepts_hourly") is True,
         "1b accepts_hourly=True persisted", str(land_listing.get("accepts_hourly")))
    must(float(land_listing.get("hourly_rate", 0)) == 15.00,
         "1b hourly_rate=15.00 persisted", str(land_listing.get("hourly_rate")))
    must(float(land_listing.get("max_rv_length", 0)) == 32.0,
         "1b max_rv_length=32.0 persisted", str(land_listing.get("max_rv_length")))

# 1c: rv_rental without accepts_hourly -> default false
rv_payload = {
    "category": "rv_rental",
    "title": f"2021 Winnebago View 24J — {uuid.uuid4().hex[:6]}",
    "description": "Class C with solar, sleeps 4. Ready for your next adventure.",
    "price": 225.00,
    "location": "Denver, CO",
    "images": ["data:image/jpeg;base64,/9j/placeholder"],
    "amenities": {
        "sleeps": 4,
        "length_ft": 25,
        "insurance_proof": "data:image/jpeg;base64,/9j/insurance",
    },
    "house_rules": "No pets, no smoking.",
    "hourly_rate": 0,
    "max_rv_length": 0,
}
r = post("/listings", json=rv_payload, headers=bearer(admin_token))
ok = must(r.status_code == 200, "1c POST rv_rental without accepts_hourly -> 200",
          f"{r.status_code} {r.text[:300]}")
rv_listing = r.json() if ok else {}
rv_listing_id = rv_listing.get("id")
if ok:
    must(rv_listing.get("accepts_hourly") is False,
         "1c accepts_hourly defaults to False", str(rv_listing.get("accepts_hourly")))


# ======================================================================
# 2. Universal Host Approval - Land booking starts as awaiting_host_approval
# ======================================================================
print("\n=== 2. Universal Host Approval on Land bookings ===")

start = datetime.utcnow() + timedelta(days=7)
end = start + timedelta(days=2)
booking_payload = {
    "listing_id": land_listing_id,
    "start_date": start.isoformat(),
    "end_date": end.isoformat(),
    "tos_accepted": True,
}
r = post("/bookings", json=booking_payload, headers=bearer(guest_token))
ok = must(r.status_code == 200, "2b Guest creates land booking -> 200", f"{r.status_code} {r.text[:300]}")
land_booking_1 = r.json() if ok else {}
land_booking_1_id = land_booking_1.get("id")
if ok:
    must(land_booking_1.get("status") == "awaiting_host_approval",
         "2c status == 'awaiting_host_approval'",
         f"got status='{land_booking_1.get('status')}'")
    must(land_booking_1.get("host_approved") is False,
         "2d host_approved == False", str(land_booking_1.get("host_approved")))


# ======================================================================
# 3. PATCH /api/bookings/{id}/approve
# ======================================================================
print("\n=== 3. /approve endpoint ===")

# 3a: Non-host (guest) calls /approve -> 403
r = patch(f"/bookings/{land_booking_1_id}/approve", headers=bearer(guest_token))
must(r.status_code == 403, "3a Non-host /approve -> 403", f"{r.status_code} {r.text[:200]}")

# 3b: Host (admin) calls /approve -> 200, status=confirmed
r = patch(f"/bookings/{land_booking_1_id}/approve", headers=bearer(admin_token))
ok = must(r.status_code == 200, "3b Host /approve -> 200", f"{r.status_code} {r.text[:200]}")
if ok:
    body = r.json()
    must(body.get("status") == "confirmed",
         "3b response status=='confirmed'", str(body.get("status")))

# Verify host_approved=True via /bookings/host
r = get("/bookings/host", headers=bearer(admin_token))
if r.status_code == 200:
    hb = next((b for b in r.json() if b.get("id") == land_booking_1_id), None)
    must(hb is not None, "3b booking found in /bookings/host")
    if hb:
        must(hb.get("host_approved") is True,
             "3b host_approved=True in DB", str(hb.get("host_approved")))
        must(hb.get("status") == "confirmed",
             "3b status=confirmed in DB", str(hb.get("status")))

# 3c: Calling /approve again -> 400
r = patch(f"/bookings/{land_booking_1_id}/approve", headers=bearer(admin_token))
must(r.status_code == 400, "3c Second /approve -> 400", f"{r.status_code} {r.text[:200]}")


# ======================================================================
# 4. PATCH /api/bookings/{id}/decline
# ======================================================================
print("\n=== 4. /decline endpoint ===")

# Create another land booking
start2 = datetime.utcnow() + timedelta(days=14)
end2 = start2 + timedelta(days=3)
r = post("/bookings", json={
    "listing_id": land_listing_id,
    "start_date": start2.isoformat(),
    "end_date": end2.isoformat(),
    "tos_accepted": True,
}, headers=bearer(guest_token))
ok = must(r.status_code == 200, "4a Second land booking created", f"{r.status_code} {r.text[:300]}")
land_booking_2 = r.json() if ok else {}
land_booking_2_id = land_booking_2.get("id")
if ok:
    must(land_booking_2.get("status") == "awaiting_host_approval",
         "4a second booking status=awaiting_host_approval",
         str(land_booking_2.get("status")))

# 4b: Non-host calls /decline -> 403
r = patch(f"/bookings/{land_booking_2_id}/decline", headers=bearer(guest_token))
must(r.status_code == 403, "4b Non-host /decline -> 403", f"{r.status_code} {r.text[:200]}")

# 4c: Host (admin) calls /decline -> 200, status=cancelled
r = patch(f"/bookings/{land_booking_2_id}/decline", headers=bearer(admin_token))
ok = must(r.status_code == 200, "4c Host /decline -> 200", f"{r.status_code} {r.text[:200]}")
if ok:
    body = r.json()
    must(body.get("status") == "cancelled",
         "4c response status=='cancelled'", str(body.get("status")))

# Verify cancellation_reason via /bookings/host
r = get("/bookings/host", headers=bearer(admin_token))
if r.status_code == 200:
    hb = next((b for b in r.json() if b.get("id") == land_booking_2_id), None)
    if hb:
        must(hb.get("cancellation_reason") == "declined_by_host",
             "4c cancellation_reason=='declined_by_host'",
             str(hb.get("cancellation_reason")))
        must(hb.get("status") == "cancelled",
             "4c status=cancelled in DB", str(hb.get("status")))


# ======================================================================
# 5. Hourly Booking Math
# ======================================================================
print("\n=== 5. Hourly Booking Math ===")

# 5a-c: hourly booking against land_stay with accepts_hourly=true, hourly_rate=15
hour_start = datetime.utcnow() + timedelta(days=21, hours=9)
hour_end = hour_start + timedelta(hours=4)
r = post("/bookings", json={
    "listing_id": land_listing_id,
    "start_date": hour_start.isoformat(),
    "end_date": hour_end.isoformat(),
    "tos_accepted": True,
    "is_hourly": True,
}, headers=bearer(guest_token))
ok = must(r.status_code == 200, "5a Hourly booking -> 200", f"{r.status_code} {r.text[:300]}")
if ok:
    b = r.json()
    must(b.get("unit_label") == "hour",
         "5c unit_label=='hour'", str(b.get("unit_label")))
    must(b.get("units") == 4,
         "5c units==4", str(b.get("units")))
    must(float(b.get("base_subtotal", 0)) == 60.00,
         "5c base_subtotal==60.00 (15*4)", str(b.get("base_subtotal")))
    must(b.get("is_hourly") is True,
         "5c is_hourly flag persisted True", str(b.get("is_hourly")))

# 5d: hourly against RV listing (no accepts_hourly) -> should fall back to daily OR 4xx (no 500)
r = post("/bookings", json={
    "listing_id": rv_listing_id,
    "start_date": hour_start.isoformat(),
    "end_date": hour_end.isoformat(),
    "tos_accepted": True,
    "is_hourly": True,
}, headers=bearer(guest_token))
# Either succeeds with daily fallback (but range < 1 day -> should 400), OR 4xx.
# Accept: anything except 500.
must(r.status_code < 500,
     "5d Hourly on RV (no accepts_hourly) -> no 500",
     f"status={r.status_code} body={r.text[:200]}")
# If 200, verify it fell back to daily (unit_label=='day')
if r.status_code == 200:
    bd = r.json()
    must(bd.get("unit_label") == "day",
         "5d fallback to daily unit_label", str(bd.get("unit_label")))

# 5e: is_hourly omitted -> daily math
day_start = datetime.utcnow() + timedelta(days=30)
day_end = day_start + timedelta(days=3)
r = post("/bookings", json={
    "listing_id": land_listing_id,
    "start_date": day_start.isoformat(),
    "end_date": day_end.isoformat(),
    "tos_accepted": True,
    # is_hourly omitted
}, headers=bearer(guest_token))
ok = must(r.status_code == 200, "5e Daily booking (is_hourly omitted) -> 200",
          f"{r.status_code} {r.text[:300]}")
if ok:
    b = r.json()
    must(b.get("unit_label") == "day",
         "5e unit_label=='day'", str(b.get("unit_label")))
    must(b.get("units") == 3,
         "5e units==3", str(b.get("units")))
    # price=45 daily x 3
    must(float(b.get("base_subtotal", 0)) == 135.00,
         "5e base_subtotal==135.00 (45*3)", str(b.get("base_subtotal")))


# ======================================================================
# Summary
# ======================================================================
print("\n" + "=" * 60)
passed = sum(1 for s, *_ in results if s)
failed = sum(1 for s, *_ in results if not s)
print(f"TOTAL: {passed} passed, {failed} failed, {len(results)} assertions")
if failed:
    print("\nFAILURES:")
    for s, n, d in results:
        if not s:
            print(f"  [FAIL] {n} — {d}")
sys.exit(0 if failed == 0 else 1)
