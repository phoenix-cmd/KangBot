import os
import io
import httpx
from pyrogram import filters
from pyrogram.types import Message
from client import app
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

QUOTE_API_URL = os.getenv("QUOTE_API_URL")

@app.on_message(filters.command("q") & filters.reply)
async def quotely(client, message: Message):
    reply = message.reply_to_message

    if not QUOTE_API_URL:
        await message.reply_text("❌ Quote API URL not configured.")
        return

    if not reply:
        await message.reply_text("❌ You must reply to a message to quote it.")
        return

    try:
        # Prepare the message for the API
        payload = {
            "messages": [{
                "text": reply.text or reply.caption or "",
                "from_user": {
                    "id": reply.from_user.id if reply.from_user else None,
                    "first_name": reply.from_user.first_name if reply.from_user else None,
                    "username": reply.from_user.username if reply.from_user else None
                },
                "message_id": reply.message_id
            }],
            "type": "quote"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{QUOTE_API_URL}/api/quote", json=payload)

        if response.status_code != 200:
            await message.reply_text(f"❌ Quote API error: {response.status_code}\n{response.text}")
            return

        buffer = io.BytesIO(response.content)
        buffer.name = "quote.png"
        buffer.seek(0)

        await message.reply_photo(photo=buffer)

    except Exception as e:
        await message.reply_text(f"❌ Exception occurred:\n`{e}`")
