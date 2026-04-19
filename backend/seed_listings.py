"""
FurrstCamp Travel — Seed Premium Listings
Creates 6 curated listings showcasing high-value rentals across all categories.
All listings are marked status='booked' to reflect active demand while still browsable.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

# Featured listings — real-person host names, lifelike imagery
MOCK_LISTINGS = [
    {
        "owner_id": "seed_user_1",
        "owner_name": "Marcus T.",
        "category": "rv_rental",
        "title": "Luxury Airstream — 31ft Classic with Full Amenities",
        "description": """Experience the pinnacle of mobile luxury in this meticulously maintained 31-foot Airstream Classic. Fully renovated interior with high-end finishes, full kitchen with stainless appliances, spacious bathroom with rainfall shower, and a master bedroom with premium bedding.

Security Features: GPS tracking, 24/7 roadside assistance, comprehensive insurance included.

Perfect for: Extended road trips, family adventures, or remote work on wheels. Fully winterized and ready for four-season travel.

Note: Currently booked through next month due to high demand. Join our waitlist for priority notification.""",
        "price": 299.00,
        "location": "Moab, Utah",
        "latitude": 38.5733,
        "longitude": -109.5498,
        "images": [
            "https://images.unsplash.com/photo-1591799590615-758704d3df5c?w=800&auto=format&fit=crop",
            "https://images.pexels.com/photos/13304737/pexels-photo-13304737.jpeg?auto=compress&cs=tinysrgb&w=800"
        ],
        "amenities": {
            "rv_type": "Class A",
            "capacity": 4,
            "power": True,
            "water": True,
            "sewage": True,
            "insurance_proof": "data:image/jpeg;base64,seed",
            "add_ons": {
                "golf_cart": {"available": True, "price_per_day": 25.00, "included_free": False}
            }
        },
        "house_rules": "No smoking. Quiet hours 10pm–7am. Pets OK with $100 deposit. Check-in 3pm.",
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_2",
        "owner_name": "Sarah M.",
        "category": "land_stay",
        "title": "Private 40-Acre Estate — Gated, Utilities, Mountain Views",
        "description": """Rare opportunity to secure premium acreage in prime location. This pristine 40-acre parcel offers complete privacy, breathtaking mountain vistas, and professional-grade infrastructure.

Property Features:
• Full hookup sites with 50amp service
• Potable water system throughout
• Gated entry with keypad access
• Gravel roads maintained year-round
• Fiber internet available
• Security cameras at entry points

Ideal for long-term RV parking, equipment storage, off-grid living, or investment holding. Zoning: Agricultural with RV-friendly ordinances.""",
        "price": 150.00,
        "location": "Jackson Hole, Wyoming",
        "latitude": 43.4799,
        "longitude": -110.7624,
        "images": [
            "https://images.pexels.com/photos/28903008/pexels-photo-28903008.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/27824279/pexels-photo-27824279.jpeg?auto=compress&cs=tinysrgb&w=800"
        ],
        "amenities": {
            "acreage": 40.0,
            "hookup_type": "Full Hookup",
            "utilities": "Electric, Water, Sewer, Fiber Internet",
            "add_ons": {
                "golf_cart": {"available": True, "price_per_day": 0.00, "included_free": True}
            }
        },
        "house_rules": "No fires outside designated pits. Quiet hours 10pm–8am. Dogs welcome on leash.",
        "max_rv_length": 45.0,
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_3",
        "owner_name": "David C.",
        "category": "vehicle_storage",
        "title": "Climate-Controlled RV Storage — 24/7 Gated Access",
        "description": """Premium indoor/outdoor storage facility designed specifically for high-value vehicles and RVs. Our facility sets the standard for security and convenience.

Security Infrastructure:
• 24/7 HD surveillance with cloud backup
• Gated entry with individual access codes
• Motion-sensor LED lighting throughout
• Fire suppression systems

Features:
• Electric hookups for battery maintenance
• Wash station on-site
• Dump station available
• Month-to-month or annual contracts

Zero incidents in 5 years of operation.""",
        "price": 250.00,
        "location": "Boulder, Colorado",
        "latitude": 40.0150,
        "longitude": -105.2705,
        "images": [
            "https://images.unsplash.com/photo-1766503494749-0806c2a0aab4?w=800&auto=format&fit=crop",
            "https://images.pexels.com/photos/20877915/pexels-photo-20877915.jpeg?auto=compress&cs=tinysrgb&w=800"
        ],
        "amenities": {
            "dimensions": {"length": 45.0, "width": 12.0, "height": 14.0},
            "security_features": ["Gated", "Cameras", "Lights", "24/7 Access"],
            "access_hours": "24/7"
        },
        "house_rules": "Access code must be kept confidential. Vehicles must be insured.",
        "max_rv_length": 45.0,
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_4",
        "owner_name": "Elena R.",
        "category": "rv_rental",
        "title": "4x4 Mercedes Sprinter — Full Overland Build, Solar Powered",
        "description": """Professional-grade overland vehicle built for serious adventurers. Custom 4x4 Mercedes Sprinter combines luxury with extreme capability.

