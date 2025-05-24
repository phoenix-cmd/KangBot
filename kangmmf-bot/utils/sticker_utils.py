# import os
# import requests
# import subprocess
# from PIL import Image
# from pyrogram.types import Message

# BOT_TOKEN = os.getenv("BOT_TOKEN")
# API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# async def kang_sticker(client, message: Message, target: Message):
#     user = message.from_user
#     user_id = user.id
#     emoji = "😎"

#     me = await client.get_me()
#     pack_name = f"kang_pack_{user_id}_by_{me.username}"
#     title = f"{user.first_name}'s Kang Pack"

#     os.makedirs("temp", exist_ok=True)
#     input_path = f"temp/input"
#     output_path = ""
#     sticker_type = ""

#     # Detect input type
#     if target.sticker:
#         emoji = target.sticker.emoji or "😎"
#         if target.sticker.is_animated:
#             sticker_type = "animated"
#             input_path += ".tgs"
#             output_path = input_path
#         elif target.sticker.is_video:
#             sticker_type = "video"
#             input_path += ".webm"
#             output_path = input_path
#         else:
#             sticker_type = "static"
#             input_path += ".png"
#             output_path = input_path
#         await target.download(input_path)

#     elif target.photo:
#         sticker_type = "static"
#         input_path += ".jpg"
#         output_path = f"temp/sticker.png"
#         await target.download(input_path)
        
#         img = Image.open(input_path).convert("RGBA")
#         img.thumbnail((512, 512))  # Resize to max 512x512
        
#         # Save as optimized PNG first
#         img.save(output_path, "PNG", optimize=True)

#         # If PNG > 512 KB, convert to WEBP (usually smaller)
#         if os.path.getsize(output_path) > 512 * 1024:
#             webp_path = output_path.replace(".png", ".webp")
#             img.save(webp_path, "WEBP", quality=95)
#             output_path = webp_path

#     elif target.document:
#         mime = target.document.mime_type
#         if mime in ["video/mp4", "image/gif"]:
#             sticker_type = "video"
#             input_path += ".mp4"
#             output_path = f"temp/sticker.webm"
#             await target.download(input_path)

#             # Convert GIF/MP4 to WebM video sticker format
#             cmd = [
#                 "ffmpeg", "-y", "-i", input_path,
#                 "-vf", "scale='min(512,iw)':min'(512,ih)':force_original_aspect_ratio=decrease",
#                 "-c:v", "libvpx-vp9",
#                 "-b:v", "512K",
#                 "-an",
#                 "-t", "3",
#                 "-pix_fmt", "yuva420p",
#                 output_path
#             ]
#             proc = subprocess.run(cmd, capture_output=True, text=True)
#             if proc.returncode != 0:
#                 print("FFmpeg error:", proc.stderr)
#                 await message.reply("Failed to convert GIF/video to video sticker.")
#                 return
#         else:
#             await message.reply("Unsupported document format. Send gif/mp4/photo/sticker.")
#             return
#     else:
#         await message.reply("Send me a photo, gif, or sticker to kang!")
#         return

#     if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
#         await message.reply("Conversion failed. Output file is invalid.")
#         return

#     # Prepare upload files based on sticker type
#     if sticker_type == "static":
#         files = {"png_sticker": open(output_path, "rb")}
#     elif sticker_type == "animated":
#         files = {"tgs_sticker": open(output_path, "rb")}
#     elif sticker_type == "video":
#         files = {"webm_sticker": open(output_path, "rb")}
#     else:
#         await message.reply("Sticker type not recognized.")
#         return

#     data = {
#         "user_id": user_id,
#         "name": pack_name,
#         "title": title,
#         "emojis": emoji
#     }

#     # Create new sticker set
#     response = requests.post(f"{API_URL}/createNewStickerSet", data=data, files=files)
#     result = response.json()
#     print("Create response:", result)

#     if result.get("ok"):
#         await message.reply(f"Created & added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
#     elif "sticker set name is already occupied" in result.get("description", ""):
#         del data["title"]
#         files[list(files.keys())[0]].seek(0)  # reset file pointer before re-upload
#         response = requests.post(f"{API_URL}/addStickerToSet", data=data, files=files)
#         result = response.json()
#         print("Add response:", result)

