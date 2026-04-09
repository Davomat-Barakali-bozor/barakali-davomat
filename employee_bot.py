from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

users = {}
registered = {}

phone_btn = ReplyKeyboardMarkup(resize_keyboard=True)
phone_btn.add(KeyboardButton("📞 Telefon yuborish", request_contact=True))

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    user_id = msg.from_user.id
    if user_id in registered:
        await msg.answer("Siz ro‘yxatdan o‘tgansiz.")
        return

    users[user_id] = {"step": "name"}
    await msg.answer("Ism familyangizni yozing:")

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in users:
        return

    users[user_id]["phone"] = msg.contact.phone_number
    users[user_id]["username"] = msg.from_user.username or "-"
    users[user_id]["tg_id"] = msg.from_user.id

    registered[user_id] = {
        "name": users[user_id]["name"],
        "phone": users[user_id]["phone"],
        "username": users[user_id]["username"],
        "tg_id": users[user_id]["tg_id"],
        "approved": False
    }

    await msg.answer(
        "Ro‘yxatdan o‘tish yakunlandi ✅\n"
        "Admin tasdiqlagandan keyin botdan foydalanasiz."
    )

@dp.message_handler()
async def text_handler(msg: types.Message):
    user_id = msg.from_user.id

    if user_id in users and users[user_id].get("step") == "name":
        users[user_id]["name"] = msg.text
        users[user_id]["step"] = "phone"
        await msg.answer("Endi telefon raqamingizni yuboring:", reply_markup=phone_btn)
        return

if name == "__main__":
    executor.start_polling(dp, skip_updates=True)
