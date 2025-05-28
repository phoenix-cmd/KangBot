import os
import json
import httpx
from pyrogram import filters
from pyrogram.types import Message
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
GOOGLE_GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_GEMINI_API_KEY}"
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

async def generate_text_gemini(prompt: str) -> str:
    headers = {
        "Content-Type": "application/json",
    }
    json_data = {
        "prompt": {
            "text": prompt
        },
        "temperature": 0.7,
        "maxOutputTokens": 256,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GOOGLE_GEMINI_API_URL, headers=headers, json=json_data)
        response.raise_for_status()
        data = response.json()
        # Depending on the API response format:
        return data.get("candidates", [{}])[0].get("output", "Sorry, I couldn't generate a response.")


def register_chatbot_handlers(app):
    @app.on_message(filters.command("chatbot") & (filters.private | filters.group))
    async def toggle_chatbot(client, message: Message):
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
    async def ai_chat_handler(client, message: Message):
        chat_id = str(message.chat.id)

        if chat_id not in enabled_chats:
            return

        if message.from_user.is_bot:
            return

        # Only reply in groups if bot is replied to
        if message.chat.type != "private":
            if not message.reply_to_message or message.reply_to_message.from_user.id != client.me.id:
                return

        prompt = message.text

        try:
            reply_text = await generate_text_gemini(prompt)
            await message.reply_text(reply_text)
        except Exception as e:
            await message.reply_text("Something went wrong 🤖\n" + str(e))