Build:
• 4x4 conversion with lifted suspension
• 400W solar + lithium batteries
• Diesel heater, full kitchen, shower
• Starlink internet capability
• Recovery gear included

Trusted by professional expedition teams. Serious inquiries only.""",
        "price": 350.00,
        "location": "Flagstaff, Arizona",
        "latitude": 35.1983,
        "longitude": -111.6513,
        "images": [
            "https://images.unsplash.com/photo-1633043793637-635238a9d20d?w=800&auto=format&fit=crop",
            "https://images.pexels.com/photos/27620845/pexels-photo-27620845.jpeg?auto=compress&cs=tinysrgb&w=800"
        ],
        "amenities": {
            "rv_type": "Class B",
            "capacity": 2,
            "power": True,
            "water": True,
            "sewage": True,
            "insurance_proof": "data:image/jpeg;base64,seed"
        },
        "house_rules": "No off-roading outside planned route. Full insurance required.",
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_5",
        "owner_name": "James K.",
        "category": "land_stay",
        "title": "Waterfront RV Dock — Private Boat Slip & Full Hookups",
        "description": """Ultra-premium waterfront RV space with private boat dock access. Resort amenities in a secured community.

Waterfront:
• Direct lake access with private 30ft dock
• 50amp electric, full sewer/water
• Fiber internet
• Patio, picnic table, fire ring

Community:
• Gated, 24/7 security
• Clubhouse with showers/laundry
• Kayak storage, fish cleaning station""",
        "price": 185.00,
        "location": "Lake Tahoe, California",
        "latitude": 39.0968,
        "longitude": -120.0324,
        "images": [
            "https://images.pexels.com/photos/9137669/pexels-photo-9137669.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/37114015/pexels-photo-37114015.jpeg?auto=compress&cs=tinysrgb&w=800"
        ],
        "amenities": {
            "acreage": 0.25,
            "hookup_type": "Full Hookup",
            "utilities": "50amp Electric, Water, Sewer, Fiber, Dock Access"
        },
        "house_rules": "No loud music after 9pm. Pets on leash. Trash to community dumpster.",
        "max_rv_length": 40.0,
        "status": "booked",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "owner_id": "seed_user_6",
        "owner_name": "Alicia B.",
        "category": "boat_rental",
        "title": "The Blue Water Pontoon — 24ft Premium w/ 150HP Mercury",
        "description": """Experience luxury on the water with our premium 24-foot pontoon boat. Meticulously maintained vessel with comfort, performance, and safety.

Specs:
• 24ft pontoon, 150HP Mercury outboard
• Capacity: 8 passengers
• Bimini top, Bluetooth audio, cooler, GPS fish finder
• Coast Guard safety equipment

Current: RESERVED FOR LONG-TERM LEASE (365-day corporate contract). Seasonal availability may open Q3.""",
        "price": 450.00,
        "location": "Lake Havasu, Arizona",
        "latitude": 34.4839,
        "longitude": -114.3225,
        "images": [
            "https://images.pexels.com/photos/12914427/pexels-photo-12914427.jpeg?auto=compress&cs=tinysrgb&w=800",
            "https://images.pexels.com/photos/26838520/pexels-photo-26838520.jpeg?auto=compress&cs=tinysrgb&w=800"
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
        "house_rules": "Life jackets required for all passengers. Boating license required. No alcohol for operator.",
        "status": "booked",
        "is_long_term": True,
        "created_at": datetime.utcnow().isoformat()
    }
]


async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("🌱 Seeding FurrstCamp Travel with premium listings...")

    existing = await db.listings.count_documents({"owner_id": {"$regex": "^seed_user_"}})
    if existing > 0:
        print(f"⚠️  Found {existing} existing seed listings. Removing old seed data...")
        await db.listings.delete_many({"owner_id": {"$regex": "^seed_user_"}})

    result = await db.listings.insert_many(MOCK_LISTINGS)
    print(f"✅ Successfully inserted {len(result.inserted_ids)} listings:")
    for i, listing in enumerate(MOCK_LISTINGS, 1):
        print(f"   {i}. {listing['title']} — ${listing['price']}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
