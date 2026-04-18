from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
import os
from jose import jwt, JWTError
from passlib.context import CryptContext
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT and Password setup
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Stripe setup
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
VERIFICATION_AMOUNT = 25.00  # Fixed $25 verification fee

# Platform commission config
PLATFORM_COMMISSION_INTRO_RATE = 0.10  # 10% for first 6 months after host joined
PLATFORM_COMMISSION_STANDARD_RATE = 0.15  # 15% after intro period
PLATFORM_ADD_ON_FEE_RATE = 0.10  # flat 10% on all add-ons, always
INTRO_PERIOD_DAYS = 180  # 6 months

def compute_host_commission_rate(host_created_at_iso: Optional[str]) -> float:
    """Returns the platform commission rate for the host based on tenure."""
    if not host_created_at_iso:
        return PLATFORM_COMMISSION_STANDARD_RATE
    try:
        host_created = datetime.fromisoformat(host_created_at_iso.replace("Z", ""))
    except Exception:
        return PLATFORM_COMMISSION_STANDARD_RATE
    age = datetime.utcnow() - host_created
    if age.days < INTRO_PERIOD_DAYS:
        return PLATFORM_COMMISSION_INTRO_RATE
    return PLATFORM_COMMISSION_STANDARD_RATE

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user["_id"] = str(user["_id"])
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    accepted_tos: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: str
    is_verified: bool
    created_at: str

class ListingCreate(BaseModel):
    category: str  # "rv_rental", "land_stay", "vehicle_storage", "boat_rental"
    title: str
    description: str
    price: float
    location: str
    images: List[str]  # base64 images
    amenities: Dict[str, Any]
    is_long_term: Optional[bool] = False

class ListingResponse(BaseModel):
    id: str
    owner_id: str
    owner_name: str
    category: str
    title: str
    description: str
    price: float
    location: str
    images: List[str]
    amenities: Dict[str, Any]
    status: str
    created_at: str

class BookingCreate(BaseModel):
    listing_id: str
    start_date: str
    end_date: str
    selected_add_ons: Optional[List[str]] = []  # e.g., ["golf_cart", "trailer", "bimini_top"]
    tos_accepted: bool = False

class BookingResponse(BaseModel):
    id: str
    listing_id: str
    guest_id: str
    host_id: str
    start_date: str
    end_date: str
    total_price: float
    status: str
    created_at: str

class MessageCreate(BaseModel):
    receiver_id: str
    listing_id: Optional[str] = None
    message: str

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    receiver_id: str
    message: str
    timestamp: str

# =====================
# AUTH ENDPOINTS
# =====================
@app.post("/api/auth/register")
async def register(user: UserRegister):
    # Require ToS acceptance
    if not user.accepted_tos:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the Terms of Service to create an account."
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    now = datetime.utcnow().isoformat()
    # Create new user
    new_user = {
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "is_verified": False,
        "is_admin": False,
        "is_banned": False,
        "accepted_tos": True,
        "tos_accepted_at": now,
        "created_at": now
    }
    
    result = await db.users.insert_one(new_user)
    
    # Create JWT token
    token = create_access_token({"sub": user.email})
    
    return {
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "is_verified": False,
            "created_at": new_user["created_at"]
        }
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": credentials.email})
    
    return {
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "is_verified": user.get("is_verified", False),
            "created_at": user["created_at"]
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "phone": current_user["phone"],
        "is_verified": current_user.get("is_verified", False),
        "created_at": current_user["created_at"]
    }

