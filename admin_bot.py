import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.utils import executor

from db import (
    init_db, get_pending_employees, approve_employee, remove_employee,
    get_approved_employees, create_daily_excel, create_month_excel,
    now_local
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
admin_ids_env = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x) for x in admin_ids_env.split(',') if x.strip().isdigit()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add('📊 Kunlik hisobot', '📅 Oylik hisobot')
menu.add('🕓 Kutilayotganlar', '📋 Xodimlar ro‘yxati')


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer('Siz admin emassiz')
        return
    await msg.answer('Admin panelga xush kelibsiz', reply_markup=menu)


@dp.message_handler(lambda m: m.text == '🕓 Kutilayotganlar')
async def pending(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    rows = get_pending_employees()
    if not rows:
        await msg.answer('Kutilayotgan xodim yo‘q')
        return
    for row in rows:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton('✅ Tasdiqlash', callback_data=f"approve:{row['user_id']}"),
            InlineKeyboardButton('❌ Rad etish', callback_data=f"reject:{row['user_id']}")
        )
        text = (
            f"Xodim: {row['full_name']}\n"
            f"ID: {row['user_id']}\n"
            f"Username: @{row['username'] or '-'}\n"
            f"Tel: {row['phone'] or '-'}"
        )
        await msg.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith('approve:'))
async def approve_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Ruxsat yo‘q', show_alert=True)
        return
    user_id = int(call.data.split(':')[1])
    ok = approve_employee(user_id)
    if ok:
        try:
            await bot.send_message(user_id, 'Siz admin tomonidan tasdiqlandingiz ✅')
        except Exception:
            pass
        await call.message.edit_text(call.message.text + '\n\nTasdiqlandi ✅')
    else:
        await call.answer('Topilmadi', show_alert=True)


@dp.callback_query_handler(lambda c: c.data.startswith('reject:'))
async def reject_cb(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer('Ruxsat yo‘q', show_alert=True)
        return
    user_id = int(call.data.split(':')[1])
    ok = remove_employee(user_id)
    if ok:
        try:
            await bot.send_message(user_id, 'Arizangiz rad etildi ❌')
        except Exception:
            pass
        await call.message.edit_text(call.message.text + '\n\nRad etildi ❌')
    else:
        await call.answer('Topilmadi', show_alert=True)


@dp.message_handler(lambda m: m.text == '📋 Xodimlar ro‘yxati')
async def employees_list(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    rows = get_approved_employees()
    if not rows:
        await msg.answer('Tasdiqlangan xodim yo‘q')
        return
    text = 'Tasdiqlangan xodimlar:\n\n'
    for row in rows:
        text += (
            f"{row['full_name']}\n"
            f"ID: {row['user_id']}\n"
            f"Username: @{row['username'] or '-'}\n"
            f"Tel: {row['phone'] or '-'}\n\n"
        )
    await msg.answer(text)


@dp.message_handler(lambda m: m.text == '📊 Kunlik hisobot')
async def daily_report(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    d = now_local().date()
    bio = create_daily_excel(d)
    await bot.send_document(msg.chat.id, InputFile(bio, filename=f'kunlik_hisobot_{d}.xlsx'))


@dp.message_handler(lambda m: m.text == '📅 Oylik hisobot')
async def monthly_report(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    now = now_local()
    bio = create_month_excel(now.year, now.month)
    await bot.send_document(msg.chat.id, InputFile(bio, filename=f'oylik_hisobot_{now.year}_{now.month:02d}.xlsx'))


if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)
