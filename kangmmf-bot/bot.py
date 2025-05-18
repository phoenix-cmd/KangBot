import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from handlers.kang import kang_handler
from handlers.mmf import mmf_handler
from handlers.group_admin import group_admin_handlers

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("kangmmf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

app.add_handler(mmf_handler)
app.add_handler(kang_handler)

for handler in group_admin_handlers:
    app.add_handler(handler)

@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text("""👋 Hello! I'm AFC-Bot.

I can help you:
📌 Kang stickers
🖼️ Create memes from images/videos

Here's what I can do:

• `/kang` — Reply to a sticker, photo, or image to steal it into your pack.
• `/mmf top ; bottom` — Meme Maker Format! Reply to an image/sticker/video with your meme text.

🛠 Example:  
`/mmf when the code works ; but you don't know why`

✨ More features coming soon.  
Made with ❤️ by AFC Engineers.""")

if __name__ == "__main__":
    while True:
        try:
            app.run()
        except FloodWait as e:
            print(f"FloodWait: Need to wait {e.x} seconds. Sleeping...")
            asyncio.run(asyncio.sleep(e.x))
            print("Resuming...")
