#!/usr/bin/env python3
"""FurrstCamp Travel backend tests — focus on NEW features:
1. Furrst-Check verification fee = $14.99
2. Host Authenticity fee = $9.99
3. Booking payment checkout
4. Favorites CRUD
5. Nearby listings (Haversine)
"""
import os
import sys
import uuid
import json
import requests
from datetime import datetime, timedelta
from pymongo import MongoClient

BASE = "https://forest-dock.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@driveshare.com"
ADMIN_PASSWORD = "Admin123!"

# Mongo connection for DB verification
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

results = []

def log(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" — {detail}" if detail else ""))
    results.append((name, ok, detail))


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"], r.json()["user"]


def register(email, password, name, phone, tos=True):
    r = requests.post(f"{BASE}/auth/register", json={
        "email": email, "password": password, "name": name,
        "phone": phone, "accepted_tos": tos
    })
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return r.json()["token"], r.json()["user"]


def admin_verify_user(admin_token, user_id):
    r = requests.patch(f"{BASE}/admin/users/{user_id}/verify", headers=auth_headers(admin_token))
    assert r.status_code == 200, f"admin verify failed: {r.text}"


# -------- Load env for direct DB access --------
try:
    from dotenv import dotenv_values
    env = dotenv_values("/app/backend/.env")
    mongo_url = env.get("MONGO_URL", MONGO_URL)
    db_name = env.get("DB_NAME", DB_NAME)
    mongo = MongoClient(mongo_url)
    db = mongo[db_name]
    print(f"Mongo connected: db={db_name}")
except Exception as e:
    print(f"WARNING: Mongo direct access not available: {e}")
    db = None


def test_1_verification_fee_1499():
    print("\n=== Test 1: Verification fee = $14.99 ===")
    stamp = uuid.uuid4().hex[:8]
    email = f"furrstcheck_{stamp}@example.com"
    token, user = register(email, "SecurePass2024!", "Riley Walker", "555-0100")
    log("1a Register fresh unverified user", user["is_verified"] is False)
    
    r = requests.post(
        f"{BASE}/payments/verification/create-checkout",
        params={"origin_url": "https://example.com"},
        headers=auth_headers(token)
    )
    ok = r.status_code == 200 and "url" in r.json() and "session_id" in r.json()
    log("1b POST /payments/verification/create-checkout → 200 + url + session_id",
        ok, f"status={r.status_code} body={r.text[:200]}")
    if not ok:
        return
    session_id = r.json()["session_id"]
    
    if db is not None:
        tx = db.payment_transactions.find_one({"session_id": session_id})
        if tx is None:
            log("1c payment_transactions has record with amount=14.99", False, "no record")
        else:
            log("1c payment_transactions.amount == 14.99", tx.get("amount") == 14.99,
                f"amount={tx.get('amount')}, type={tx.get('type')}")
            log("1d payment_transactions.type == 'verification'", tx.get("type") == "verification",
                f"type={tx.get('type')}")


def test_2_host_authenticity_fee_999():
    print("\n=== Test 2: Host Authenticity fee = $9.99 ===")
    admin_token, admin_user = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    if db is not None:
        db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$unset": {"host_verified": "", "host_verified_at": ""}}
        )
    
    r = requests.post(
        f"{BASE}/payments/host-authenticity/create-checkout",
        params={"origin_url": "https://example.com"},
        headers=auth_headers(admin_token)
    )
    ok = r.status_code == 200 and "url" in r.json() and "session_id" in r.json()
    log("2a POST /payments/host-authenticity/create-checkout → 200", ok,
        f"status={r.status_code} body={r.text[:200]}")
    if not ok:
        return
    session_id = r.json()["session_id"]
    
    if db is not None:
        tx = db.payment_transactions.find_one({"session_id": session_id})
        if tx is None:
            log("2b payment_transactions host_authenticity recorded", False, "no record")
        else:
            log("2b payment_transactions.amount == 9.99", tx.get("amount") == 9.99,
                f"amount={tx.get('amount')}")
            log("2c payment_transactions.type == 'host_authenticity'",
                tx.get("type") == "host_authenticity", f"type={tx.get('type')}")
    
    if db is not None:
        db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"host_verified": True, "host_verified_at": datetime.utcnow().isoformat()}}
        )
        r2 = requests.post(
            f"{BASE}/payments/host-authenticity/create-checkout",
            params={"origin_url": "https://example.com"},
            headers=auth_headers(admin_token)
        )
        log("2d Already host-verified → 400", r2.status_code == 400,
            f"status={r2.status_code} body={r2.text[:200]}")
        db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$unset": {"host_verified": "", "host_verified_at": ""}}
        )


