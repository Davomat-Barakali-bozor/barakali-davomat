PRO SQLITE DAVOMAT TIZIMI

Admin bot imkoniyatlari:
- Kutilayotgan xodimlar
- Approve / Reject inline tugmalar
- Tasdiqlangan xodimlar ro'yxati
- Kunlik Excel hisobot
- Oylik Excel hisobot

Xodim bot imkoniyatlari:
- Ism familya bilan ro'yxatdan o'tish
- Telefon yuborish
- Tasdiqlangandan keyin Keldim / Ketdim
- Rasm yuborish
- Lokatsiya yuborish
- Adminga foto + lokatsiya xabari

Railway admin bot variables:
BOT_TOKEN=admin token
ADMIN_IDS=sizning tg id
DB_PATH=/data/davomat.db
TIMEZONE=Asia/Tashkent

Railway employee bot variables:
BOT_TOKEN=xodim token
ADMIN_CHAT_ID=admin chat id
DB_PATH=/data/davomat.db
TIMEZONE=Asia/Tashkent

Start command:
admin -> python admin_bot.py
employee -> python employee_bot.py

Ikkala servicega ham volume mount path: /data
