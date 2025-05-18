from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram import Client
from handlers.kang import kang_handler
from handlers.mmf import mmf_handler
from handlers.group_admin import group_admin_handlers

for handler in group_admin_handlers:
    app.add_handler(handler)

API_ID = 123456   # Replace with your API ID
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

app = Client("kangmmf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app.add_handler(mmf_handler)
app.add_handler(kang_handler)

@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text("Hi! I can /kang stickers, /mmf videos, and manage your group.")

if __name__ == "__main__":
    app.run()