import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import requests
import imghdr
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logging.info(f"ffmpeg found at: {shutil.which('ffmpeg')}")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = os.path.join(TEMP_DIR, "Anton-Regular.ttf")

def ensure_font():
    if not os.path.exists(FONT_PATH):
        logging.info("Downloading font...")
        r = requests.get(FONT_URL)
        r.raise_for_status()
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
        logging.info("Font downloaded.")

# (Your existing drawing functions here: draw_centered_text, draw_meme_text, draw_text_on_frame, meme_video)

def convert_to_telegram_sticker(input_webm, output_webm):
    cmd = [
        "ffmpeg",
        "-i", input_webm,
        "-an",  # remove audio
        "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libvpx-vp9",
        "-deadline", "realtime",
        "-quality", "good",
        "-speed", "4",
        "-tile-columns", "0",
        "-frame-parallel", "1",
        output_webm
    ]
    subprocess.run(cmd, check=True)

async def mmf_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to an image/video/sticker with:\n`/mmf top text ; bottom text`")
        return

    top_text, bottom_text = "", ""
    try:
        cmd = message.text.split(None, 1)[1]
        top_text, bottom_text = map(str.strip, cmd.split(";", 1))
    except (IndexError, ValueError):
        pass

    replied = message.reply_to_message
    user_id = message.from_user.id
    input_path = os.path.join(TEMP_DIR, f"{user_id}_input")
    output_path = os.path.join(TEMP_DIR, f"{user_id}_output")

    if replied.video or replied.animation:
        await message.reply("Processing video/GIF with meme text... This may take a moment.")
        video_path = await replied.download(file_name=input_path + ".mp4")
        temp_output = output_path + ".webm"
        sticker_output = output_path + "_sticker.webm"

        try:
            ensure_font()
            meme_video(video_path, temp_output, top_text, bottom_text, FONT_PATH)

            # Convert meme video .webm to Telegram video sticker format
            convert_to_telegram_sticker(temp_output, sticker_output)

            # Send as video sticker (video note)
            await message.reply_video_note(sticker_output, duration=3, length=512)

        except Exception as e:
            await message.reply(f"Failed to process video: `{e}`")
        finally:
            for path in [video_path, temp_output, sticker_output]:
                if os.path.exists(path):
                    os.remove(path)

    elif replied.photo or (replied.document and replied.document.mime_type.startswith("image")) or (replied.sticker and not replied.sticker.is_animated):
        await message.reply("Creating your meme...")

        try:
            if replied.sticker and not replied.sticker.is_animated:
                webp_path = await replied.download(file_name=input_path + ".webp")
                png_path = input_path + ".png"
                subprocess.run(["ffmpeg", "-y", "-i", webp_path, png_path], check=True)
                os.remove(webp_path)
                image_path = png_path
            else:
                image_path = await replied.download(file_name=input_path + ".png")

            if not imghdr.what(image_path):
                await message.reply("Downloaded file is not a valid image.")
                os.remove(image_path)
                return

            img = Image.open(image_path).convert("RGB")
            meme = draw_meme_text(img, top_text, bottom_text)
            meme_output = output_path + ".jpg"
            meme.save(meme_output, "JPEG")

            await message.reply_photo(meme_output, caption="Here's your meme!")

        except Exception as e:
            await message.reply(f"Image processing failed: `{e}`")
        finally:
            for path in [image_path, meme_output]:
                if os.path.exists(path):
                    os.remove(path)

    else:
        await message.reply("Unsupported media. Reply to an image, video, or static sticker.")

mmf_handler = MessageHandler(mmf_command, filters.command("mmf"))
