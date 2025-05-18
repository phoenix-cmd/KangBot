from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from utils.ffmpeg import convert_video_to_webm

async def mmf_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to a video or GIF with /mmf.")
        return

    replied = message.reply_to_message
    if not (replied.video or replied.animation):
        await message.reply("That’s not a video or GIF.")
        return

    await message.reply("Processing your media...")

    path = await replied.download(file_name=f"temp/{message.from_user.id}_input.mp4")
    output_path = f"temp/{message.from_user.id}_output.webm"

    success = convert_video_to_webm(path, output_path)
    if not success:
        await message.reply("Failed to convert the video.")
        return

    try:
        await message.reply_video(output_path, supports_streaming=False)
    except Exception as e:
        await message.reply(f"Failed to send converted video: {e}")

mmf_handler = MessageHandler(mmf_command, filters.command("mmf"))
