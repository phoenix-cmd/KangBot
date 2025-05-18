import os
import requests
from PIL import Image
from pyrogram.types import Message

BOT_TOKEN = "your_token_here"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    user_id = user.id
    emoji = "😎"
    me = await client.get_me()  # 👈 required
    pack_name = f"kang_pack_{user_id}_by_{me.username}"

    title = f"{user.first_name}'s Kang Pack"

    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{user_id}.png"  # Use .png

    # Download sticker or image
    if target.sticker:
        emoji = target.sticker.emoji or "😎"
        await target.download(file_path)
    elif target.photo:
        await target.download("temp/temp_photo.jpg")
        img = Image.open("temp/temp_photo.jpg").convert("RGBA")
        img.thumbnail((512, 512))
        img.save(file_path, "PNG")
    else:
        await message.reply("Send me a sticker or photo to kang!")
        return

    # Validate file before sending
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        await message.reply("Downloaded file is empty or invalid.")
        return

    with open(file_path, "rb") as sticker_file:
        files = {"png_sticker": sticker_file}
        data = {
            "user_id": user_id,
            "name": pack_name,
            "title": title,
            "emojis": emoji
        }

        response = requests.post(f"{API_URL}/createNewStickerSet", data=data, files=files)
        result = response.json()

        if result.get("ok"):
            await message.reply(
                f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅",
                disable_web_page_preview=True
            )
        elif "sticker set name is already occupied" in result.get("description", ""):
            del data["title"]
            response = requests.post(f"{API_URL}/addStickerToSet", data=data, files=files)
            result = response.json()

            if result.get("ok"):
                await message.reply(
                    f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅",
                    disable_web_page_preview=True
                )
            else:
                await message.reply(f"Failed to add sticker.\nError: {result.get('description')}")
        else:
            await message.reply(f"Failed to create sticker pack.\nError: {result.get('description')}")

    os.remove(file_path)

