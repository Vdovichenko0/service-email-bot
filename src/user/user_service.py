from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from src.user.user_model import User

async def register_user(
    users_collection: AsyncIOMotorCollection,
    user_id: str,
    name_official: str,
    recipient: str,
    name: str = None,
    nickname: str = None,
    phone_number: str = None,
):
    existing_user = await users_collection.find_one({"_id": user_id})

    if not existing_user:
        new_user = User(
            _id=user_id,
            name=name,
            nickname=nickname,
            phone_number=phone_number,
            name_official=name_official,
            recipient=recipient,
            sent_emails_count=0,
            created_at=datetime.utcnow(),
        )
        await users_collection.insert_one(new_user.model_dump(by_alias=True))
        return "🎉 Registered successfully!"

    if phone_number and not existing_user.get("phone_number"):
        await users_collection.update_one(
            {"_id": user_id}, {"$set": {"phone_number": phone_number}}
        )
        return "📱 Your phone number has been updated!"

    return "🔁 You are already registered."


async def increment_sent_emails(users_collection: AsyncIOMotorCollection, user_id: str):
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$inc": {"sent_emails_count": 1}}
    )

    if result.modified_count > 0:
        return "Sent emails count increased!"
    return "User not found!"


async def set_recipient(users_collection: AsyncIOMotorCollection, user_id: str, recipient: str):
    result = await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"recipient": recipient}}
    )

    if result.modified_count > 0:
        return f"Recipient updated to {recipient}!"
    return "User not found!"


async def get_by_id(users_collection: AsyncIOMotorCollection, user_id: str):
    user_data = await users_collection.find_one({"_id": user_id})
    if not user_data:
        return None
    return User(**user_data)