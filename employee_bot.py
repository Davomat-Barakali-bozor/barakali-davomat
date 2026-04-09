import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from db import (
    init_db, set_employee_state, get_employee_state, register_pending_employee,
    is_employee_approved, record_attendance
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
    set_employee_state(msg.from_user.id, state='waiting_name')
    await msg.answer('Ism familyangizni yozing:', reply_markup=menu)


@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state:
        await msg.answer('Avval /start bosing')
        return
    set_employee_state(msg.from_user.id, state='waiting_after_contact', phone=msg.contact.phone_number, full_name=state['full_name'] if 'full_name' in state.keys() else None)
    await msg.answer('Telefon saqlandi. Endi kuting yoki Keldim/Ketdim ni admin tasdiqlagach ishlating.')


@dp.message_handler(lambda m: m.text in ['✅ Keldim', '❌ Ketdim'])
async def action_handler(msg: types.Message):
    if not is_employee_approved(msg.from_user.id):
        await msg.answer('Siz hali admin tomonidan tasdiqlanmagansiz.')
        return
    action = 'checkin' if msg.text == '✅ Keldim' else 'checkout'
    st = get_employee_state(msg.from_user.id)
    phone = st['phone'] if st else None
    full_name = st['full_name'] if st else None
    set_employee_state(msg.from_user.id, state='waiting_photo', action=action, phone=phone, full_name=full_name)
    await msg.answer('Endi rasmingizni yuboring.')


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state or state['state'] != 'waiting_photo':
        await msg.answer('Avval Keldim yoki Ketdim ni bosing.')
        return
    set_employee_state(msg.from_user.id, state='waiting_location', action=state['action'], phone=state['phone'], full_name=state['full_name'], photo_file_id=msg.photo[-1].file_id)
    await msg.answer('Endi lokatsiyani yuboring.')


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def location_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state or state['state'] != 'waiting_location':
        await msg.answer('Avval rasm yuboring.')
        return
    action = state['action']
    phone = state['phone']
    photo_file_id = state['photo_file_id']
    full_name_db, event_time = record_attendance(msg.from_user.id, action, msg.location.latitude, msg.location.longitude, photo_file_id)
    title = '✅ Keldim' if action == 'checkin' else '❌ Ketdim'
    caption = f'{title}\nXodim: {full_name_db}\nUsername: @{msg.from_user.username or "-"}\nTel: {phone or "-"}\nLokatsiya: {msg.location.latitude}, {msg.location.longitude}'
    if ADMIN_CHAT_ID:
        await bot.send_photo(ADMIN_CHAT_ID, photo_file_id, caption=caption)
        await bot.send_location(ADMIN_CHAT_ID, msg.location.latitude, msg.location.longitude)
    set_employee_state(msg.from_user.id, None)
    await msg.answer('Davomat yuborildi ✅')


@dp.message_handler()
async def text_handler(msg: types.Message):
    state = get_employee_state(msg.from_user.id)
    if not state:
        return
    if state['state'] == 'waiting_name':
        set_employee_state(msg.from_user.id, state='waiting_contact', full_name=msg.text.strip())
        await msg.answer('Endi telefon raqamingizni yuboring.', reply_markup=menu)
        return
    if state['state'] == 'waiting_contact':
        await msg.answer('Telefonni tugma orqali yuboring.')
        return
    if state['state'] == 'waiting_after_contact':
        register_pending_employee(msg.from_user.id, state['full_name'] or msg.from_user.full_name, msg.from_user.username, state['phone'] or '-')
        set_employee_state(msg.from_user.id, None)
        await msg.answer('Arizangiz yuborildi. Admin tasdiqlagach foydalanasiz.')
        return


if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)
