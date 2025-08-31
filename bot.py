import asyncio
import os
import sqlite3
from telethon import TelegramClient, events, Button
from telethon.errors import UserNotParticipantError

# اطلاعات ربات
api_id = 123456  # جایگزین کن با api_id خودت
api_hash = 'your_api_hash_here'
bot_token = 'your_bot_token_here'
owner = 123456789  # ایدی عددی ادمین

# اتصال به تلگرام
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# اتصال به دیتابیس
conn = sqlite3.connect('channels.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, username TEXT UNIQUE)')
conn.commit()

# گرفتن لیست کانال‌ها از دیتابیس
def get_required_channels():
    cursor.execute('SELECT username FROM channels')
    return [row[0] for row in cursor.fetchall()]

# بررسی عضویت کاربر
async def check_membership(user_id):
    not_joined = []
    for channel in get_required_channels():
        try:
            await client.get_participant(channel, user_id)
        except UserNotParticipantError:
            not_joined.append(channel)
        except:
            continue
    return not_joined

# ارسال دکمه‌های عضویت
async def send_join_prompt(event, not_joined):
    buttons = [[Button.url(f'عضویت در @{ch}', f'https://t.me/{ch}')] for ch in not_joined]
    buttons.append([Button.inline('بررسی عضویت ✅', data='check_membership')])
    await event.respond('برای استفاده از ربات، لطفاً ابتدا در کانال‌های زیر عضو شوید:', buttons=buttons)

# هندل پیام‌های جدید
@client.on(events.NewMessage)
async def handler(event):
    user_id = event.sender_id
    if event.text.startswith('/start'):
        not_joined = await check_membership(user_id)
        if not_joined:
            await send_join_prompt(event, not_joined)
        else:
            await event.respond('✅ خوش اومدی! عضویت شما تایید شد.')
    elif event.text.startswith('/addchannel') and user_id == owner:
        username = event.text.split(' ')[1].replace('@', '')
        try:
            cursor.execute('INSERT INTO channels (username) VALUES (?)', (username,))
            conn.commit()
            await event.respond(f'✅ کانال @{username} اضافه شد.')
        except sqlite3.IntegrityError:
            await event.respond('⚠️ این کانال قبلاً اضافه شده.')
    else:
        not_joined = await check_membership(user_id)
        if not_joined:
            await send_join_prompt(event, not_joined)
        else:
            await event.respond('🎵 پیام شما دریافت شد. آماده‌ام برای جستجوی آهنگ!')

# هندل دکمه بررسی عضویت
@client.on(events.CallbackQuery(data=b'check_membership'))
async def recheck(event):
    user_id = event.sender_id
    not_joined = await check_membership(user_id)
    if not_joined:
        await send_join_prompt(event, not_joined)
    else:
        await event.respond('✅ عضویت شما تایید شد! حالا می‌تونی از ربات استفاده کنی.')

# اجرای ربات
print("ربات فعال شد ✅")
client.run_until_disconnected()
