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

def draw_centered_text(draw, img, text, y, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (img.width - w) // 2
    draw.text((x, y), text, fill="white", font=font, stroke_width=2, stroke_fill="black")

def draw_meme_text(img: Image.Image, top_text: str, bottom_text: str) -> Image.Image:
    ensure_font()
    draw = ImageDraw.Draw(img)
    font_size = int(img.height * 0.08)
    font = ImageFont.truetype(FONT_PATH, font_size)
    if top_text:
        draw_centered_text(draw, img, top_text.upper(), 10, font)
    if bottom_text:
        draw_centered_text(draw, img, bottom_text.upper(), img.height - font_size - 10, font)
    return img

def draw_text_on_frame(frame_path, top_text, bottom_text, font_path):
    img = Image.open(frame_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font_size = int(img.height * 0.08)
    font = ImageFont.truetype(font_path, font_size)

    def draw_centered(text, y):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (img.width - w) // 2
        draw.text((x, y), text, fill="white", font=font, stroke_width=2, stroke_fill="black")

    if top_text:
        draw_centered(top_text.upper(), 10)
    if bottom_text:
        draw_centered(bottom_text.upper(), img.height - font_size - 10)

    img.save(frame_path)

def meme_video(input_video, output_video, top_text, bottom_text, font_path):
    frames_dir = os.path.join(TEMP_DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    # Extract frames
    subprocess.run([
        "ffmpeg", "-i", input_video,
        "-vf", "scale=iw:ih",
        f"{frames_dir}/frame_%04d.png"
    ], check=True)

    # Draw meme text on each frame
    for filename in sorted(os.listdir(frames_dir)):
        if filename.endswith(".png"):
            draw_text_on_frame(os.path.join(frames_dir, filename), top_text, bottom_text, font_path)

    # Re-encode video as webm VP9 with alpha
    subprocess.run([
        "ffmpeg",
        "-framerate", "30",
        "-i", f"{frames_dir}/frame_%04d.png",
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0",
        output_video
    ], check=True)

    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

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

    # Handle video or animation (GIF)
    if replied.video or replied.animation:
        await message.reply("Processing video/GIF with meme text... This may take a moment.")
        video_path = await replied.download(file_name=input_path + ".mp4")
        output_file = output_path + ".webm"

        try:
            ensure_font()
            meme_video(video_path, output_file, top_text, bottom_text, FONT_PATH)
            await message.reply_video(output_file, supports_streaming=False)
        except Exception as e:
            await message.reply(f"Failed to process video: `{e}`")
        finally:
            for path in [video_path, output_file]:
                if os.path.exists(path):
                    os.remove(path)

    # Handle video stickers (.webm animated stickers)
    elif replied.sticker and replied.sticker.is_video:
        await message.reply("Processing video sticker with meme text... This may take a moment.")
        video_path = await replied.download(file_name=input_path + ".webm")
        output_file = output_path + ".webm"

        try:
            ensure_font()
            meme_video(video_path, output_file, top_text, bottom_text, FONT_PATH)
            await message.reply_video(output_file, supports_streaming=False)
        except Exception as e:
            await message.reply(f"Failed to process video sticker: `{e}`")
        finally:
            for path in [video_path, output_file]:
                if os.path.exists(path):
                    os.remove(path)

    # Handle static images and static stickers
    elif replied.photo or (replied.document and replied.document.mime_type.startswith("image")) or (replied.sticker and not replied.sticker.is_animated):
        await message.reply("Creating your meme...")

        try:
            if replied.sticker and not replied.sticker.is_animated:
                # Convert webp sticker to png
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
        await message.reply("Unsupported media. Reply to an image, video, static sticker, or video sticker.")

mmf_handler = MessageHandler(mmf_command, filters.command("mmf"))
