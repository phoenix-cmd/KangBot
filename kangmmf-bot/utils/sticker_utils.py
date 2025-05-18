import os
from pyrogram.types import Message
from pyrogram.errors import StickerEmojiInvalid
from PIL import Image

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    file_path = f"temp/{user.id}.webp"
    emoji = "😎"

    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)

    if target.sticker:
        # Download the sticker file from the message, not from sticker object
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
    await client.add_sticker_to_set(
        user_id=user.id,
        name=pack_name,
        emojis=emoji,
        png_sticker=file_path
    )
    await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
except StickerEmojiInvalid:
    await message.reply("Failed: Invalid emoji.")
except Exception as e:
    # First time? Create pack with correct method
    try:
        await client.create_new_sticker_set(
            user_id=user.id,
            name=pack_name,
            title=title,
            emojis=emoji,
            png_sticker=file_path
        )
        await message.reply(f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"Failed to create sticker pack.\nError: {e}")


    # Clean up temp file
    os.remove(file_path)
