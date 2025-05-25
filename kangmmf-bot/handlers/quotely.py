# import os
# import io
# import httpx
# from pyrogram import filters
# from pyrogram.types import Message
# from client import app
# from dotenv import load_dotenv

# load_dotenv()

# QUOTE_API_URL = os.getenv("QUOTE_API_URL", "https://bot.lyo.su/quote")
# BOT_TOKEN = os.getenv("BOT_TOKEN")  # Load your bot token from .env

# async def fetch_user_photo(client, user_id):
#     """Fetch user's biggest profile photo URL from Telegram."""
#     try:
#         photos = await client.get_profile_photos(user_id, limit=1)
#         if photos.total_count > 0:
#             photo = photos.photos[0]
#             biggest = max(photo, key=lambda p: p.width * p.height)
#             file = await client.download_media(biggest.file_id, file=io.BytesIO())
#             return None  # No direct URL available, return None for now
#     except Exception:
#         return None
#     return None

# def extract_entities(message: Message):
#     if not message.entities:
#         return []

#     entities = []
#     for e in message.entities:
#         type_map = {
#             "bold": "bold",
#             "italic": "italic",
#             "underline": "underline",
#             "strikethrough": "strikethrough",
#             "code": "code",
#             "pre": "pre",
#             "text_link": "text_link",
#             "mention": "mention",
#             "url": "url",
#             "email": "email",
#         }
#         entity_type = type_map.get(e.type)
#         if not entity_type:
#             continue

#         ent = {
#             "type": entity_type,
#             "offset": e.offset,
#             "length": e.length,
#         }
#         if e.type == "text_link" and e.url:
#             ent["url"] = e.url
#         entities.append(ent)
#     return entities

# async def build_user_info(client, user):
#     """Build user info dict with fallback avatar."""
#     if not user:
#         return {
#             "id": 0,
#             "name": "Unknown",
#             "photo": {"url": "https://dummyimage.com/100x100/888/fff&text=No+User"}
#         }
#     photo_url = await fetch_user_photo(client, user.id)
#     if not photo_url:
#         photo_url = f"https://dummyimage.com/100x100/888/fff&text={user.first_name[:1]}"
#     return {
#         "id": user.id,
#         "name": user.first_name or "Unknown",
#         "photo": {
#             "url": photo_url
#         }
#     }

# def build_reply_message(reply_msg: Message):
#     if not reply_msg:
#         return None
#     return {
#         "name": reply_msg.from_user.first_name if reply_msg.from_user else "Unknown",
#         "text": reply_msg.text or reply_msg.caption or "",
#         "entities": extract_entities(reply_msg),
#         "chatId": reply_msg.chat.id
#     }

# async def build_message_obj(client, message: Message):
#     user_info = await build_user_info(client, message.from_user)

#     if message.sticker:
#         text = message.sticker.emoji or "[Sticker]"
#     elif message.video:
#         text = "[Video]"
#     elif message.document:
#         text = "[Document]"
#     else:
#         text = message.text or message.caption or ""

#     msg_obj = {
#         "from": user_info,
#         "text": text,
#         "avatar": True,
#         "entities": extract_entities(message),
#         "replyMessage": build_reply_message(message.reply_to_message) if message.reply_to_message else None
#     }
#     return msg_obj

# @app.on_message(filters.command("q") & filters.reply)
# async def quotely(client, message: Message):
#     reply = message.reply_to_message

#     if not QUOTE_API_URL:
#         await message.reply_text("❌ Quote API URL not configured.")
#         return

#     if not BOT_TOKEN:
#         await message.reply_text("❌ Bot token is missing from environment.")
#         return

#     if not reply:
#         await message.reply_text("❌ You must reply to a message to quote it.")
#         return

#     try:
#         payload = {
#             "botToken": BOT_TOKEN,  # <-- Added bot token here
#             "backgroundColor": "#1E1E1E",
#             "width": 512,
#             "height": 768,
#             "scale": 2,
#             "emojiBrand": "apple",
#             "messages": [
#                 await build_message_obj(client, reply)
#             ]
#         }

#         async with httpx.AsyncClient() as http_client:
#             response = await http_client.post(f"{QUOTE_API_URL}/generate.png", json=payload)

#         if response.status_code != 200:
#             await message.reply_text(f"❌ Quote API error: {response.status_code}\n{response.text}")
#             return

