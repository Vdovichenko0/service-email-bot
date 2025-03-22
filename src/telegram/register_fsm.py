import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.user.user_service import register_user
from src.configs.mongodb import users_collection
from src.telegram.keyboard import main_keyboard, choice_recipient_register_keyboard

EMAIL1 = os.getenv("TO_EMAIL1")
# EMAIL2 = os.getenv("TO_EMAIL2")
ARIE_EMAIL = os.getenv("ARIE_EMAIL")
register_router = Router()

class RegisterStates(StatesGroup):
    entering_name_official = State()
    choosing_recipient = State()


@register_router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    existing_user = await users_collection.find_one({"_id": user_id})
    if existing_user:
        await message.answer("✅ You are already registered!", reply_markup=main_keyboard)
        return

    await state.clear()
    await message.answer("👤 Please enter your full official name:")
    await state.set_state(RegisterStates.entering_name_official)


@register_router.message(RegisterStates.entering_name_official)
async def handle_name_official(message: Message, state: FSMContext):
    await state.update_data(name_official=message.text)
    await message.answer("👥 Choose a recipient:", reply_markup=choice_recipient_register_keyboard)
    await state.set_state(RegisterStates.choosing_recipient)


@register_router.message(RegisterStates.choosing_recipient)
async def handle_recipient_choice(message: Message, state: FSMContext):
    if message.text not in ["Max email", "Erzhan email"]:
        await message.answer("❌ Invalid choice. Please select Max or Erzhan.")
        return

    recipient = EMAIL1 if message.text == "Max email" else ARIE_EMAIL
    user_data = await state.get_data()

    user_id = str(message.from_user.id)
    name = message.from_user.full_name
    nickname = message.from_user.username or ""
    phone_number = None

    response_message = await register_user(
        users_collection=users_collection,
        user_id=user_id,
        name=name,
        nickname=nickname,
        phone_number=phone_number,
        name_official=user_data["name_official"],
        recipient=recipient
    )

    await message.answer(response_message, reply_markup=main_keyboard)
    await state.clear()