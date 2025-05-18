from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from utils.ffmpeg import convert_video_to_webm
from PIL import Image, ImageDraw, ImageFont
import os
import requests

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
FONT_PATH = os.path.join(TEMP_DIR, "Roboto-Bold.ttf")

def ensure_font():
    if not os.path.exists(FONT_PATH):
        print("Downloading font...")
        r = requests.get(FONT_URL)
        r.raise_for_status()
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
        print("Font downloaded.")

def draw_meme_text(img: Image.Image, top_text: str, bottom_text: str) -> Image.Image:
    ensure_font()  # Make sure font exists before loading

    draw = ImageDraw.Draw(img)
    font_size = int(img.height * 0.08)
    font = ImageFont.truetype(FONT_PATH, font_size)

    def draw_centered_text(text, y):
        w, h = draw.textsize(text, font=font)
        x = (img.width - w) // 2
        draw.text((x, y), text, fill="white", font=font, stroke_width=2, stroke_fill="black")

    if top_text:
        draw_centered_text(top_text.upper(), 10)
    if bottom_text:
        draw_centered_text(bottom_text.upper(), img.height - font_size - 10)

    return img

async def mmf_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to an image/video/sticker with:\n`/mmf top text ; bottom text`")
        return

    # Parse text if available
    top_text, bottom_text = "", ""
    try:
        cmd = message.text.split(None, 1)[1]
        top_text, bottom_text = map(str.strip, cmd.split(";", 1))
    except:
        pass  # Leave blank if parsing fails

    replied = message.reply_to_message
    user_id = message.from_user.id
    input_path = f"{TEMP_DIR}/{user_id}_input"
    output_path = f"{TEMP_DIR}/{user_id}_output"

    if replied.video or replied.animation:
        await message.reply("Processing video/GIF...")
        video_path = await replied.download(file_name=input_path + ".mp4")
        output_file = output_path + ".webm"

        if convert_video_to_webm(video_path, output_file):
            await message.reply_video(output_file, supports_streaming=False)
            os.remove(video_path)
            os.remove(output_file)
        else:
            await message.reply("Failed to convert the video.")

    elif replied.photo or (replied.document and replied.document.mime_type.startswith("image")) or (replied.sticker and not replied.sticker.is_animated):
        await message.reply("Creating your meme...")

        image_path = await replied.download(file_name=input_path + ".png")
        img = Image.open(image_path).convert("RGB")
        meme = draw_meme_text(img, top_text, bottom_text)
        meme_output = output_path + ".jpg"
        meme.save(meme_output, "JPEG")

        await message.reply_photo(meme_output, caption="Here's your meme!")

        os.remove(image_path)
        os.remove(meme_output)

    else:
        await message.reply("Unsupported media. Reply to an image, video, or static sticker.")

mmf_handler = MessageHandler(mmf_command, filters.command("mmf"))
