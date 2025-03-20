import logging
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from src.user.user_service import register_user
from src.configs.mongodb import users_collection
from src.email.email_service import send_email

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN null")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

send_photo_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send Photo original quality")],
        [KeyboardButton(text="📸 Send Photo")],
        [KeyboardButton(text="📎 Send Document")]
    ],
    resize_keyboard=True
)

os.makedirs("content/images", exist_ok=True)
os.makedirs("content/documents", exist_ok=True)

# /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    name = message.from_user.full_name
    nickname = message.from_user.username or ""

    phone_number = None
    if message.contact and message.contact.phone_number:
        phone_number = message.contact.phone_number

    response_message = await register_user(users_collection, user_id, name, nickname, phone_number)

    await message.answer(response_message)

# ✅ Обработчик "📸 Send Photo original quality"
@dp.message(lambda message: message.text == "📸 Send Photo original quality")
async def request_original_photo(message: Message):
    await message.answer("We are ready! Please send your **photo as a file (📎 Document)** to keep the original quality.")


# ✅ Обработчик "📸 Send Photo" (обычная сжатая фотография)
@dp.message(lambda message: message.text == "📸 Send Photo")
async def request_compressed_photo(message: Message):
    await message.answer("We are ready! Send any photo.")


# ✅ Обработчик "📎 Send Document"
@dp.message(lambda message: message.text == "📎 Send Document")
async def request_document(message: Message):
    await message.answer("We are ready! Send any document file.")


# ✅ Обработчик **сжатого фото**
@dp.message(lambda message: message.photo)
async def receive_compressed_photo(message: Message):
    photo = message.photo[-1]  # Самое качественное сжатое фото
    file_path = f"content/images/photo_{message.from_user.id}.jpg"

    try:
        file_info = await bot.get_file(photo.file_id)
        await bot.download(file_info, file_path)
        logging.info(f"✅ Сжатое фото сохранено: {file_path}")

        email_sent = send_email("New Compressed Photo", "User sent a compressed photo.", file_path)

        if email_sent:
            await message.answer("📨 Your compressed photo has been sent successfully!")
        else:
            await message.answer("❌ Failed to send photo. Please try again.")

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке фото: {e}")
        await message.answer(f"❌ Error processing the photo: {str(e)}")


# ✅ Обработчик **фото как документа (без потери качества)**
@dp.message(lambda message: message.document and message.document.mime_type.startswith("image/"))
async def receive_original_photo(message: Message):
    document = message.document
    file_path = f"content/images/{document.file_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download(file_info, file_path)
        logging.info(f"✅ Оригинальное фото сохранено: {file_path}")

        email_sent = send_email("New High-Quality Photo", "User sent a high-quality photo.", file_path)

        if email_sent:
            await message.answer("📨 Your high-quality photo has been sent successfully!")
        else:
            await message.answer("❌ Failed to send photo. Please try again.")

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке фото: {e}")
        await message.answer(f"❌ Error processing the photo: {str(e)}")


# ✅ Обработчик **документов (файлы, PDF, TXT, и т. д.)**
@dp.message(lambda message: message.document)
async def receive_document(message: Message):
    document = message.document
    file_path = f"content/documents/{document.file_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download(file_info, file_path)
        logging.info(f"✅ Документ сохранен: {file_path}")

        email_sent = send_email("New Document", "User sent a document.", file_path)

        if email_sent:
            await message.answer("📨 Your document has been sent successfully!")
        else:
            await message.answer("❌ Failed to send document. Please try again.")

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке документа: {e}")
        await message.answer(f"❌ Error processing the document: {str(e)}")

# for start bot
async def start_telegram_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    task = asyncio.create_task(dp.start_polling(bot))
    await task
