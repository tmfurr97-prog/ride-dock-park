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

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str

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
    category: str  # "rv_rental", "land_stay", "vehicle_storage"
    title: str
    description: str
    price: float
    location: str
    images: List[str]  # base64 images
    amenities: Dict[str, Any]

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
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = {
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat()
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
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    result = await db.listings.insert_one(new_listing)
    new_listing["id"] = str(result.inserted_id)
    new_listing.pop("_id", None)
    
    return new_listing

@app.get("/api/listings")
async def get_listings(category: Optional[str] = None, search: Optional[str] = None):
    query = {"status": "active"}
    
    if category:
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}}
        ]
    
    listings = []
    async for listing in db.listings.find(query).sort("created_at", -1):
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
async def get_my_listings(current_user: dict = Depends(get_current_user)):
    listings = []
    async for listing in db.listings.find({"owner_id": current_user["_id"]}).sort("created_at", -1):
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
    
    # Get listing
    try:
        listing = await db.listings.find_one({"_id": ObjectId(booking.listing_id)})
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Can't book own listing
        if listing["owner_id"] == current_user["_id"]:
            raise HTTPException(status_code=400, detail="Cannot book your own listing")
        
        # Calculate total price (simple calculation, can be enhanced)
        start = datetime.fromisoformat(booking.start_date)
        end = datetime.fromisoformat(booking.end_date)
        days = (end - start).days
        
        if days <= 0:
            raise HTTPException(status_code=400, detail="Invalid date range")
        
        total_price = listing["price"] * days
        
        new_booking = {
            "listing_id": booking.listing_id,
            "guest_id": current_user["_id"],
            "host_id": listing["owner_id"],
            "start_date": booking.start_date,
            "end_date": booking.end_date,
            "total_price": total_price,
            "status": "pending",
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
async def get_guest_bookings(current_user: dict = Depends(get_current_user)):
    bookings = []
    async for booking in db.bookings.find({"guest_id": current_user["_id"]}).sort("created_at", -1):
        # Get listing info
        listing = await db.listings.find_one({"_id": ObjectId(booking["listing_id"])})
        
        booking["id"] = str(booking["_id"])
        booking.pop("_id", None)
        
        if listing:
            booking["listing_title"] = listing["title"]
            booking["listing_image"] = listing["images"][0] if listing["images"] else None
        
        bookings.append(booking)
    
    return bookings

@app.get("/api/bookings/host")
async def get_host_bookings(current_user: dict = Depends(get_current_user)):
    bookings = []
    async for booking in db.bookings.find({"host_id": current_user["_id"]}).sort("created_at", -1):
        # Get guest info
        guest = await db.users.find_one({"_id": ObjectId(booking["guest_id"])})
        listing = await db.listings.find_one({"_id": ObjectId(booking["listing_id"])})
        
        booking["id"] = str(booking["_id"])
        booking.pop("_id", None)
        
        if guest:
            booking["guest_name"] = guest["name"]
            booking["guest_email"] = guest["email"]
        
        if listing:
            booking["listing_title"] = listing["title"]
        
        bookings.append(booking)
    
    return bookings

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
async def get_conversations(current_user: dict = Depends(get_current_user)):
    # Get all unique conversations
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
        }}
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
    current_user: dict = Depends(get_current_user)
):
    # Verify user is part of conversation
    if current_user["_id"] not in conversation_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = []
    async for msg in db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1):
        msg["id"] = str(msg["_id"])
        msg.pop("_id", None)
        messages.append(msg)
    
    return messages

@app.get("/")
async def root():
    return {"message": "DriveShare & Dock API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
