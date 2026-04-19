"""
FurrstCamp Travel — Seed Premium Listings
Creates 6 curated listings showcasing high-value rentals across all categories.
All listings are marked status='booked' to reflect active demand.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# Premium featured listings
MOCK_LISTINGS = [
    {
        "owner_id": "seed_user_1",
        "owner_name": "Premium Rentals Co.",
        "category": "rv_rental",
        "title": "Luxury Airstream - 31ft Classic with Full Amenities",
        "description": """Experience the pinnacle of mobile luxury in this meticulously maintained 31-foot Airstream Classic. This premium RV features a completely renovated interior with high-end finishes, full kitchen with stainless appliances, spacious bathroom with rainfall shower, and a master bedroom with premium bedding.

Security Features: GPS tracking, 24/7 roadside assistance, comprehensive insurance included.

Perfect for: Extended road trips, family adventures, or remote work on wheels. Fully winterized and ready for four-season travel.

Note: Currently booked through next month due to high demand. Join our waitlist for priority notification.""",
        "price": 299.00,
        "location": "Moab, Utah",
        "images": [
            "https://images.unsplash.com/photo-1760982136283-4d65075ac619?w=800",
            "https://images.unsplash.com/photo-1760982136283-4d65075ac619?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "rv_type": "Class A",
            "capacity": 4,
            "power": True,
            "water": True,
            "sewage": True
        },
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_2",
        "owner_name": "Mountain View Properties",
        "category": "land_stay",
        "title": "Private 40-Acre Estate - Gated, Utilities, Mountain Views",
        "description": """Rare opportunity to secure premium acreage in prime location. This pristine 40-acre parcel offers complete privacy, breathtaking mountain vistas, and professional-grade infrastructure.

Property Features:
• Full hookup sites with 50amp service
• Potable water system throughout
• Gated entry with keypad access
• Gravel roads maintained year-round
• Fiber internet available
• Security cameras at entry points

Ideal for: Long-term RV parking, equipment storage, off-grid living, or investment holding. Property is currently hosting a vetted long-term guest but accepting applications for future availability.

Zoning: Agricultural with RV-friendly ordinances. All permits in place.""",
        "price": 150.00,
        "location": "Jackson Hole, Wyoming",
        "images": [
            "https://images.unsplash.com/photo-1776204142084-d4ac2d07e049?w=800",
            "https://images.unsplash.com/photo-1776204142084-d4ac2d07e049?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "acreage": 40.0,
            "hookup_type": "Full Hookup",
            "utilities": "Electric, Water, Sewer, Fiber Internet"
        },
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_3",
        "owner_name": "SecureStore Facilities",
        "category": "vehicle_storage",
        "title": "Climate-Controlled RV Storage - 24/7 Gated Access",
        "description": """Premium indoor/outdoor storage facility designed specifically for high-value vehicles and RVs. Our facility sets the standard for security and convenience in vehicle storage.

Security Infrastructure:
• 24/7 HD surveillance with cloud backup
• Gated entry with individual access codes
• Motion-sensor LED lighting throughout
• Regular security patrols
• Concrete pads with drainage
• Fire suppression systems

Features:
• Electric hookups for battery maintenance
• Wash station on-site
• Dump station available
• Easy in-and-out access
• Month-to-month or annual contracts

Current Status: All premium spaces fully occupied. Limited standard spaces available with waitlist for covered storage. High demand due to exceptional security record - zero incidents in 5 years of operation.""",
        "price": 250.00,
        "location": "Boulder, Colorado",
        "images": [
            "https://images.unsplash.com/photo-1694601618351-dbbbb2b8934f?w=800",
            "https://images.unsplash.com/photo-1694601618351-dbbbb2b8934f?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "dimensions": {
                "length": 45.0,
                "width": 12.0,
                "height": 14.0
            },
            "security_features": ["Gated", "Cameras", "Lights", "24/7 Access"],
            "access_hours": "24/7"
        },
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_4",
        "owner_name": "Adventure Overland Rentals",
        "category": "rv_rental",
        "title": "4x4 Mercedes Sprinter - Full Overland Build, Solar Powered",
        "description": """Professional-grade overland vehicle built for serious adventurers. This custom 4x4 Mercedes Sprinter combines luxury with extreme capability, ready for the most demanding terrain.

Build Specifications:
• 4x4 conversion with lifted suspension
• 400W solar system with lithium batteries
• Diesel heater for cold weather
• Full kitchen with refrigerator/freezer
• Shower system with 30-gallon freshwater
• Starlink internet capability
• MaxTrax, recovery gear included

Safety & Security:
• Comprehensive insurance required
• GPS tracking installed
• Emergency satellite communicator
• Full tool kit and spare parts
• 24/7 support hotline

Currently Reserved: High-mileage bookings scheduled for next 60 days. This rig is trusted by professional expedition teams and has completed trips to Alaska, Baja, and remote Canadian territories. Serious inquiries only.""",
        "price": 350.00,
        "location": "Flagstaff, Arizona",
        "images": [
            "https://images.unsplash.com/photo-1758409313902-db8e331f71cf?w=800",
            "https://images.unsplash.com/photo-1758409313902-db8e331f71cf?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "rv_type": "Class B",
            "capacity": 2,
            "power": True,
            "water": True,
            "sewage": True
        },
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_5",
        "owner_name": "Lakeside RV Resort",
        "category": "land_stay",
        "title": "Waterfront RV Dock - Private Boat Slip & Full Hookups",
        "description": """Ultra-premium waterfront RV space with private boat dock access. This is destination-quality living with resort amenities in a secured community.

