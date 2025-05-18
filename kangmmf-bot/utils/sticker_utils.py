import os
from pyrogram.types import Message
from pyrogram.errors import StickerEmojiInvalid
from PIL import Image
from pyrogram.raw import functions, types

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    file_path = f"temp/{user.id}.webp"
    emoji = "😎"

    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)

    if target.sticker:
        file = await target.download(file_path)
        emoji = target.sticker.emoji or "😎"
    elif target.photo:
        file = await target.download(file_path)
        img = Image.open(file).convert("RGBA")
        img.thumbnail((512, 512))
        img.save(file_path, "WEBP")
    else:
        await message.reply("Only stickers, images or photos are supported.")
        return

    pack_name = f"kang_pack_{user.id}_by_{client.me.username}"
    title = f"{user.first_name}'s Kang Pack"

    try:
        # Add sticker to existing pack
        await client.send(
            functions.stickers.AddStickerToSet(
                stickerset=types.InputStickerSetShortName(short_name=pack_name),
                sticker=types.InputSticker(
                    # Use PNG sticker input file
                    png_sticker=await client.upload_file(file_path),
                    emojis=emoji
                )
            )
        )
        await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
    except Exception as e:
        # If add failed, try to create a new pack
        try:
            await client.send(
                functions.stickers.CreateStickerSet(
                    user_id=user.id,
                    title=title,
                    short_name=pack_name,
                    stickers=[
                        types.InputSticker(
                            png_sticker=await client.upload_file(file_path),
                            emojis=emoji
                        )
                    ],
                    # You can specify the sticker set type (e.g., 'regular' for static stickers)
                    stickerset_type="regular"
                )
            )
            await message.reply(f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
        except Exception as e2:
            await message.reply(f"Failed to create sticker pack.\nError: {e2}")

    os.remove(file_path)
