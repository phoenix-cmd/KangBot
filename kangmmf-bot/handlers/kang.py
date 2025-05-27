# from pyrogram import filters
# from pyrogram.types import Message
# from pyrogram.handlers import MessageHandler
# from utils.sticker_utils import kang_sticker

# async def kang_command(client, message: Message):
#     if not message.reply_to_message:
#         await message.reply("Reply to a sticker, image, or photo to kang it.")
#         return

#     target = message.reply_to_message
#     await kang_sticker(client, message, target)

# kang_handler = MessageHandler(kang_command, filters.command("kang"))
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from utils.sticker_utils import kang_sticker
from utils.logger import log_to_channel  

async def kang_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to a sticker, image, or photo to kang it.")
        return

    target = message.reply_to_message
    await kang_sticker(client, message, target)

    await log_to_channel(client, message, command="kang")

kang_handler = MessageHandler(kang_command, filters.command("kang"))