Waterfront Features:
• Direct lake access with private 30ft dock
• 50amp electrical service
• Full sewer and water hookups
• Fiber internet included
• Concrete pad with patio area
• Picnic table and fire ring
• LED security lighting

Community Amenities:
• Gated entry with 24/7 security
• Clubhouse with showers/laundry
• Kayak and paddleboard storage
• Fish cleaning station
• Boat launch nearby

Availability: This premier space is currently occupied by a seasonal guest. Extremely limited availability due to waterfront location. Annual contracts available for qualified applicants. References required.

Perfect For: Fishing enthusiasts, water sports, luxury RV living, or investment property. Property values in community have increased 40% in 3 years.""",
        "price": 185.00,
        "location": "Lake Tahoe, California",
        "images": [
            "https://images.unsplash.com/photo-1773580733011-635f0d29cbef?w=800",
            "https://images.unsplash.com/photo-1773580733011-635f0d29cbef?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "acreage": 0.25,
            "hookup_type": "Full Hookup",
            "utilities": "50amp Electric, Water, Sewer, Fiber, Dock Access"
        },
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_6",
        "owner_name": "Marina Bay Rentals",
        "category": "boat_rental",
        "title": "The Blue Water Pontoon - 24ft Premium w/ 150HP Mercury",
        "description": """Experience luxury on the water with our premium 24-foot pontoon boat. This meticulously maintained vessel combines comfort, performance, and safety for unforgettable days on the lake.

Boat Specifications:
• 24-foot premium pontoon with modern amenities
• 150HP Mercury outboard motor (professionally serviced)
• Capacity: 8 passengers plus captain
• Bimini top for sun protection
• Premium sound system with Bluetooth
• Built-in cooler and storage compartments
• GPS fish finder included
• Safety equipment exceeds Coast Guard requirements

Dock & Marina Features:
• Private covered slip at premium marina
• Easy loading dock with boarding platform
• Fuel available on-site
• Restroom and shower facilities
• Ample parking at marina

Security & Insurance:
• Comprehensive marine insurance included
• $500 refundable security deposit
• Pre-departure safety briefing required
• 24/7 emergency support hotline
• Boat inspected before each rental

Current Availability: RESERVED FOR LONG-TERM LEASE
This vessel is currently under a 365-day lease agreement with a vetted corporate client for executive waterfront entertainment. Limited seasonal availability may open in Q3 for premium daily rates.

Long-Term Lease Option: Available for qualified applicants seeking year-round water access. Perfect for corporate events, fishing charters, or lifestyle lease agreements. Annual contracts provide significant cost savings and guaranteed availability.

Insurance Required: Proof of boating insurance or purchase of our comprehensive coverage package mandatory for all renters. Coast Guard certification recommended but not required.""",
        "price": 450.00,
        "location": "Lake Havasu, Arizona",
        "images": [
            "https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?w=800",
            "https://images.unsplash.com/photo-1567899378494-47b22a2ae96a?w=800&crop=entropy&fit=crop"
        ],
        "amenities": {
            "boat_type": "Pontoon",
            "length": 24.0,
            "horsepower": 150,
            "capacity": 8,
            "has_dock": True,
            "insurance_proof": "data:image/jpeg;base64,placeholder",
            "security_deposit": 500.00,
            "life_jackets_count": 10,
            "add_ons": {
                "trailer": {"available": True, "price_per_day": 75.00, "included_free": False},
                "wakeboard_tower": {"available": True, "price_per_day": 50.00, "included_free": False},
                "fishing_gear": {"available": True, "price_per_day": 0.00, "included_free": True},
                "bimini_top": {"available": True, "price_per_day": 0.00, "included_free": True}
            }
        },
        "status": "booked",
        "is_long_term": True,
        "created_at": datetime.utcnow().isoformat()
    }
]

async def seed_database():
    """Seed the database with mock listings"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🌱 Seeding FurrstCamp Travel with premium listings...")
    
    # Check if seed listings already exist
    existing = await db.listings.count_documents({"owner_id": {"$regex": "^seed_user_"}})
    if existing > 0:
        print(f"⚠️  Found {existing} existing seed listings. Removing old seed data...")
        await db.listings.delete_many({"owner_id": {"$regex": "^seed_user_"}})
    
    # Insert new listings
    result = await db.listings.insert_many(MOCK_LISTINGS)
    print(f"✅ Successfully created {len(result.inserted_ids)} premium listings:")
    
    for i, listing in enumerate(MOCK_LISTINGS, 1):
        price_unit = 'day' if listing['category'] == 'rv_rental' or listing['category'] == 'boat_rental' else 'night' if listing['category'] == 'land_stay' else 'month'
        long_term = ' [365-Day Lease]' if listing.get('is_long_term') else ''
        print(f"   {i}. {listing['title']} - ${listing['price']}/{price_unit}{long_term}")
    
    print("\n📊 Social proof listings are now live in the marketplace!")
    print("🔒 All listings marked as 'Currently Booked' to show high demand")
    print("🚤 New: Boat Rentals & Docks category added with insurance + deposit requirements")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