def test_3_booking_payment_checkout():
    print("\n=== Test 3: Booking Payment Checkout ===")
    admin_token, admin_user = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    listing_payload = {
        "category": "land_stay",
        "title": f"Lakeside Cabin Retreat {uuid.uuid4().hex[:6]}",
        "description": "Cozy cabin by Lake Tahoe",
        "price": 120.0,
        "location": "South Lake Tahoe, CA",
        "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//gA7..."],
        "amenities": {"sleeps": 4, "wifi": True},
        "latitude": 38.9399,
        "longitude": -119.9772
    }
    r = requests.post(f"{BASE}/listings", json=listing_payload, headers=auth_headers(admin_token))
    if r.status_code != 200:
        log("3a Create land_stay listing", False, f"status={r.status_code} body={r.text[:200]}")
        return
    listing_id = r.json()["id"]
    log("3a Create land_stay listing", True, f"id={listing_id}")
    
    stamp = uuid.uuid4().hex[:8]
    guest_email = f"bookpay_{stamp}@example.com"
    g_token, g_user = register(guest_email, "GuestPass2024!", "Morgan Lee", "555-0200")
    admin_verify_user(admin_token, g_user["id"])
    g_token, g_user = login(guest_email, "GuestPass2024!")
    log("3b Guest verified", g_user.get("is_verified") is True)
    
    start = datetime.utcnow().date() + timedelta(days=5)
    end = start + timedelta(days=3)
    booking_payload = {
        "listing_id": listing_id,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "tos_accepted": True
    }
    rb = requests.post(f"{BASE}/bookings", json=booking_payload, headers=auth_headers(g_token))
    if rb.status_code != 200:
        log("3c Create booking", False, f"status={rb.status_code} body={rb.text[:200]}")
        return
    booking_id = rb.json()["id"]
    log("3c Create booking", True, f"id={booking_id} status={rb.json().get('status')}")
    
    rp = requests.post(
        f"{BASE}/payments/booking/create-checkout",
        params={"booking_id": booking_id, "origin_url": "https://example.com"},
        headers=auth_headers(g_token)
    )
    ok = rp.status_code == 200 and "url" in rp.json() and "session_id" in rp.json()
    log("3d Guest POST /payments/booking/create-checkout → 200 + url + session_id",
        ok, f"status={rp.status_code} body={rp.text[:200]}")
    if not ok:
        return
    session_id = rp.json()["session_id"]
    
    if db is not None:
        from bson import ObjectId
        booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
        log("3e booking.payment_session_id set",
            booking.get("payment_session_id") == session_id,
            f"session_id={booking.get('payment_session_id')}")
        log("3f booking.payment_status == 'initiated'",
            booking.get("payment_status") == "initiated",
            f"payment_status={booking.get('payment_status')}")
    
    ra = requests.post(
        f"{BASE}/payments/booking/create-checkout",
        params={"booking_id": booking_id, "origin_url": "https://example.com"},
        headers=auth_headers(admin_token)
    )
    log("3g Non-guest (admin) → 403", ra.status_code == 403,
        f"status={ra.status_code} body={ra.text[:200]}")


def test_4_favorites_crud():
    print("\n=== Test 4: Favorites CRUD ===")
    admin_token, _ = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    rl = requests.get(f"{BASE}/listings", headers=auth_headers(admin_token))
    if rl.status_code != 200 or len(rl.json()) == 0:
        log("4a Get listings", False, f"status={rl.status_code}")
        return
    listing_id = rl.json()[0]["id"]
    log("4a Get listings (pick one)", True, f"listing_id={listing_id}")
    
    if db is not None:
        admin = db.users.find_one({"email": ADMIN_EMAIL})
        db.favorites.delete_many({"user_id": str(admin["_id"]), "listing_id": listing_id})
    
    r = requests.post(f"{BASE}/favorites/{listing_id}", headers=auth_headers(admin_token))
    body = r.json() if r.status_code == 200 else {}
    log("4b POST /favorites/{id} → 200, favorited=true",
        r.status_code == 200 and body.get("favorited") is True,
        f"status={r.status_code} body={r.text[:200]}")
    
    r2 = requests.post(f"{BASE}/favorites/{listing_id}", headers=auth_headers(admin_token))
    body2 = r2.json() if r2.status_code == 200 else {}
    log("4c POST again → 200 with 'Already favorited'",
        r2.status_code == 200 and "Already" in body2.get("message", ""),
        f"status={r2.status_code} body={r2.text[:200]}")
    
    rg = requests.get(f"{BASE}/favorites", headers=auth_headers(admin_token))
    favs = rg.json() if rg.status_code == 200 else []
    has_listing = any(f.get("id") == listing_id for f in favs)
    has_fav_at = any(f.get("id") == listing_id and f.get("favorited_at") for f in favs)
    log("4d GET /favorites contains listing", rg.status_code == 200 and has_listing,
        f"status={rg.status_code} count={len(favs)}")
    log("4e favorited_at field present", has_fav_at)
    
    rd = requests.delete(f"{BASE}/favorites/{listing_id}", headers=auth_headers(admin_token))
    bd = rd.json() if rd.status_code == 200 else {}
    log("4f DELETE /favorites/{id} → 200, removed=true",
        rd.status_code == 200 and bd.get("removed") is True,
        f"status={rd.status_code} body={rd.text[:200]}")
    
    rg2 = requests.get(f"{BASE}/favorites", headers=auth_headers(admin_token))
    favs2 = rg2.json() if rg2.status_code == 200 else []
    log("4g GET /favorites no longer contains listing",
        not any(f.get("id") == listing_id for f in favs2),
        f"count={len(favs2)}")


