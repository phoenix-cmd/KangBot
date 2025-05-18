import os
import requests
from PIL import Image
from pyrogram.types import Message

BOT_TOKEN = "8009363720:AAFNbkPS7LNip5WBIy9krO3yhrY0Sc_8-vM"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    user_id = user.id
    emoji = "😎"
    file_path = f"temp/{user_id}.webp"
    pack_name = f"kang_pack_{user_id}_by_{client.me.username}"
    title = f"{user.first_name}'s Kang Pack"

    os.makedirs("temp", exist_ok=True)

    # Download sticker or image
    if target.sticker:
        emoji = target.sticker.emoji or "😎"
        await target.download(file_path)
    elif target.photo:
        await target.download(file_path)
        img = Image.open(file_path).convert("RGBA")
        img.thumbnail((512, 512))
        img.save(file_path, "WEBP")
    else:
        await message.reply("Send me a sticker or photo to kang!")
        return

    with open(file_path, "rb") as sticker_file:
        files = {"png_sticker": sticker_file}
        data = {
            "user_id": user_id,
            "name": pack_name,
            "title": title,
            "emojis": emoji
        }

        # Try creating sticker set first
        response = requests.post(f"{API_URL}/createNewStickerSet", data=data, files=files)
        result = response.json()

        if result.get("ok"):
            await message.reply(f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
        elif "sticker set name is already occupied" in result.get("description", ""):
            # Try adding to existing set
            del data["title"]  # Not needed when adding
            response = requests.post(f"{API_URL}/addStickerToSet", data=data, files=files)
            result = response.json()

            if result.get("ok"):
                await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
            else:
                await message.reply(f"Failed to add sticker.\nError: {result.get('description')}")
        else:
            await message.reply(f"Failed to create sticker pack.\nError: {result.get('description')}")

    os.remove(file_path)
