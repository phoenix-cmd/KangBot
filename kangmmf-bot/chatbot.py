from pyrogram import filters
from pyrogram.types import Message
from openai import OpenAI
import os
import json

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set")

client = OpenAI()

CHATBOT_TOGGLE_FILE = "enabled_chats.json"

def load_enabled_chats():
    try:
        with open(CHATBOT_TOGGLE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(CHATBOT_TOGGLE_FILE, "w") as f:
            json.dump([], f)
        return []

def save_enabled_chats(enabled_chats):
    with open(CHATBOT_TOGGLE_FILE, "w") as f:
        json.dump(enabled_chats, f)

enabled_chats = load_enabled_chats()

def register_chatbot_handlers(app):
    @app.on_message(filters.command("chatbot") & (filters.private | filters.group))
    async def toggle_chatbot(client_pyrogram, message: Message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: `/chatbot on` or `/chatbot off`", quote=True)

        status = message.command[1].lower()
        chat_id = str(message.chat.id)

        if status == "on":
            if chat_id not in enabled_chats:
                enabled_chats.append(chat_id)
                save_enabled_chats(enabled_chats)
                await message.reply_text("✅ Chatbot has been *enabled* here.")
            else:
                await message.reply_text("🤖 Chatbot is *already enabled*.")
        elif status == "off":
            if chat_id in enabled_chats:
                enabled_chats.remove(chat_id)
                save_enabled_chats(enabled_chats)
                await message.reply_text("❌ Chatbot has been *disabled* here.")
            else:
                await message.reply_text("🤖 Chatbot is *already disabled*.")
        else:
            await message.reply_text("Usage: `/chatbot on` or `/chatbot off`")

    @app.on_message(filters.text & ~(filters.command("chatbot")) & (filters.private | filters.group))
    async def ai_chat_handler(client_pyrogram, message: Message):
        chat_id = str(message.chat.id)

        if chat_id not in enabled_chats:
            return

        if message.from_user.is_bot:
            return

        if message.chat.type != "private":
            if not message.reply_to_message or message.reply_to_message.from_user.id != client_pyrogram.me.id:
                return

        prompt = message.text

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly Telegram bot."},
                    {"role": "user", "content": prompt},
                ],
            )

            reply_text = response.choices[0].message.content.strip()
            await message.reply_text(reply_text)

        except Exception as e:
            await message.reply_text("Something went wrong 🤖\n" + str(e))
