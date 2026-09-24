import os
import sqlite3
import asyncio
from pyrogram import Client, filters

# Берём ключи из настроек сервера
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

app = Client("saver_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

conn = sqlite3.connect("messages.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        msg_id INTEGER, chat_id INTEGER, sender TEXT, text_content TEXT, archive_msg_id INTEGER,
        PRIMARY KEY (msg_id, chat_id)
    )
''')
conn.commit()

@app.on_message(filters.private & ~filters.me)
async def handle_incoming(client, message):
    sender_name = message.from_user.first_name if message.from_user else "Собеседник"
    text = message.text or message.caption or "[Медиафайл]"
    try:
        archived = await message.forward("me")
        cursor.execute("INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?, ?)",
                       (message.id, message.chat.id, sender_name, text, archived.id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка: {e}")

@app.on_deleted_messages()
async def handle_deleted(client, messages):
    for msg in messages:
        cursor.execute("SELECT sender, text_content FROM messages WHERE msg_id = ? AND chat_id = ?",
                       (msg.id, msg.chat.id))
        row = cursor.fetchone()
        if row:
            sender, text = row
            await client.send_message("me", f"🗑 **УДАЛЕНО СООБЩЕНИЕ!**\n👤 **От:** {sender}\n💬 **Текст:** {text}")
            cursor.execute("DELETE FROM messages WHERE msg_id = ? AND chat_id = ?", (msg.id, msg.chat.id))
            conn.commit()

print(">>> Бот успешно работает 24/7! <<<")
app.run()
