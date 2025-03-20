from motor.motor_asyncio import AsyncIOMotorClient
import os

URL = os.getenv("MONGO_URL")
if not URL:
    raise ValueError("MONGO_URL null")

MONGO_URL = URL

client = AsyncIOMotorClient(MONGO_URL)
db = client.Law
users_collection = db.users
