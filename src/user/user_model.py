from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name_official: str
    name: Optional[str] = None  # can be `None`
    nickname: Optional[str] = None
    phone_number: Optional[str] = None
    sent_emails_count: int = 0  # def 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recipient: Optional[str] = None

    class Config:
        json_encoders = {ObjectId: str}
        from_attributes = True
