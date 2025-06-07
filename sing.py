# # sing.py
# import os
# import asyncio
# from pyrogram import filters
# from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from client import app
# from bark import SAMPLE_RATE, generate_audio, preload_models
# import torch
# import tempfile
# import soundfile as sf

# preload_models()

# @app.on_message(filters.command("sing") & filters.text)
# async def sing_command(client, message):
#     if len(message.command) < 2:
#         return await message.reply_text("❌ Please provide some text to sing.\n\nUsage: /sing Hello world!", quote=True)

#     text = message.text.split(None, 1)[1]

#     if len(text.split()) > 100:
#         return await message.reply_text("❌ Please limit your text to 100 words for singing.", quote=True)

#     await message.reply_chat_action("record_voice")

#     try:
#         audio_array = generate_audio(text)

#         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
#             sf.write(tmp_wav.name, audio_array.cpu().numpy(), SAMPLE_RATE)
#             wav_path = tmp_wav.name

#         ogg_path = wav_path.replace(".wav", ".ogg")
#         os.system(f'ffmpeg -i "{wav_path}" -c:a libopus "{ogg_path}" -y -loglevel quiet')
#         os.remove(wav_path)

#         await message.reply_voice(voice=ogg_path, caption="🎤 Here's your singing voice!")

#         os.remove(ogg_path)

#     except Exception as e:
#         await message.reply_text(f"⚠️ Error during singing:\n`{e}`", quote=True)