# =====================
# STRIPE PAYMENT ENDPOINTS
# =====================
@app.post("/api/payments/verification/create-checkout")
async def create_verification_checkout(
    request: Request,
    origin_url: str,
    current_user: dict = Depends(get_current_user)
):
    # Check if already verified
    if current_user.get("is_verified"):
        raise HTTPException(status_code=400, detail="User already verified")
    
    # Check if there's a pending payment
    pending_payment = await db.payment_transactions.find_one({
        "user_id": current_user["_id"],
        "type": "verification",
        "payment_status": {"$in": ["initiated", "pending"]}
    })
    
    if pending_payment:
        raise HTTPException(status_code=400, detail="Pending verification payment exists")
    
    # Create Stripe checkout session
    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{origin_url}/verification-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/verification"
    
    checkout_request = CheckoutSessionRequest(
        amount=VERIFICATION_AMOUNT,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["_id"],
            "type": "verification",
            "email": current_user["email"]
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Store payment transaction
    payment_transaction = {
        "user_id": current_user["_id"],
        "email": current_user["email"],
        "session_id": session.session_id,
        "amount": VERIFICATION_AMOUNT,
        "currency": "usd",
        "type": "verification",
        "payment_status": "initiated",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    await db.payment_transactions.insert_one(payment_transaction)
    
    return {"url": session.url, "session_id": session.session_id}

@app.get("/api/payments/verification/status/{session_id}")
async def check_verification_status(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    # Get payment transaction
    payment = await db.payment_transactions.find_one({
        "session_id": session_id,
        "user_id": current_user["_id"]
    })
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # If already processed as paid, return success
    if payment.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "is_verified": True
        }
    
    # Check Stripe status
    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    
    # Update payment transaction
    update_data = {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": update_data}
    )
    
    # If payment is successful and not already verified, verify the user
    if checkout_status.payment_status == "paid" and not current_user.get("is_verified"):
        await db.users.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow().isoformat()}}
        )
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "is_verified": True
        }
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "is_verified": current_user.get("is_verified", False)
    }

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    base_url = str(request.base_url).rstrip('/')
    webhook_url = f"{base_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Handle verification payments
        if webhook_response.metadata.get("type") == "verification":
            user_id = webhook_response.metadata.get("user_id")
            
            if webhook_response.payment_status == "paid":
                # Update user verification status
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": {"is_verified": True, "verified_at": datetime.utcnow().isoformat()}}
                )
                
                # Update payment transaction
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "status": "complete",
                        "updated_at": datetime.utcnow().isoformat()
                    }}
                )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =====================
# LISTINGS ENDPOINTS
# =====================
@app.post("/api/listings")
async def create_listing(
    listing: ListingCreate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user is verified
    if not current_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Must be verified to create listings")
    
    # Validate category
    allowed_categories = {"rv_rental", "land_stay", "vehicle_storage", "boat_rental"}
    if listing.category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(sorted(allowed_categories))}"
        )
    
    # RV rentals: proof of insurance required
    if listing.category == "rv_rental":
        amen = listing.amenities or {}
        if not amen.get("insurance_proof"):
            raise HTTPException(
                status_code=400,
                detail="Proof of insurance is required for RV rentals"
            )
    
    # Boat rental requires insurance proof, security deposit, and life jackets count
    if listing.category == "boat_rental":
        amen = listing.amenities or {}
        if not amen.get("insurance_proof"):
            raise HTTPException(status_code=400, detail="Proof of insurance is required for boat rentals")
        if not amen.get("security_deposit") or float(amen.get("security_deposit", 0)) <= 0:
            raise HTTPException(status_code=400, detail="Security deposit is required for boat rentals")
        life_jackets = amen.get("life_jackets_count")
        capacity = amen.get("capacity", 0)
        if not life_jackets or int(life_jackets) <= 0:
            raise HTTPException(
                status_code=400,
                detail="Life jackets count is required for boat rentals (Coast Guard requirement)"
            )
        if int(life_jackets) < int(capacity):
            raise HTTPException(
                status_code=400,
                detail=f"Life jackets ({life_jackets}) must be at least equal to boat capacity ({capacity})"
            )
    
    new_listing = {
        "owner_id": current_user["_id"],
        "owner_name": current_user["name"],
        "category": listing.category,
        "title": listing.title,
        "description": listing.description,
        "price": listing.price,
        "location": listing.location,
        "images": listing.images,
        "amenities": listing.amenities,
        "is_long_term": listing.is_long_term or False,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = await db.listings.insert_one(new_listing)
    new_listing["id"] = str(result.inserted_id)
    new_listing.pop("_id", None)
    
    return new_listing

@app.get("/api/listings")
async def get_listings(
    category: Optional[str] = None, 
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    query = {"status": {"$in": ["active", "booked"]}}  # Include booked listings for social proof
    
    if category:
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}}
        ]
    
    listings = []
    # Exclude large image arrays for list view performance
    projection = {"images": {"$slice": 1}}  # Only include first image
    async for listing in db.listings.find(query, projection).sort("created_at", -1).skip(skip).limit(limit):
        listing["id"] = str(listing["_id"])
        listing.pop("_id", None)
        listings.append(listing)
    
    return listings

