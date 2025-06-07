import os
import asyncio
import yt_dlp
from pyrogram import filters, Client
from pyrogram.types import Message
import logging
from client import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MUSIC_DIR = "data/music"
os.makedirs(MUSIC_DIR, exist_ok=True)

# YouTube-DL options
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': os.path.join(MUSIC_DIR, '%(title)s.%(ext)s'),
}

@app.on_message(filters.command(["play", "p"]))
async def play_music(client, message: Message):
    """Play music in voice chat."""
    try:
        # Check if user is in voice chat
        if not message.from_user.voice:
            return await message.reply("❌ You need to be in a voice chat to use this command!")

        # Get voice chat
        voice_chat = message.from_user.voice.chat
        if not voice_chat:
            return await message.reply("❌ No voice chat found!")

        # Get song URL from command
        args = message.text.split()
        if len(args) < 2:
            return await message.reply("❌ Please provide a YouTube URL!\nUsage: `/play <url>`")

        url = args[1]
        
        # Download the song
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info['title']
                file_path = os.path.join(MUSIC_DIR, f"{title}.mp3")
        except Exception as e:
            logger.error(f"Error downloading song: {e}")
            return await message.reply("❌ Failed to download the song!")

        # Join voice chat and play
        try:
            voice = await voice_chat.join()
            voice.play(file_path)
            await message.reply(f"🎵 Now playing: {title}")
        except Exception as e:
            logger.error(f"Error playing song: {e}")
            await message.reply("❌ Failed to play the song!")

    except Exception as e:
        logger.error(f"Error in play_music: {e}")
        await message.reply("❌ An error occurred while playing music.")

@app.on_message(filters.command(["stop", "leave"]))
async def stop_music(client, message: Message):
    """Stop music and leave voice chat."""
    try:
        if not message.from_user.voice:
            return await message.reply("❌ You need to be in a voice chat to use this command!")

        voice_chat = message.from_user.voice.chat
        if not voice_chat:
            return await message.reply("❌ No voice chat found!")

        # Leave voice chat
        try:
            await voice_chat.leave()
            await message.reply("⏹️ Stopped music and left voice chat!")
        except Exception as e:
            logger.error(f"Error leaving voice chat: {e}")
            await message.reply("❌ Failed to leave voice chat!")

    except Exception as e:
        logger.error(f"Error in stop_music: {e}")
        await message.reply("❌ An error occurred while stopping music.") 
