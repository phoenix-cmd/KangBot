# voice.py

from pyrogram import Client, filters
from gtts import gTTS
import os
import asyncio

from client import app  # make sure your Client instance is called `app` in client.py

@app.on_message(filters.command("voice") & filters.text)
async def voice_command(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Please provide some text.\n\n**Usage:** `/voice Hello!`", quote=True)

    text = message.text.split(None, 1)[1]

    try:
        # Generate speech
        tts = gTTS(text=text, lang='en')
        file_name = f"voice_{message.from_user.id}.mp3"
        tts.save(file_name)

        # Send voice note
        await message.reply_voice(voice=file_name, caption="🔊 Here you go!")

        await asyncio.sleep(1)  # wait to ensure sending completes
        os.remove(file_name)

    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred:\n`{e}`", quote=True)