@app.get("/api/listings/{listing_id}")
async def get_listing(listing_id: str):
    try:
        listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        listing["id"] = str(listing["_id"])
        listing.pop("_id", None)
        return listing
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid listing ID")

@app.get("/api/listings/user/me")
async def get_my_listings(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    listings = []
    projection = {"images": {"$slice": 1}}  # Only first image for list view
    async for listing in db.listings.find({"owner_id": current_user["_id"]}, projection).sort("created_at", -1).limit(limit):
        listing["id"] = str(listing["_id"])
        listing.pop("_id", None)
        listings.append(listing)
    
    return listings

@app.delete("/api/listings/{listing_id}")
async def delete_listing(listing_id: str, current_user: dict = Depends(get_current_user)):
    try:
        listing = await db.listings.find_one({"_id": ObjectId(listing_id)})
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        if listing["owner_id"] != current_user["_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        await db.listings.update_one(
            {"_id": ObjectId(listing_id)},
            {"$set": {"status": "deleted"}}
        )
        
        return {"message": "Listing deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid listing ID")

# =====================
# BOOKINGS ENDPOINTS
# =====================
@app.post("/api/bookings")
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(get_current_user)
):
    # Check if user is verified
    if not current_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Must be verified to book")
    
    # Require ToS acceptance for every booking
    if not booking.tos_accepted:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the Terms of Service to book."
        )
    
    # Get listing
    try:
        listing = await db.listings.find_one({"_id": ObjectId(booking.listing_id)})
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Can't book own listing
        if listing["owner_id"] == current_user["_id"]:
            raise HTTPException(status_code=400, detail="Cannot book your own listing")
        
        # Calculate base rental price
        start = datetime.fromisoformat(booking.start_date)
        end = datetime.fromisoformat(booking.end_date)
        days = (end - start).days
        
        if days <= 0:
            raise HTTPException(status_code=400, detail="Invalid date range")
        
        base_subtotal = listing["price"] * days
        
        # Add-ons (owner-priced, flat 10% platform fee on each)
        amenities = listing.get("amenities", {}) or {}
        available_add_ons = amenities.get("add_ons", {}) or {}
        selected = booking.selected_add_ons or []
        
        add_on_items = []
        add_ons_subtotal = 0.0
        for key in selected:
            cfg = available_add_ons.get(key)
            if not cfg or not cfg.get("available"):
                continue
            price_per_day = float(cfg.get("price_per_day", 0) or 0)
            line_total = price_per_day * days
            add_on_items.append({
                "key": key,
                "price_per_day": price_per_day,
                "days": days,
                "line_total": round(line_total, 2),
                "included_free": cfg.get("included_free", price_per_day == 0),
            })
            add_ons_subtotal += line_total
        
        # Fetch host for commission tenure
        host = await db.users.find_one({"_id": ObjectId(listing["owner_id"])})
        host_rate = compute_host_commission_rate(host.get("created_at") if host else None)
        
        rental_commission = base_subtotal * host_rate
        add_on_commission = add_ons_subtotal * PLATFORM_ADD_ON_FEE_RATE
        platform_fee_total = rental_commission + add_on_commission
        
        # Security deposit (held but not earned)
        security_deposit = float(amenities.get("security_deposit", 0) or 0)
        
        # Total charged to guest = rentals + add-ons + security deposit (deposit refundable)
        total_price = base_subtotal + add_ons_subtotal + security_deposit
        host_payout = (base_subtotal + add_ons_subtotal) - platform_fee_total
        
        # Insurance gate: RV and Boat rentals must be accepted by host before confirmed
        category = listing.get("category", "")
        requires_insurance_review = category in ("rv_rental", "boat_rental")
        initial_status = "awaiting_insurance_review" if requires_insurance_review else "pending"
        
        new_booking = {
            "listing_id": booking.listing_id,
            "guest_id": current_user["_id"],
            "guest_name": current_user["name"],
            "host_id": listing["owner_id"],
            "category": category,
            "start_date": booking.start_date,
            "end_date": booking.end_date,
            "days": days,
            "base_subtotal": round(base_subtotal, 2),
            "add_ons": add_on_items,
            "add_ons_subtotal": round(add_ons_subtotal, 2),
            "security_deposit": round(security_deposit, 2),
            "platform_fee_rate": host_rate,
            "platform_rental_fee": round(rental_commission, 2),
            "platform_add_on_fee": round(add_on_commission, 2),
            "platform_fee_total": round(platform_fee_total, 2),
            "host_payout": round(host_payout, 2),
            "total_price": round(total_price, 2),
            "status": initial_status,
            "insurance_required": requires_insurance_review,
            "insurance_accepted": False,
            "tos_accepted": True,
            "tos_accepted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = await db.bookings.insert_one(new_booking)
        new_booking["id"] = str(result.inserted_id)
        new_booking.pop("_id", None)
        
        return new_booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/bookings/guest")
async def get_guest_bookings(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    # Use aggregation pipeline to join listings in one query (better performance)
    pipeline = [
        {"$match": {"guest_id": current_user["_id"]}},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "listings",
            "let": {"listing_id": {"$toObjectId": "$listing_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$_id", "$$listing_id"]}}},
                {"$project": {"title": 1, "images": {"$slice": ["$images", 1]}}}
            ],
            "as": "listing_info"
        }},
        {"$unwind": {"path": "$listing_info", "preserveNullAndEmptyArrays": True}}
    ]
    
    bookings = []
    async for booking in db.bookings.aggregate(pipeline):
        booking["id"] = str(booking["_id"])
        booking.pop("_id", None)
        
        if "listing_info" in booking and booking["listing_info"]:
            booking["listing_title"] = booking["listing_info"].get("title")
            booking["listing_image"] = booking["listing_info"]["images"][0] if booking["listing_info"].get("images") else None
            booking.pop("listing_info", None)
        
        bookings.append(booking)
    
    return bookings