def test_5_nearby_listings():
    print("\n=== Test 5: Nearby listings (Haversine) ===")
    admin_token, _ = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    la_payload = {
        "category": "land_stay",
        "title": f"Downtown LA Loft {uuid.uuid4().hex[:6]}",
        "description": "Urban loft near Crypto.com arena",
        "price": 150.0,
        "location": "Los Angeles, CA",
        "images": ["data:image/jpeg;base64,/9j/..."],
        "amenities": {"sleeps": 2},
        "latitude": 34.0522,
        "longitude": -118.2437
    }
    r = requests.post(f"{BASE}/listings", json=la_payload, headers=auth_headers(admin_token))
    if r.status_code != 200:
        log("5a Create LA land_stay listing", False, f"status={r.status_code} body={r.text[:200]}")
        return
    la_id = r.json()["id"]
    log("5a Create LA land_stay listing", True, f"id={la_id}")
    
    boat_payload = {
        "category": "boat_rental",
        "title": f"Marina del Rey Pontoon {uuid.uuid4().hex[:6]}",
        "description": "22ft pontoon",
        "price": 350.0,
        "location": "Marina del Rey, CA",
        "images": ["data:image/jpeg;base64,/9j/..."],
        "amenities": {
            "capacity": 8,
            "life_jackets_count": 8,
            "insurance_proof": "data:image/jpeg;base64,proof",
            "security_deposit": 500
        },
        "latitude": 34.0522,
        "longitude": -118.2437
    }
    rb = requests.post(f"{BASE}/listings", json=boat_payload, headers=auth_headers(admin_token))
    boat_created = rb.status_code == 200
    boat_id = rb.json()["id"] if boat_created else None
    log("5b Create LA boat_rental listing", boat_created,
        f"status={rb.status_code} body={rb.text[:200]}")
    
    rn = requests.get(f"{BASE}/listings/nearby",
                      params={"lat": 34.05, "lng": -118.25, "radius_miles": 10})
    if rn.status_code != 200:
        log("5c Nearby LA 10mi → 200", False, f"status={rn.status_code} body={rn.text[:200]}")
        return
    data = rn.json()
    count = data.get("count", 0)
    listings = data.get("listings", [])
    found = next((x for x in listings if x.get("id") == la_id), None)
    log("5c Nearby LA count >= 1", count >= 1, f"count={count}")
    log("5d LA listing included", found is not None)
    log("5e distance_miles < 10",
        found is not None and found.get("distance_miles", 999) < 10,
        f"distance={found.get('distance_miles') if found else None}")
    
    rny = requests.get(f"{BASE}/listings/nearby",
                       params={"lat": 40.7128, "lng": -74.006, "radius_miles": 10})
    if rny.status_code == 200:
        ny_data = rny.json()
        ny_ids = [x.get("id") for x in ny_data.get("listings", [])]
        log("5f NY nearby does NOT include LA listing", la_id not in ny_ids,
            f"count={ny_data.get('count')} LA_in_list={la_id in ny_ids}")
    else:
        log("5f NY nearby call", False, f"status={rny.status_code}")
    
    rc = requests.get(f"{BASE}/listings/nearby",
                      params={"lat": 34.0522, "lng": -118.2437,
                              "radius_miles": 10, "category": "boat_rental"})
    if rc.status_code == 200:
        cdata = rc.json()
        clistings = cdata.get("listings", [])
        all_boats = all(x.get("category") == "boat_rental" for x in clistings) if clistings else True
        boat_found = boat_id is None or any(x.get("id") == boat_id for x in clistings)
        no_land = not any(x.get("id") == la_id for x in clistings)
        log("5g Category filter returns only boat_rental",
            all_boats and no_land,
            f"count={cdata.get('count')} all_boats={all_boats} no_land={no_land}")
        log("5h Created boat listing appears in category filter", boat_found)
    else:
        log("5g Category filter call", False, f"status={rc.status_code}")


def main():
    print(f"Backend: {BASE}")
    test_1_verification_fee_1499()
    test_2_host_authenticity_fee_999()
    test_3_booking_payment_checkout()
    test_4_favorites_crud()
    test_5_nearby_listings()
    
    print("\n=====================================")
    print("SUMMARY")
    print("=====================================")
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
    print(f"\n{passed}/{total} assertions passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
