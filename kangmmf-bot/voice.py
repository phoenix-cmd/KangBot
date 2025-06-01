# voice.py

from pyrogram import Client, filters
from gtts import gTTS
import os
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from client import app

VOICE_STORE = {}

@app.on_message(filters.command("voice") & filters.text)
async def voice_command(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Please provide some text.\n\n**Usage:** `/voice Hello!`", quote=True)

    text = message.text.split(None, 1)[1]
    user_id = message.from_user.id

    try:
        tts = gTTS(text=text, lang='en')
        file_name = f"voice_{user_id}.mp3"
        tts.save(file_name)

        sent = await message.reply_voice(
            voice=file_name,
            caption="🔊 Here's your voice note!",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🔁 Replay", callback_data=f"replay_{user_id}"),
                    InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{user_id}")
                ]]
            )
        )

        VOICE_STORE[str(sent.id)] = file_name  # store filename for replay
        await asyncio.sleep(1)

    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred:\n`{e}`", quote=True)


@app.on_callback_query(filters.regex(r"^(replay|delete)_(\d+)$"))
async def callback_handler(client, query: CallbackQuery):
    action, owner_id = query.data.split("_", 1)

    # Check if the user pressing the button is the original sender
    if str(query.from_user.id) != owner_id:
        return await query.answer("⛔ You're not allowed to do that.", show_alert=True)

    if action == "replay":
        voice_path = VOICE_STORE.get(str(query.message.id))
        if voice_path and os.path.exists(voice_path):
            await query.message.reply_voice(voice=voice_path, caption="🔁 Replaying!")
        await query.answer()

    elif action == "delete":
        try:
            await query.message.delete()
            await query.answer("🗑️ Deleted!")
        except:
            await query.answer("❌ Couldn't delete.")