@app.get("/api/bookings/host")
async def get_host_bookings(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    # Use aggregation pipeline to join users and listings efficiently
    pipeline = [
        {"$match": {"host_id": current_user["_id"]}},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from": "users",
            "let": {"guest_id": {"$toObjectId": "$guest_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$_id", "$$guest_id"]}}},
                {"$project": {"name": 1, "email": 1}}
            ],
            "as": "guest_info"
        }},
        {"$lookup": {
            "from": "listings",
            "let": {"listing_id": {"$toObjectId": "$listing_id"}},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$_id", "$$listing_id"]}}},
                {"$project": {"title": 1}}
            ],
            "as": "listing_info"
        }},
        {"$unwind": {"path": "$guest_info", "preserveNullAndEmptyArrays": True}},
        {"$unwind": {"path": "$listing_info", "preserveNullAndEmptyArrays": True}}
    ]
    
    bookings = []
    async for booking in db.bookings.aggregate(pipeline):
        booking["id"] = str(booking["_id"])
        booking.pop("_id", None)
        
        if "guest_info" in booking and booking["guest_info"]:
            booking["guest_name"] = booking["guest_info"].get("name")
            booking["guest_email"] = booking["guest_info"].get("email")
            booking.pop("guest_info", None)
        
        if "listing_info" in booking and booking["listing_info"]:
            booking["listing_title"] = booking["listing_info"].get("title")
            booking.pop("listing_info", None)
        
        bookings.append(booking)
    
    return bookings

@app.patch("/api/bookings/{booking_id}/accept-insurance")
async def accept_insurance(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Host accepts the guest's insurance / approves the booking.
    Only works on bookings in 'awaiting_insurance_review' status, and only
    the listing host may call it."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.get("host_id") != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Only the host can accept this booking")
    
    if booking.get("status") != "awaiting_insurance_review":
        raise HTTPException(
            status_code=400,
            detail=f"Booking is not awaiting insurance review (current status: {booking.get('status')})"
        )
    
    await db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "insurance_accepted": True,
            "insurance_accepted_at": datetime.utcnow().isoformat(),
            "status": "confirmed"
        }}
    )
    return {"message": "Insurance accepted, booking confirmed", "status": "confirmed"}

@app.patch("/api/bookings/{booking_id}/reject-insurance")
async def reject_insurance(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Host rejects the guest's insurance — booking is cancelled."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking ID")
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.get("host_id") != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Only the host can reject this booking")
    
    await db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {
            "insurance_accepted": False,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancellation_reason": "insurance_rejected"
        }}
    )
    return {"message": "Insurance rejected, booking cancelled", "status": "cancelled"}

