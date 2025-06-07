import os
import asyncio
import shutil
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import time
import logging
from voice import *  

from client import app
from handlers.group_admin import (
    kick_user, ban_user, unban_user, mute_user, unmute_user,
    warn_user, view_warnings, delete_warning, spam_check, spam_settings
)
from handlers.kang import kang_handler
from handlers.mmf import mmf_handler
from handlers.quotely import quotely
# Removed explicit imports of word_chain handlers
from handlers.genshin import save_genshin_uid, show_genshin_profile, show_character_card, refresh_profile
import handlers.tree_grow 
import handlers.word_chain  # This loads the handlers so decorators run

print("✅ FFmpeg found at:", shutil.which("ffmpeg"))

# Add handlers
app.add_handler(mmf_handler)
app.add_handler(kang_handler)
app.add_handler(quotely)

# Add group admin handlers
app.add_handler(kick_user)
app.add_handler(ban_user)
app.add_handler(unban_user)
app.add_handler(mute_user)
app.add_handler(unmute_user)
app.add_handler(warn_user)
app.add_handler(view_warnings)
app.add_handler(delete_warning)
app.add_handler(spam_check)
app.add_handler(spam_settings)

# Removed word chain game handlers here (decorators handle registration)

# Add Genshin Impact handlers
app.add_handler(save_genshin_uid)
app.add_handler(show_genshin_profile)
app.add_handler(show_character_card)
app.add_handler(refresh_profile)

# Start command handler
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply_text(
        """👋 Hello! I'm AFC-Bot.

I can help you with:
📌 Kang stickers
🖼️ Create memes from images/videos
🛡️ Group administration
🛠️ Spam protection
🎮 Word Chain Game
🎮 Genshin Impact Profile

Here's what I can do:

Sticker & Media:
• `/kang` — Reply to a sticker, photo, or image to steal it into your pack.
• `/mmf top ; bottom` — Meme Maker Format! Reply to an image/sticker/video with your meme text.

Genshin Impact:
• `/gilogin <uid>` — Save your Genshin Impact UID
• `/myc` — View your Genshin Impact profile and characters
Features:
- View Adventure Rank and World Level
- List all your characters
- View detailed character cards
- Check artifacts and talents

Word Chain Game:
• `/wordchain` or `/wc` — Start a new word chain game
• `/endchain` or `/ec` — End the current game
• `/chainstats` or `/cs` — Show current game stats
Rules:
- Words must be at least 3 letters
- Each word must start with the last letter of previous word
- No repeating words
- Game times out after 5 minutes of inactivity

Group Admin:
• `/kick` — Kick a user from the group
• `/ban` — Ban a user from the group
• `/unban` — Unban a user
• `/mute` — Mute a user (with optional duration: 1h, 30m, 2d)
• `/unmute` — Unmute a user

Warning System:
• `/warn` — Warn a user
• `/warnings` — View user's warnings
• `/delwarn` — Remove a warning

Spam Protection:
• `/spamsettings` — Configure spam protection
• Auto-detects and handles:
  - Message flooding
  - Link spam
  - Media spam

🛠 Examples:  
`/mmf when the code works ; but you don't know why`
`/mute 1h` (mute for 1 hour)
`/warn Spamming in chat`
`/wordchain` (start a word chain game)
`/gilogin 123456789` (save your Genshin UID)
`/myc` (view your Genshin profile)

✨ More features coming soon.  
Made with ❤️ by AFC Engineers."""
    )

if __name__ == "__main__":
    try:
        app.run()
    except FloodWait as e:
        logging.warning(f"FloodWait: Need to wait {e.value} seconds. Sleeping...")
        time.sleep(e.value)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
