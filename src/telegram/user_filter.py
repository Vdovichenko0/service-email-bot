import os
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any

# Считываем список ID из переменной окружения (через запятую)
# Пример в .env: ALLOWED_USER_IDS=336178,123456789
raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_IDS = [int(uid.strip()) for uid in raw_ids.split(",") if uid.strip().isdigit()]
NAME = os.getenv("NAME")
class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id not in ALLOWED_IDS:
            await event.answer(
                "🚫 Access denied.\n\n"
                f"To get access, please contact [{NAME}](https://t.me/{NAME[1:]})\n\n",
                parse_mode="Markdown",
                disable_web_page_preview = True
            )
            return
        return await handler(event, data)
