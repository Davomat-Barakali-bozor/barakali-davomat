import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor

from db import (
    init_db, get_pending_employees, approve_employee, remove_employee,
    get_active_employees, set_admin_state, get_admin_state,
    create_daily_excel, create_month_excel, now_local
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
admin_ids_env = os.getenv('ADMIN_IDS')
ADMIN_IDS = list(map(int, admin_ids_env.split(','))) if admin_ids_env else []

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add('📊 Kunlik hisobot')
menu.add('📅 Oylik hisobot')
menu.add('🕓 Kutilayotganlar')
menu.add('➕ Xodim qo‘shish')
menu.add('❌ Xodim o‘chirish')
menu.add('📋 Xodimlar ro‘yxati')


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
    text = 'Kutilayotgan xodimlar:\n\n'
    for user_id, full_name, username, phone in rows:
        text += f'{full_name}\nID: {user_id}\nUsername: @{username or "-"}\nTel: {phone or "-"}\n\n'
    await msg.answer(text)


@dp.message_handler(lambda m: m.text == '📋 Xodimlar ro‘yxati')
async def active_list(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    rows = get_active_employees()
    if not rows:
        await msg.answer('Faol xodim yo‘q')
        return
    text = 'Faol xodimlar:\n\n'
    for user_id, full_name, username, phone in rows:
        text += f'{full_name}\nID: {user_id}\nUsername: @{username or "-"}\nTel: {phone or "-"}\n\n'
    await msg.answer(text)


@dp.message_handler(lambda m: m.text == '➕ Xodim qo‘shish')
async def add_mode(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    set_admin_state(msg.from_user.id, 'approve')
    await msg.answer('Tasdiqlash uchun xodim ID sini yuboring')


@dp.message_handler(lambda m: m.text == '❌ Xodim o‘chirish')
async def remove_mode(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    set_admin_state(msg.from_user.id, 'remove')
    await msg.answer('O‘chirish uchun xodim ID sini yuboring')


@dp.message_handler(lambda m: m.text == '📊 Kunlik hisobot')
async def daily_report(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    d = now_local().date()
    bio = create_daily_excel(d)
    await bot.send_document(msg.chat.id, types.InputFile(bio, filename=f'kunlik_hisobot_{d}.xlsx'))


@dp.message_handler(lambda m: m.text == '📅 Oylik hisobot')
async def monthly_report(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    now = now_local()
    bio = create_month_excel(now.year, now.month)
    await bot.send_document(msg.chat.id, types.InputFile(bio, filename=f'oylik_hisobot_{now.year}_{now.month:02d}.xlsx'))


@dp.message_handler()
async def process_id(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    state = get_admin_state(msg.from_user.id)
    if state not in ('approve', 'remove'):
        return
    try:
        employee_id = int(msg.text.strip())
    except ValueError:
        await msg.answer('Faqat raqam yuboring')
        return
    if state == 'approve':
        ok = approve_employee(employee_id)
        await msg.answer('Xodim qo‘shildi ✅' if ok else 'Bunday xodim topilmadi')
    else:
        ok = remove_employee(employee_id)
        await msg.answer('Xodim o‘chirildi ❌' if ok else 'Bunday xodim topilmadi')
    set_admin_state(msg.from_user.id, None)


if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)
