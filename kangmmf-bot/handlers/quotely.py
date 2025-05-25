import os
import io
import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message
from client import app  # Your Pyrogram client instance

QUOTE_API_URL = os.getenv("QUOTE_API_URL")  # e.g. "https://your-quote-api-domain/quote"

def is_hex_color(s):
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", s))

def clean_color_arg(arg):
    if is_hex_color(arg):
        return arg if arg.startswith("#") else f"#{arg}"
    # Accept simple color names if needed:
    valid_colors = {
        "white", "black", "red", "green", "blue",
        "yellow", "pink", "purple", "orange", "gray"
    }
    if arg.lower() in valid_colors:
        return arg.lower()
    return None

@app.on_message(filters.command("q"))
async def quotely_handler(client, message: Message):
    if not QUOTE_API_URL:
        await message.reply("Quote API URL is not set in environment variables.")
        return

    # Default params
    bg_color = "white"
    show_avatar = True
    count = 1

    # Parse command args
    args = message.command[1:]
    for arg in args:
        if arg.isdigit():
            count = min(int(arg), 10)
        elif arg.lower() == "avataroff":
            show_avatar = False
        else:
            color = clean_color_arg(arg)
            if color:
                bg_color = color

    # Gather messages for quoting (simple: only the replied message or the current message)
    messages = []
    if message.reply_to_message:
        messages.append(message.reply_to_message)
    else:
        messages.append(message)

    # Support multi-message quote (up to count)
    # This example supports only single message text for simplicity
    # You can extend this to concatenate multiple messages' texts

    text_parts = []
    for msg in messages:
        text = msg.text or msg.caption or ""
        text_parts.append(text)
    full_text = "\n".join(text_parts).strip()
    if not full_text:
        await message.reply("No text found to quote!")
        return

    payload = {
        "text": full_text,
        "background_color": bg_color,
        "show_avatar": show_avatar,
        # Add more fields here if your API supports them (e.g. font size, username, etc.)
    }

    # Call the quote-api
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(QUOTE_API_URL, json=payload) as resp:
                if resp.status != 200:
                    await message.reply(f"Quote API error: {resp.status}")
                    return
                img_bytes = await resp.read()

        await message.reply_photo(photo=io.BytesIO(img_bytes))
    except Exception as e:
        await message.reply(f"Failed to generate quote image: {e}")