# =====================
# MESSAGES ENDPOINTS
# =====================
@app.post("/api/messages")
async def send_message(
    message: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    # Create conversation ID (sorted user IDs)
    user_ids = sorted([current_user["_id"], message.receiver_id])
    conversation_id = f"{user_ids[0]}_{user_ids[1]}"
    
    new_message = {
        "conversation_id": conversation_id,
        "sender_id": current_user["_id"],
        "sender_name": current_user["name"],
        "receiver_id": message.receiver_id,
        "listing_id": message.listing_id,
        "message": message.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await db.messages.insert_one(new_message)
    new_message["id"] = str(result.inserted_id)
    new_message.pop("_id", None)
    
    return new_message

@app.get("/api/messages/conversations")
async def get_conversations(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    # Get all unique conversations with limit
    pipeline = [
        {"$match": {
            "$or": [
                {"sender_id": current_user["_id"]},
                {"receiver_id": current_user["_id"]}
            ]
        }},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$conversation_id",
            "last_message": {"$first": "$$ROOT"}
        }},
        {"$limit": limit}
    ]
    
    conversations = []
    async for conv in db.messages.aggregate(pipeline):
        msg = conv["last_message"]
        
        # Get other user info
        other_user_id = msg["sender_id"] if msg["sender_id"] != current_user["_id"] else msg["receiver_id"]
        other_user = await db.users.find_one({"_id": ObjectId(other_user_id)})
        
        if other_user:
            conversations.append({
                "conversation_id": conv["_id"],
                "other_user": {
                    "id": str(other_user["_id"]),
                    "name": other_user["name"]
                },
                "last_message": msg["message"],
                "timestamp": msg["timestamp"]
            })
    
    return conversations

@app.get("/api/messages/{conversation_id}")
async def get_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 200
):
    # Verify user is part of conversation
    if current_user["_id"] not in conversation_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = []
    # Get most recent messages (reversed for chronological order in UI)
    async for msg in db.messages.find({"conversation_id": conversation_id}).sort("timestamp", -1).limit(limit):
        msg["id"] = str(msg["_id"])
        msg.pop("_id", None)
        messages.append(msg)
    
    # Reverse to show oldest first
    messages.reverse()
    
    return messages

# =====================
# ADMIN ENDPOINTS
# =====================
@app.get("/api/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    verified_users = await db.users.count_documents({"is_verified": True})
    total_listings = await db.listings.count_documents({"status": "active"})
    total_bookings = await db.bookings.count_documents({})
    
    # Calculate total revenue from verification payments
    pipeline = [
        {"$match": {"type": "verification", "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.payment_transactions.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Recent users (last 7 days)
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_users = await db.users.count_documents({"created_at": {"$gte": seven_days_ago}})
    
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "total_listings": total_listings,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "recent_users": recent_users,
    }

@app.get("/api/admin/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    users = []
    # Exclude password from projection for security
    projection = {"password": 0}
    async for user in db.users.find({}, projection).skip(skip).limit(limit).sort("created_at", -1):
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        users.append(user)
    
    total = await db.users.count_documents({})
    return {"users": users, "total": total}

@app.patch("/api/admin/users/{user_id}/verify")
async def admin_verify_user(user_id: str, admin: dict = Depends(get_admin_user)):
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow().isoformat()}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User verified"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/admin/users/{user_id}/ban")
async def admin_ban_user(user_id: str, banned: bool, admin: dict = Depends(get_admin_user)):
    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_banned": banned}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": f"User {'banned' if banned else 'unbanned'}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/listings")
async def get_all_listings_admin(
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    listings = []
    # Exclude large images for admin list view performance
    projection = {"images": 0}
    async for listing in db.listings.find({}, projection).skip(skip).limit(limit).sort("created_at", -1):
        listing["id"] = str(listing["_id"])
        listing.pop("_id", None)
        listings.append(listing)
    
    total = await db.listings.count_documents({})
    return {"listings": listings, "total": total}

@app.delete("/api/admin/listings/{listing_id}")
async def admin_delete_listing(listing_id: str, admin: dict = Depends(get_admin_user)):
    try:
        result = await db.listings.update_one(
            {"_id": ObjectId(listing_id)},
            {"$set": {"status": "deleted"}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Listing not found")
        return {"message": "Listing deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/payments")
async def get_all_payments(
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    payments = []
    async for payment in db.payment_transactions.find().skip(skip).limit(limit).sort("created_at", -1):
        payment["id"] = str(payment["_id"])
        payment.pop("_id", None)
        payments.append(payment)
    
    total = await db.payment_transactions.count_documents({})
    return {"payments": payments, "total": total}

@app.get("/")
async def root():
    return {"message": "DriveShare & Dock API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
