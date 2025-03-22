from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Send Image")],
        [KeyboardButton(text="📸 Send a lot Images")],
        [KeyboardButton(text="Choice recipient")],
    ],
    resize_keyboard=True
)

choice_recipient_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Max")],  # EMAIL1
        [KeyboardButton(text="Erzhan")],  # EMAIL2
        [KeyboardButton(text="❌ Cancel")]
    ],
    resize_keyboard=True
)

choice_recipient_register_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Max email")],  # EMAIL1
        [KeyboardButton(text="Erzhan email")],  # EMAIL2
    ],
    resize_keyboard=True
)

exit_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Exit")]
    ],
    resize_keyboard=True
)

send_many_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Send All")],
        [KeyboardButton(text="❌ Cancel")]
    ],
    resize_keyboard=True
)
