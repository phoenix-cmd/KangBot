import os
from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.kang import kang_handler
from handlers.mmf import mmf_handler
from handlers.group_admin import group_admin_handlers

# Load API credentials from environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize the bot client
app = Client("kangmmf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Add command handlers
app.add_handler(mmf_handler)
app.add_handler(kang_handler)

for handler in group_admin_handlers:
    app.add_handler(handler)

# /start command for private chat
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text("👋 Hi! I can:\n\n"
                              "📌 /kang stickers\n"
                              "📼 /mmf videos\n"
                              "🛡️ Manage your group.\n\n"
                              "➕ Add me to a group and make me admin!")

if __name__ == "__main__":
    app.run()
