from pyrogram import Client, filters
from pyrogram.types import Message
import os
import json
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client_openai = OpenAI(api_key=openai_api_key)

# Path to store enabled chats
CHATBOT_TOGGLE_FILE = "enabled_chats.json"

# Load or initialize enabled chats
def load_enabled_chats():
    if not os.path.exists(CHATBOT_TOGGLE_FILE):
        with open(CHATBOT_TOGGLE_FILE, "w") as f:
            json.dump([], f)
    with open(CHATBOT_TOGGLE_FILE, "r") as f:
        return json.load(f)

def save_enabled_chats(enabled_chats):
    with open(CHATBOT_TOGGLE_FILE, "w") as f:
        json.dump(enabled_chats, f)

enabled_chats = load_enabled_chats()

# Command to toggle chatbot on/off
@Client.on_message(filters.command("chatbot") & (filters.private | filters.group))
async def toggle_chatbot(client: Client, message: Message):
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

# Main handler for chatbot replies
@Client.on_message(filters.text & (filters.private | filters.group))
async def ai_chat_handler(client: Client, message: Message):
    chat_id = str(message.chat.id)

    # Only respond if chatbot is enabled in this chat
    if chat_id not in enabled_chats:
        return

    # Avoid replying to itself or other bots
    if message.from_user.is_bot:
        return

    # In groups, reply only if bot was replied to
    if message.chat.type != "private":
        if not message.reply_to_message or message.reply_to_message.from_user.id != client.me.id:
            return

    prompt = message.text

    try:
        response = client_openai.chat.completions.create(
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
