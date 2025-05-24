# import os
# import asyncio
# import shutil
# from pyrogram import filters
# from pyrogram.types import Message
# from pyrogram.errors import FloodWait
# import time
# from client import app  # Moved Client init to client.py

# from handlers.kang import kang_handler
# from handlers.mmf import mmf_handler
# from handlers.group_admin import group_admin_handlers
# from handlers.quotely import quotely_handler

# print("✅ FFmpeg found at:", shutil.which("ffmpeg"))

# # Add handlers
# app.add_handler(mmf_handler)
# app.add_handler(kang_handler)
# app.add_handler(quotely_handler)
# for handler in group_admin_handlers:
#     app.add_handler(handler)

# @app.on_message(filters.command("start") & filters.private)
# async def start(_, message: Message):
#     await message.reply_text(
#         """👋 Hello! I'm AFC-Bot.

# I can help you:
# 📌 Kang stickers
# 🖼️ Create memes from images/videos

# Here's what I can do:

# • `/kang` — Reply to a sticker, photo, or image to steal it into your pack.
# • `/mmf top ; bottom` — Meme Maker Format! Reply to an image/sticker/video with your meme text.

# 🛠 Example:  
# `/mmf when the code works ; but you don't know why`

# ✨ More features coming soon.  
# Made with ❤️ by AFC Engineers."""
#     )

# if __name__ == "__main__":
#     try:
#         app.run()
#     except FloodWait as e:
#         print(f"FloodWait: Need to wait {e.value} seconds. Sleeping...")
#         time.sleep(e.value)


import os
import asyncio
import shutil
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import time
from client import app  # Moved Client init to client.py

from handlers.kang import kang_handler
from handlers.mmf import mmf_handler
from handlers.group_admin import group_admin_handlers
from handlers.quotely import quotely_handler

from music import init_music  # <-- import the music initializer

print("✅ FFmpeg found at:", shutil.which("ffmpeg"))

# Add handlers
app.add_handler(mmf_handler)
app.add_handler(kang_handler)
app.add_handler(quotely_handler)
for handler in group_admin_handlers:
    app.add_handler(handler)

# Initialize music handlers, commands, and pytgcalls
init_music(app)

@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text(
        """👋 Hello! I'm AFC-Bot.

I can help you:
📌 Kang stickers
🖼️ Create memes from images/videos

Here's what I can do:

• `/kang` — Reply to a sticker, photo, or image to steal it into your pack.
• `/mmf top ; bottom` — Meme Maker Format! Reply to an image/sticker/video with your meme text.

🛠 Example:  
`/mmf when the code works ; but you don't know why`

✨ More features coming soon.  
Made with ❤️ by AFC Engineers."""
    )

if __name__ == "__main__":
    try:
        app.run()
    except FloodWait as e:
        print(f"FloodWait: Need to wait {e.value} seconds. Sleeping...")
        time.sleep(e.value)

