from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("📊 Kunlik hisobot")
menu.add("📅 Oylik hisobot")
menu.add("➕ Xodim qo‘shish")
menu.add("❌ Xodim o‘chirish")

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if msg.from_user.id in ADMIN_IDS:
        await msg.answer("Admin panelga xush kelibsiz", reply_markup=menu)
    else:
        await msg.answer("Siz admin emassiz")

@dp.message_handler(lambda msg: msg.text == "📊 Kunlik hisobot")
async def daily(msg: types.Message):
    await msg.answer("Bugungi hisobot")

@dp.message_handler(lambda msg: msg.text == "📅 Oylik hisobot")
async def monthly(msg: types.Message):
    await msg.answer("Oylik hisobot")

@dp.message_handler(lambda msg: msg.text == "➕ Xodim qo‘shish")
async def add_worker(msg: types.Message):
    await msg.answer("Xodim ID yuboring")

@dp.message_handler(lambda msg: msg.text == "❌ Xodim o‘chirish")
async def remove_worker(msg: types.Message):
    await msg.answer("O‘chirish uchun ID yuboring")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