#         if result.get("ok"):
#             await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
#         else:
#             await message.reply(f"Failed to add sticker.\nError: {result.get('description')}")
#     else:
#         await message.reply(f"Failed to create sticker pack.\nError: {result.get('description')}")

#     # Cleanup temp files
#     for f in [input_path, output_path]:
#         if os.path.exists(f):
#             os.remove(f)





import os
import requests
import subprocess
from PIL import Image
from pyrogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    user_id = user.id
    emoji = "😎"

    me = await client.get_me()
    pack_name = f"kang_pack_{user_id}_by_{me.username}"
    title = f"{user.first_name}'s Kang Pack"

    os.makedirs("temp", exist_ok=True)
    input_path = "temp/input"
    output_path = ""
    sticker_type = ""

    try:
        # === Handle stickers ===
        if target.sticker:
            emoji = target.sticker.emoji or emoji
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
                input_path += ".webp"
                output_path = f"temp/sticker.png"
            await target.download(input_path)

        # === Handle photos ===
        elif target.photo:
            sticker_type = "static"
            input_path += ".jpg"
            output_path = f"temp/sticker.png"
            await target.download(input_path)
            img = Image.open(input_path).convert("RGBA")
            img.thumbnail((512, 512))
            img.save(output_path, "PNG", optimize=True)

        # === Handle documents and animations ===
        elif target.document or target.animation or target.video:
            mime = target.document.mime_type if target.document else \
                   target.animation.mime_type if target.animation else \
                   target.video.mime_type if target.video else ""

            # Static images
            if mime.startswith("image/") and not mime.endswith("gif"):
                sticker_type = "static"
                ext = mime.split("/")[-1]
                input_path += f".{ext}"
                output_path = f"temp/sticker.png"
                await target.download(input_path)
                img = Image.open(input_path).convert("RGBA")
                img.thumbnail((512, 512))
                img.save(output_path, "PNG", optimize=True)

            # Animated GIF or MP4 or WEBM video sticker
            elif mime in ["video/mp4", "image/gif", "video/webm"]:
                sticker_type = "video"
                ext = mime.split("/")[-1]
                input_path += f".{ext}"
                output_path = "temp/sticker.webm"
                await target.download(input_path)

                cmd = [
                    "ffmpeg", "-y", "-i", input_path,
                    "-vf", "scale='min(512,iw)':min'(512,ih)':force_original_aspect_ratio=decrease",
                    "-c:v", "libvpx-vp9", "-b:v", "512K", "-an",
                    "-t", "3", "-pix_fmt", "yuva420p",
                    output_path
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    await message.reply(f"FFmpeg error:\n`{proc.stderr.strip()}`")
                    return

            else:
                await message.reply("Unsupported document type. Send a photo, gif, mp4, webm, or sticker.")
                return

        else:
            await message.reply("Send a sticker, photo, gif, or video to kang.")
            return

        # Validate final file
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            await message.reply("Something went wrong. Output file is invalid.")
            return

        # Upload file
        if sticker_type == "static":
            files = {"png_sticker": open(output_path, "rb")}
        elif sticker_type == "animated":
            files = {"tgs_sticker": open(output_path, "rb")}
        elif sticker_type == "video":
            files = {"webm_sticker": open(output_path, "rb")}
        else:
            await message.reply("Failed to determine sticker type.")
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

        if result.get("ok"):
            await message.reply(
                f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅",
                disable_web_page_preview=True
            )
        elif "sticker set name is already occupied" in result.get("description", ""):
            del data["title"]
            files[list(files.keys())[0]].seek(0)
            response = requests.post(f"{API_URL}/addStickerToSet", data=data, files=files)
            result = response.json()
            if result.get("ok"):
                await message.reply(
                    f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅",
                    disable_web_page_preview=True
                )
            else:
                await message.reply(f"Failed to add sticker: {result.get('description')}")
        else:
            await message.reply(f"Failed to create sticker pack: {result.get('description')}")

    finally:
        # Cleanup temp files
        for f in [input_path, output_path]:
            if f and os.path.exists(f):
                os.remove(f)

