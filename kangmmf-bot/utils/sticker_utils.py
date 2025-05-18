import os
import requests
import subprocess
from PIL import Image
from pyrogram.types import Message

BOT_TOKEN = "8009363720:AAFNbkPS7LNip5WBIy9krO3yhrY0Sc_8-vM"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    user_id = user.id
    emoji = "😎"

    me = await client.get_me()
    pack_name = f"kang_pack_{user_id}_by_{me.username}"
    title = f"{user.first_name}'s Kang Pack"

    os.makedirs("temp", exist_ok=True)
    input_path = f"temp/input"
    output_path = ""
    sticker_type = ""

    # === Detect type ===
    if target.sticker:
        emoji = target.sticker.emoji or "😎"
        if target.sticker.is_animated:
            sticker_type = "animated"
            input_path += ".tgs"
            output_path = input_path
        elif target.sticker.is_video:
            sticker_type = "video"
            input_path += ".webm"
            output_path = input_path
        else:
            sticker_type = "static"
            input_path += ".png"
            output_path = input_path
        await target.download(input_path)

    elif target.photo:
        sticker_type = "static"
        input_path += ".jpg"
        output_path = f"temp/sticker.png"
        await target.download(input_path)
        img = Image.open(input_path).convert("RGBA")
        img.thumbnail((512, 512))
        img.save(output_path, "PNG")

    elif target.document:
        mime = target.document.mime_type
        if mime in ["video/mp4", "image/gif"]:
            sticker_type = "video"
            input_path += ".mp4"
            output_path = f"temp/sticker.webm"
            await target.download(input_path)

            # Convert to webm using ffmpeg
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "scale=512:512:force_original_aspect_ratio=decrease",
                "-c:v", "libvpx-vp9", "-b:v", "500K", "-an", "-t", "3",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            await message.reply("Unsupported document format. Send gif/mp4/photo/sticker.")
            return
    else:
        await message.reply("Send me a photo, gif, or sticker to kang!")
        return

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        await message.reply("Conversion failed. Output file is invalid.")
        return

    # === Prepare upload ===
    if sticker_type == "static":
        files = {"png_sticker": open(output_path, "rb")}
    elif sticker_type == "animated":
        files = {"tgs_sticker": open(output_path, "rb")}
    elif sticker_type == "video":
        files = {"webm_sticker": open(output_path, "rb")}
    else:
        await message.reply("Sticker type not recognized.")
        return

    data = {
        "user_id": user_id,
        "name": pack_name,
        "title": title,
        "emojis": emoji
    }

    # Try to create new pack
    response = requests.post(f"{API_URL}/createNewStickerSet", data=data, files=files)
    result = response.json()
    print("Create response:", result)

    if result.get("ok"):
        await message.reply(f"Created & added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
    elif "sticker set name is already occupied" in result.get("description", ""):
        del data["title"]
        files[list(files.keys())[0]].seek(0)
        response = requests.post(f"{API_URL}/addStickerToSet", data=data, files=files)
        result = response.json()
        print("Add response:", result)

        if result.get("ok"):
            await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
        else:
            await message.reply(f"Failed to add sticker.\nError: {result.get('description')}")
    else:
        await message.reply(f"Failed to create sticker pack.\nError: {result.get('description')}")

    # Clean up
    for f in [input_path, output_path]:
        if os.path.exists(f): os.remove(f)
