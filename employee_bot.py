import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from db import (
    init_db, set_employee_state, get_employee_state,
    upsert_pending_employee, is_employee_approved,
    record_attendance, get_latest_today_action
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', '0'))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(KeyboardButton('📞 Telefon yuborish', request_contact=True))
menu.add('✅ Keldim', '❌ Ketdim')
menu.add(KeyboardButton('📍 Lokatsiya yuborish', request_location=True))


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    set_employee_state(msg.from_user.id, step='waiting_name')
    await msg.answer('Ism familyangizni yozing:', reply_markup=menu)


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state:
        await msg.answer('Avval /start bosing')
        return
    if state['step'] not in ('waiting_contact', 'waiting_phone'):
        await msg.answer('Avval ism familyangizni kiriting')
        return
    upsert_pending_employee(
        user_id=msg.from_user.id,
        full_name=state['full_name'] or msg.from_user.full_name,
        username=msg.from_user.username,
        phone=msg.contact.phone_number,
    )
    set_employee_state(msg.from_user.id, None)
    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"Yangi ariza keldi ⏳\n\n"
            f"Xodim: {state['full_name'] or msg.from_user.full_name}\n"
            f"ID: {msg.from_user.id}\n"
            f"Username: @{msg.from_user.username or '-'}\n"
            f"Tel: {msg.contact.phone_number}"
        )
    await msg.answer('Arizangiz yuborildi. Admin tasdiqlashini kuting ✅')


@dp.message_handler(lambda m: m.text in ['✅ Keldim', '❌ Ketdim'])
async def action_handler(msg: types.Message):
    if not is_employee_approved(msg.from_user.id):
        await msg.answer('Siz hali admin tomonidan tasdiqlanmagansiz.')
        return

    latest = get_latest_today_action(msg.from_user.id)
    if msg.text == '✅ Keldim' and latest == 'checkin':
        await msg.answer('Siz bugun allaqachon Keldim yuborgansiz.')
        return
    if msg.text == '❌ Ketdim' and latest != 'checkin':
        await msg.answer('Avval Keldim yuborishingiz kerak.')
        return

    action = 'checkin' if msg.text == '✅ Keldim' else 'checkout'
    set_employee_state(msg.from_user.id, step='waiting_photo', action=action)
    await msg.answer('Endi rasmingizni yuboring.')


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state or state['step'] != 'waiting_photo':
        await msg.answer('Avval Keldim yoki Ketdim ni bosing.')
        return
    set_employee_state(msg.from_user.id, step='waiting_location', action=state['action'], photo_file_id=msg.photo[-1].file_id)
    await msg.answer('Endi lokatsiyani yuboring.')


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def location_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state or state['step'] != 'waiting_location':
        await msg.answer('Avval rasm yuboring.')
        return
    full_name, event_time = record_attendance(
        user_id=msg.from_user.id,
        action=state['action'],
        latitude=msg.location.latitude,
        longitude=msg.location.longitude,
        photo_file_id=state['photo_file_id'],
    )
    title = '✅ Keldim' if state['action'] == 'checkin' else '❌ Ketdim'
    caption = (
        f"{title}\n"
        f"Xodim: {full_name}\n"
        f"Username: @{msg.from_user.username or '-'}\n"
        f"Lokatsiya: {msg.location.latitude}, {msg.location.longitude}\n"
        f"Vaqt: {event_time.strftime('%H:%M')}"
    )
    if ADMIN_CHAT_ID:
        await bot.send_photo(ADMIN_CHAT_ID, state['photo_file_id'], caption=caption)
        await bot.send_location(ADMIN_CHAT_ID, msg.location.latitude, msg.location.longitude)
    set_employee_state(msg.from_user.id, None)
    await msg.answer('Davomat yuborildi ✅')


@dp.message_handler()
async def text_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state:
        return
    if state['step'] == 'waiting_name':
        set_employee_state(msg.from_user.id, step='waiting_contact', full_name=msg.text.strip())
        await msg.answer('Endi telefon raqamingizni yuboring.', reply_markup=menu)
        return
    if state['step'] == 'waiting_contact':
        await msg.answer('Telefonni tugma orqali yuboring.')
        return


if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)
