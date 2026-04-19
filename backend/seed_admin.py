"""
Idempotent admin user bootstrap for FurrstCamp Travel.
Safe to run multiple times — always resets the admin password hash
to the documented credential.

Documented admin: admin@furrstcamp.com / Admin123!
"""
import asyncio
import os
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME")

ADMIN_EMAIL = "admin@furrstcamp.com"
ADMIN_PASSWORD = "Admin123!"
ADMIN_NAME = "FurrstCamp Admin"
ADMIN_PHONE = "+15555550100"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    hashed = pwd_context.hash(ADMIN_PASSWORD)
    now = datetime.utcnow().isoformat()

    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if existing:
        await db.users.update_one(
            {"email": ADMIN_EMAIL},
            {
                "$set": {
                    "password": hashed,
                    "is_admin": True,
                    "is_verified": True,
                    "is_banned": False,
                    "name": existing.get("name") or ADMIN_NAME,
                    "phone": existing.get("phone") or ADMIN_PHONE,
                }
            },
        )
        print(f"Reset admin password + flags for {ADMIN_EMAIL}")
    else:
        await db.users.insert_one(
            {
                "email": ADMIN_EMAIL,
                "password": hashed,
                "name": ADMIN_NAME,
                "phone": ADMIN_PHONE,
                "is_verified": True,
                "is_admin": True,
                "is_banned": False,
                "created_at": now,
                "verified_at": now,
            }
        )
        print(f"Created admin user {ADMIN_EMAIL}")

    # Verify the hash works
    user = await db.users.find_one({"email": ADMIN_EMAIL})
    ok = pwd_context.verify(ADMIN_PASSWORD, user["password"])
    print(f"Password verification check: {'PASS' if ok else 'FAIL'}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_admin())
