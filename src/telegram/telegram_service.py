import logging
import os
import asyncio
from uuid import uuid4

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.telegram.register_fsm import register_router
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from src.user.user_service import set_recipient, get_by_id, increment_sent_emails
from src.configs.mongodb import users_collection
from src.email.email_service import send_email, send_email_with_files
from src.telegram.keyboard import main_keyboard, choice_recipient_keyboard, send_many_keyboard
from src.telegram.user_filter import AccessMiddleware

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN null")

EMAIL1 = os.getenv("TO_EMAIL1")
# EMAIL2 = os.getenv("TO_EMAIL2")
ARIE_EMAIL = os.getenv("ARIE_EMAIL")
logging.basicConfig(level=logging.INFO)
NAME = os.getenv("NAME")
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AccessMiddleware())
dp.include_router(register_router)


os.makedirs("content/images", exist_ok=True)
os.makedirs("content/documents", exist_ok=True)
os.makedirs("content/tmp", exist_ok=True)

# for start bot
async def start_telegram_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



@dp.message(lambda message: message.text == "📤 Choose recipient")
async def choice_recipient(message: Message):
    await message.answer("📤 Choose where to send files:", reply_markup=choice_recipient_keyboard)

@dp.message(lambda message: message.text in ["Max", "Arie"])
async def set_recipient_choice(message: Message):
    user_id = str(message.from_user.id)
    recipient = EMAIL1 if message.text == "Max" else ARIE_EMAIL

    # Обновляем в БД
    update_result = await set_recipient(users_collection, user_id, recipient)

    await message.answer(update_result, reply_markup=main_keyboard)

#Send Photo
# @dp.message(lambda message: message.text == "📸 Send Image")
# async def request_photo(message: Message):
#     await message.answer("We are ready! Send any image.")

#Send many Photos
@dp.message(lambda message: message.text == "📸 Send a lot of Images")
async def request_many_images(message: Message, state: FSMContext):
    await state.set_state("awaiting_media_group")
    await state.update_data(files=[])
    await message.answer("📥 Ready! Send multiple images or documents now. When finished, press ✅ Send All.", reply_markup=send_many_keyboard)



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

    name_official = user.name_official if user.name_official else f"User {user_id}"
    success = send_email_with_files(
        to_email=user.recipient,
        subject=f"{name_official}",
        message=f"{name_official} sent a media group.",
        file_paths=files
    )

    if success:
        await increment_sent_emails(users_collection, user_id)
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
async def receive_any_file(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == "awaiting_media_group":
        # Режим групповой отправки: собираем все файлы в список
        state_data = await state.get_data()
        files = state_data.get("files", [])

        if message.photo:
            file = message.photo[-1]
            ext = "jpg"
        elif message.document:
            file = message.document
            ext = file.file_name.split(".")[-1]
        else:
            await message.answer("❌ Unsupported file type.")
            return

        filename = f"content/tmp/{message.from_user.id}_{uuid4()}.{ext}"
        try:
            file_info = await bot.get_file(file.file_id)
            await bot.download(file_info.file_path, filename)
            files.append(filename)
            await state.update_data(files=files)
            logging.info(f"📎 [GROUP] Файл добавлен: {filename}")
        except Exception as e:
            logging.error(f"❌ Ошибка загрузки файла (группа): {e}")
        return  # не обрабатываем как одиночное сообщение

    # Если не в режиме групповой отправки – обычная логика
    if message.photo:
        await process_compressed_photo(message)
    elif message.document and message.document.mime_type.startswith("image/"):
        await process_original_photo(message)
    elif message.document:
        await process_document(message)
    else:
        await message.answer("❌ This is not a valid image or document.")


# Обработчик сжатых фото
async def process_compressed_photo(message: Message):
    sent_message = await message.answer("📸 Photo received, processing...")
    await asyncio.sleep(1)

    photo = message.photo[-1]
    file_path = f"content/images/photo_{message.from_user.id}.jpg"

    try:
        file_info = await bot.get_file(photo.file_id)
        await bot.download(file_info, file_path)

        user_id = str(message.from_user.id)
        user = await get_by_id(users_collection, user_id)
        name_official = user.name_official if user.name_official else f"User {user_id}"

        email_sent = send_email_with_files(
            to_email=user.recipient,
            subject=f"{name_official}",
            message=f"{name_official} sent a compressed image.",
            file_paths=[file_path]
        )

        new_text = "📨 Your compressed image has been sent successfully!" if email_sent else "❌ Failed to send image. Please try again."
        await sent_message.edit_text(new_text)
        await increment_sent_emails(users_collection, user_id)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error processing the image: {str(e)}")



# Обработчик оригинальных фото (документ)
async def process_original_photo(message: Message):
    sent_message = await message.answer("📸 High-quality photo received, processing...")
    await asyncio.sleep(1)

    document = message.document
    file_path = f"content/images/{document.file_name}"

    try:
        file_info = await bot.get_file(document.file_id)
        await bot.download(file_info, file_path)

        user_id = str(message.from_user.id)
        user = await get_by_id(users_collection, user_id)
        name_official = user.name_official if user.name_official else f"User {user_id}"

        email_sent = send_email_with_files(
            to_email=user.recipient,
            subject=f"{name_official}",
            message=f"{name_official} sent a high-quality image.",
            file_paths=[file_path]
        )
        await increment_sent_emails(users_collection, user_id)

        new_text = "📨 Your high-quality photo has been sent successfully!" if email_sent else "❌ Failed to send photo. Please try again."
        await sent_message.edit_text(new_text)

    except Exception as e:
        await sent_message.edit_text(f"❌ Error processing the photo: {str(e)}")



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
        name_official = user.name_official if user.name_official else f"User {user_id}"

        email_sent = send_email_with_files(
            to_email=user.recipient,
            subject=f"{name_official}",
            message=f"{name_official} sent a document.",
            file_paths=[file_path]
        )
        await increment_sent_emails(users_collection, user_id)

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

@dp.message(lambda message: message.text == "❌ Cancel")
async def cancel_many_images(message: Message, state: FSMContext):
        data = await state.get_data()
        files = data.get("files", [])
        for file_path in files:
            try:
                os.remove(file_path)
                logging.info(f"Файл {file_path} успешно удалён при отмене.")
            except Exception as e:
                logging.error(f"Не удалось удалить файл {file_path}: {e}")
        await state.clear()
        await message.answer("Операция отменена. Все временные файлы удалены.", reply_markup=main_keyboard)

@register_router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📖 *How to use Lawyer Email Bot:*\n\n"
        "1️⃣ To send a single photo or document — just forward it here. Original photos are supported too.\n\n"
        "2️⃣ Want to send multiple files?\n"
        "   Tap *📸 Send a lot of Images*, upload everything you need, then press *✅ Send All* to send them all at once.\n\n"
        "3️⃣ Need to change the recipient?\n"
        "   Tap *📤 Choose recipient* and select one of the options:\n"
        "   - Max\n"
        "   - Arie\n"
        "   - ❌ Cancel to go back\n\n"
        "4️⃣ If something isn't working or you need to restart the bot, just press */start*.\n\n"
        f"5️⃣ Questions? Contact [{NAME}](https://t.me/{NAME[1:]})\n\n"
        "🤖 *Simple. Fast. Confidential.*",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
