import os
from pyrogram.types import Message
from pyrogram.errors import StickerEmojiInvalid
from PIL import Image
from pyrogram.raw.functions.stickers import CreateStickerSet, AddStickerToSet
from pyrogram.raw.types import InputStickerSetShortName, InputSticker, InputDocument
from pyrogram.raw.types.input_sticker_set_short_name import InputStickerSetShortName

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
        # Upload file to Telegram
        uploaded_file = await client.save_file(file_path)

        # Try adding to existing pack
        await client.invoke(
            AddStickerToSet(
                stickerset=InputStickerSetShortName(short_name=pack_name),
                sticker=InputSticker(
                    file=uploaded_file,
                    emojis=emoji
                )
            )
        )
        await message.reply(f"Kanged to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)

    except Exception as e:
        try:
            uploaded_file = await client.save_file(file_path)

            # Create new sticker set
            await client.invoke(
                CreateStickerSet(
                    user_id=user.id,
                    title=title,
                    short_name=pack_name,
                    stickers=[
                        InputSticker(
                            file=uploaded_file,
                            emojis=emoji
                        )
                    ],
                    stickerset_type="stickersetTypeRegular"
                )
            )
            await message.reply(f"Created and added to [your pack](https://t.me/addstickers/{pack_name}) ✅", disable_web_page_preview=True)
        except Exception as e2:
            await message.reply(f"Failed to create sticker pack.\nError: {e2}")

    os.remove(file_path)
