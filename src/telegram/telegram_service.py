import logging
import os
import asyncio
import mimetypes
from uuid import uuid4
from aiogram.fsm.context import FSMContext
from src.telegram.register_fsm import register_router
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from src.user.user_service import set_recipient, get_by_id
from src.configs.mongodb import users_collection
from src.email.email_service import send_email, send_email_with_files
from src.telegram.keyboard import main_keyboard, choice_recipient_keyboard, send_many_keyboard

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN null")

EMAIL1 = os.getenv("TO_EMAIL1")
EMAIL2 = os.getenv("TO_EMAIL2")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

dp.include_router(register_router)


os.makedirs("content/images", exist_ok=True)
os.makedirs("content/documents", exist_ok=True)
os.makedirs("content/tmp", exist_ok=True)

# for start bot
async def start_telegram_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



@dp.message(lambda message: message.text == "Choice recipient")
async def choice_recipient(message: Message):
    await message.answer("📤 Choose where to send files:", reply_markup=choice_recipient_keyboard)

@dp.message(lambda message: message.text in ["Max", "Erzhan"])
async def set_recipient_choice(message: Message):
    user_id = str(message.from_user.id)
    recipient = EMAIL1 if message.text == "Max" else EMAIL2

    # Обновляем в БД
    update_result = await set_recipient(users_collection, user_id, recipient)

    await message.answer(update_result, reply_markup=main_keyboard)

#Send Photo
@dp.message(lambda message: message.text == "📸 Send Image")
async def request_photo(message: Message):
    await message.answer("We are ready! Send any image.")

#Send many Photos
@dp.message(lambda message: message.text == "📸 Send a lot Images")
async def request_many_images(message: Message, state: FSMContext):
    await state.set_state("awaiting_media_group")
    await state.update_data(media_group_id=None, files=[])
    await message.answer("📥 Ready! Send multiple images or documents now.", reply_markup=send_many_keyboard)


@dp.message(lambda message: message.media_group_id is not None)
async def handle_media_group_file(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = str(message.from_user.id)

    # Первое сообщение задаёт media_group_id
    media_id = data.get("media_group_id") or message.media_group_id
    if not data.get("media_group_id"):
        await state.update_data(media_group_id=media_id)

    files = data.get("files", [])

    # Определим тип файла
    if message.photo:
        file = message.photo[-1]
        ext = "jpg"
    elif message.document:
        file = message.document
        ext = file.file_name.split(".")[-1]
    else:
        return  # Пропускаем неизвестные типы

    filename = f"content/tmp/{user_id}_{uuid4()}.{ext}"

    try:
        file_info = await bot.get_file(file.file_id)
        await bot.download(file_info, filename)
        files.append(filename)
        await state.update_data(files=files)
        logging.info(f"📎 Файл сохранён: {filename}")
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки файла: {e}")


@dp.message(lambda message: message.text == "✅ Send All")
async def send_media_group_files(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get("files", [])

    if not files:
        await message.answer("⚠️ No files received.", reply_markup=main_keyboard)
        return

    user_id = str(message.from_user.id)
    user = await get_by_id(users_collection, user_id)

    success = send_email_with_files(
        to_email=user.recipient,
        subject=f"📸 Media Group {user.name_official}",
        message=f"{user.name_official} sent a media group.",
        file_paths=files
    )

    if success:
        await message.answer("✅ All files sent successfully!", reply_markup=main_keyboard)
    else:
        await message.answer("❌ Failed to send files.", reply_markup=main_keyboard)

    for path in files:
        try:
            os.remove(path)
        except Exception as e:
            logging.warning(f"⚠️ Не удалось удалить файл {path}: {e}")

    await state.clear()



@dp.message(lambda message: message.photo or message.document)
async def receive_any_file(message: Message):
    if message.photo:
        await process_compressed_photo(message)  # 📷 Сжатое фото
    elif message.document and message.document.mime_type.startswith("image/"):
        await process_original_photo(message)  # 🖼 Фото-документ
    elif message.document:  # 📄 Документ любого типа
        await process_document(message)
    else:
        await message.answer("❌ This is not a valid image or document. Please send a valid file.")



# Обработчик сжатых фото
async def process_compressed_photo(message: Message):
    sent_message = await message.answer("📸 Image received, processing...")
    await asyncio.sleep(1)

    photo = message.photo[-1]
    file_path = f"content/images/photo_{message.from_user.id}.jpg"

    try:
        file_info = await bot.get_file(photo.file_id)
        await bot.download(file_info, file_path)

        user_id = str(message.from_user.id)
        user = await get_by_id(users_collection, user_id)
        email_sent = send_email(user.recipient, f"{user.name_official} New Image", f"{user.name_official} sent a compressed image.", file_path)

        new_text = "📨 Your compressed image has been sent successfully!" if email_sent else "❌ Failed to send image. Please try again."
        await sent_message.edit_text(new_text)

    except Exception as e:
        await sent_message.edit_text(f"❌ Error processing the image: {str(e)}")



# Обработчик оригинальных фото (документ)
async def process_original_photo(message: Message):
    sent_message = await message.answer("📸 High-quality image received, processing...")
    await asyncio.sleep(1)

    document = message.document
    file_path = f"content/images/{document.file_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download(file_info, file_path)

        user_id = str(message.from_user.id)
        user = await get_by_id(users_collection, user_id)
        email_sent = send_email(user.recipient, f"{user.name_official} New High-Quality Image", f"{user.name_official} sent a high-quality image.", file_path)

        new_text = "📨 Your high-quality image has been sent successfully!" if email_sent else "❌ Failed to send image. Please try again."
        await sent_message.edit_text(new_text)

    except Exception as e:
        await sent_message.edit_text(f"❌ Error processing the image: {str(e)}")



# Обработчик обычных документов
async def process_document(message: Message):
    sent_message = await message.answer("📄 Document received, processing...")
    await asyncio.sleep(1)

    document = message.document
    file_path = f"content/documents/{document.file_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download(file_info, file_path)

        user_id = str(message.from_user.id)
        user = await get_by_id(users_collection, user_id)
        email_sent = send_email(user.recipient, f"{user.name_official} New Document", f"{user.name_official} sent a document.", file_path)

        new_text = "📨 Your document has been sent successfully!" if email_sent else "❌ Failed to send document. Please try again."
        await sent_message.edit_text(new_text)

    except Exception as e:
        await sent_message.edit_text(f"❌ Error processing the document: {str(e)}")



#Exit
@dp.message(lambda message: message.text == "❌ Exit")
async def exit_to_main_menu(message: Message):
    await message.answer("Returning to main menu.", reply_markup=main_keyboard)

@dp.message(lambda message: message.text == "❌ Cancel")
async def exit_to_main_menu2(message: Message):
    await message.answer("Returning to main menu.", reply_markup=main_keyboard)