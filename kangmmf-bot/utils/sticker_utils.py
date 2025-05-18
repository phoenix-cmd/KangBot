import os
from pyrogram.types import Message
from pyrogram.errors import StickerEmojiInvalid, StickersetInvalid
from PIL import Image

async def kang_sticker(client, message: Message, target: Message):
    user = message.from_user
    file_path = f"temp/{user.id}.webp"
    emoji = "😎"

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
        # Try adding to existing sticker pack
        await client.add_sticker_to_set(
            user_id=user.id,
            name=pack_name,
            emojis=emoji,
            png_sticker=file_path
        )
        await message.reply(
            f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅",
            disable_web_page_preview=True
        )
    except StickersetInvalid:
        # Create new sticker pack if it doesn't exist
        try:
            await client.create_sticker_set(
                user_id=user.id,
                name=pack_name,
                title=title,
                stickers=[
                    {
                        "emoji": emoji,
                        "png_sticker": file_path
                    }
                ]
            )
            await message.reply(
                f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅",
                disable_web_page_preview=True
            )
        except Exception as e:
            await message.reply(f"Failed to create sticker pack.\nError: {e}")
    except StickerEmojiInvalid:
        await message.reply("❌ Invalid emoji used.")
    except Exception as e:
        await message.reply(f"Failed to kang sticker.\nError: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

