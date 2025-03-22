import os
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any

# Считываем список ID из переменной окружения (через запятую)
# Пример в .env: ALLOWED_USER_IDS=336178,123456789
raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = [int(uid.strip()) for uid in raw_ids.split(",") if uid.strip().isdigit()]

class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id not in ALLOWED_IDS:
            await event.answer("🚫 Access denied.")
            return
        return await handler(event, data)
