from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# bu joy real loyihada DB bo‘ladi
registered = {}

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("🕓 Kutilayotganlar")
menu.add("➕ Xodim qo‘shish")
menu.add("❌ Xodim o‘chirish")

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Siz admin emassiz")
        return
    await msg.answer("Admin panelga xush kelibsiz", reply_markup=menu)

@dp.message_handler(lambda msg: msg.text == "🕓 Kutilayotganlar")
async def pending(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    pending_users = [u for u in registered.values() if not u["approved"]]

    if not pending_users:
        await msg.answer("Kutilayotgan xodim yo‘q")
        return

    text = "Kutilayotganlar:\n\n"
    for u in pending_users:
        text += (
            f"{u['name']}\n"
            f"TG ID: {u['tg_id']}\n"
            f"Username: @{u['username']}\n"
            f"Tel: {u['phone']}\n\n"
        )
    await msg.answer(text)

@dp.message_handler(commands=['approve'])
async def approve(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    try:
        user_id = int(msg.get_args())
        if user_id in registered:
            registered[user_id]["approved"] = True
            await msg.answer("Xodim qo‘shildi ✅")
        else:
            await msg.answer("Bunday TG ID topilmadi")
    except:
        await msg.answer("Masalan: /approve 1735448588")

@dp.message_handler(commands=['remove'])
async def remove(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return

    try:
        user_id = int(msg.get_args())
        if user_id in registered:
            registered[user_id]["approved"] = False
            await msg.answer("Xodim o‘chirildi ❌")
        else:
            await msg.answer("Bunday TG ID topilmadi")
    except:
        await msg.answer("Masalan: /remove 1735448588")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
