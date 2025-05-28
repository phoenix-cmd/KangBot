import os
import json
import httpx
from pyrogram import filters
from pyrogram.types import Message

HF_API_URL = "https://api-inference.huggingface.co/models/gpt2"  # Change if you want another model
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

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

async def generate_text_hf(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 150,
            "do_sample": True,
            "top_p": 0.95,
            "temperature": 0.7
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        return "Sorry, I couldn't generate a response."

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

        # Only reply to the bot in groups if it's replied to
        if message.chat.type != "private":
            if not message.reply_to_message or message.reply_to_message.from_user.id != client.me.id:
                return

        prompt = message.text

        try:
            reply_text = await generate_text_hf(prompt)
            await message.reply_text(reply_text)
        except Exception as e:
            await message.reply_text("Something went wrong 🤖\n" + str(e))