#         buffer = io.BytesIO(response.content)
#         buffer.name = "quote.png"
#         buffer.seek(0)

#         await message.reply_photo(photo=buffer)

#     except Exception as e:
#         await message.reply_text(f"❌ Exception occurred:\n`{e}`")


import os
import io
import httpx
from pyrogram import filters
from pyrogram.types import Message
from client import app
from dotenv import load_dotenv

load_dotenv()

QUOTE_API_URL = os.getenv("QUOTE_API_URL", "https://bot.lyo.su/quote")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Add your bot token in .env

async def fetch_user_big_file_id(client, user_id):
    """Get biggest profile photo file_id of user for the quote API."""
    try:
        photos = await client.get_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            photo_sizes = photos.photos[0]  # list of PhotoSize objects
            biggest = max(photo_sizes, key=lambda p: p.width * p.height)
            return biggest.file_id
    except Exception:
        return None
    return None

def extract_entities(message: Message):
    if not message.entities:
        return []

    entities = []
    for e in message.entities:
        type_map = {
            "bold": "bold",
            "italic": "italic",
            "underline": "underline",
            "strikethrough": "strikethrough",
            "code": "code",
            "pre": "pre",
            "text_link": "text_link",
            "mention": "mention",
            "url": "url",
            "email": "email",
        }
        entity_type = type_map.get(e.type)
        if not entity_type:
            continue

        ent = {
            "type": entity_type,
            "offset": e.offset,
            "length": e.length,
        }
        if e.type == "text_link" and e.url:
            ent["url"] = e.url
        entities.append(ent)
    return entities

async def build_user_info(client, user):
    if not user:
        return {
            "id": 0,
            "name": "Unknown",
            "photo": {"url": "https://dummyimage.com/100x100/888/fff&text=No+User"}
        }
    big_file_id = await fetch_user_big_file_id(client, user.id)
    photo_field = {"url": f"https://dummyimage.com/100x100/888/fff&text={user.first_name[:1]}"}  # fallback

    if big_file_id:
        photo_field = {"big_file_id": big_file_id}

    user_info = {
        "id": user.id,
        "name": user.first_name or "Unknown",
        "username": getattr(user, "username", None),
        "photo": photo_field
    }
    return user_info

def build_reply_message(reply_msg: Message):
    if not reply_msg:
        return None
    return {
        "name": reply_msg.from_user.first_name if reply_msg.from_user else "Unknown",
        "text": reply_msg.text or reply_msg.caption or "",
        "entities": extract_entities(reply_msg),
        "chatId": reply_msg.chat.id
    }

async def build_message_obj(client, message: Message):
    user_info = await build_user_info(client, message.from_user)

    if message.sticker:
        text = message.sticker.emoji or "[Sticker]"
    elif message.video:
        text = "[Video]"
    elif message.document:
        text = "[Document]"
    else:
        text = message.text or message.caption or ""

    msg_obj = {
        "from": user_info,
        "text": text,
        "avatar": True,
        "entities": extract_entities(message),
        "replyMessage": build_reply_message(message.reply_to_message) if message.reply_to_message else None
    }
    return msg_obj

@app.on_message(filters.command("q") & filters.reply)
async def quotely(client, message: Message):
    reply = message.reply_to_message

    if not QUOTE_API_URL:
        await message.reply_text("❌ Quote API URL not configured.")
        return

    if not BOT_TOKEN:
        await message.reply_text("❌ Bot token is missing in environment variables.")
        return

    if not reply:
        await message.reply_text("❌ You must reply to a message to quote it.")
        return

    try:
        payload = {
            "botToken": BOT_TOKEN,
            "backgroundColor": "#1E1E1E",
            "width": 512,
            "height": 768,
            "scale": 2,
            "emojiBrand": "apple",
            "messages": [
                await build_message_obj(client, reply)
            ]
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(f"{QUOTE_API_URL}/generate.png", json=payload)

        if response.status_code != 200:
            await message.reply_text(f"❌ Quote API error: {response.status_code}\n{response.text}")
            return

        buffer = io.BytesIO(response.content)
        buffer.name = "quote.png"
        buffer.seek(0)

        await message.reply_photo(photo=buffer)

    except Exception as e:
        await message.reply_text(f"❌ Exception occurred:\n`{e}`")

