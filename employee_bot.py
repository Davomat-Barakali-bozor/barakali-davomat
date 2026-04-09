from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton("📞 Telefon yuborish", request_contact=True))
menu.add("✅ Keldim", "❌ Ketdim")
menu.add(KeyboardButton("📍 Lokatsiya yuborish", request_location=True))

user_state = {}

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "Xodim davomat botiga xush kelibsiz.\n\n"
        "1) Telefon yuboring\n"
        "2) Keldim yoki Ketdim bosing\n"
        "3) Rasm yuboring\n"
        "4) Lokatsiya yuboring",
        reply_markup=menu
    )

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(msg: types.Message):
    user_state[msg.from_user.id] = {
        "phone": msg.contact.phone_number,
        "full_name": msg.from_user.full_name,
        "username": msg.from_user.username or "-"
    }
    await msg.answer("Telefon raqamingiz saqlandi.")

@dp.message_handler(lambda msg: msg.text in ["✅ Keldim", "❌ Ketdim"])
async def action_handler(msg: types.Message):
    if msg.from_user.id not in user_state:
        await msg.answer("Avval telefon raqamingizni yuboring.")
        return
    user_state[msg.from_user.id]["action"] = msg.text
    await msg.answer("Endi rasmingizni yuboring.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(msg: types.Message):
    if msg.from_user.id not in user_state or "action" not in user_state[msg.from_user.id]:
        await msg.answer("Avval Keldim yoki Ketdim ni bosing.")
        return
    user_state[msg.from_user.id]["photo_id"] = msg.photo[-1].file_id
    await msg.answer("Endi lokatsiyangizni yuboring.")

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def location_handler(msg: types.Message):
    data = user_state.get(msg.from_user.id)
    if not data or "photo_id" not in data:
        await msg.answer("Avval rasm yuboring.")
        return

    lat = msg.location.latitude
    lon = msg.location.longitude
    action = data["action"]
    phone = data["phone"]
    full_name = data["full_name"]
    username = data["username"]
    photo_id = data["photo_id"]

    caption = (
        f"{action}\n"
        f"Xodim: {full_name}\n"
        f"Username: @{username}\n"
        f"Tel: {phone}\n"
        f"Lokatsiya: {lat}, {lon}"
    )

    if ADMIN_CHAT_ID:
        await bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=caption)
        await bot.send_location(ADMIN_CHAT_ID, latitude=lat, longitude=lon)

    await msg.answer("Davomat yuborildi ✅")
    user_state[msg.from_user.id].pop("action", None)
    user_state[msg.from_user.id].pop("photo_id", None)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
