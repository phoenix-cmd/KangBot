import os
import subprocess
from PIL import Image, ImageDraw, ImageFont
import requests
import imghdr
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = os.path.join(TEMP_DIR, "Anton-Regular.ttf")

def ensure_font():
    if not os.path.exists(FONT_PATH):
        print("Downloading font...")
        r = requests.get(FONT_URL)
        r.raise_for_status()
        with open(FONT_PATH, "wb") as f:
            f.write(r.content)
        print("Font downloaded.")

def draw_centered_text(draw, img, text, y, font):
    w, h = draw.textsize(text, font=font)
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

    def draw_centered_text(text, y):
        w, h = draw.textsize(text, font=font)
        x = (img.width - w) // 2
        draw.text((x, y), text, fill="white", font=font, stroke_width=2, stroke_fill="black")

    if top_text:
        draw_centered_text(top_text.upper(), 10)
    if bottom_text:
        draw_centered_text(bottom_text.upper(), img.height - font_size - 10)

    img.save(frame_path)

def meme_video(input_video, output_video, top_text, bottom_text, font_path):
    frames_dir = os.path.join(TEMP_DIR, "frames")
    if os.path.exists(frames_dir):
        # Clean up old frames
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))
    else:
        os.makedirs(frames_dir)

    # Extract frames
    subprocess.run([
        "ffmpeg", "-i", input_video,
        "-vf", "scale=iw:ih",
        f"{frames_dir}/frame_%04d.png"
    ], check=True)

    # Draw text on each frame
    for filename in sorted(os.listdir(frames_dir)):
        if filename.endswith(".png"):
            draw_text_on_frame(os.path.join(frames_dir, filename), top_text, bottom_text, font_path)

    # Re-encode frames to webm video
    subprocess.run([
        "ffmpeg",
        "-framerate", "30",
        "-i", f"{frames_dir}/frame_%04d.png",
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0",
        output_video
    ], check=True)

    # Cleanup frames
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

async def mmf_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply("Reply to an image/video/sticker with:\n`/mmf top text ; bottom text`")
        return

    # Parse meme texts
    top_text, bottom_text = "", ""
    try:
        cmd = message.text.split(None, 1)[1]
        top_text, bottom_text = map(str.strip, cmd.split(";", 1))
    except:
        pass  # If parsing fails, leave texts blank

    replied = message.reply_to_message
    user_id = message.from_user.id
    input_path = os.path.join(TEMP_DIR, f"{user_id}_input")
    output_path = os.path.join(TEMP_DIR, f"{user_id}_output")

    # Video or GIF processing
    if replied.video or replied.animation:
        await message.reply("Processing video/GIF with meme text... This may take a moment.")
        video_path = await replied.download(file_name=input_path + ".mp4")
        output_file = output_path + ".webm"

        try:
            ensure_font()
            meme_video(video_path, output_file, top_text, bottom_text, FONT_PATH)
            await message.reply_video(output_file, supports_streaming=False)
        except Exception as e:
            await message.reply(f"Failed to process video: {e}")
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(output_file):
                os.remove(output_file)

    # Photo, static sticker, or image document processing
    elif replied.photo or (replied.document and replied.document.mime_type.startswith("image")) or (replied.sticker and not replied.sticker.is_animated):
        await message.reply("Creating your meme...")

        # Handle webp stickers by converting to PNG
        if replied.sticker and not replied.sticker.is_animated:
            webp_path = await replied.download(file_name=input_path + ".webp")
            png_path = input_path + ".png"
            try:
                # Convert webp to png using ffmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-i", webp_path, png_path
                ], check=True)
                os.remove(webp_path)
            except Exception as e:
                await message.reply(f"Failed to convert sticker image: {e}")
                if os.path.exists(webp_path):
                    os.remove(webp_path)
                return
            image_path = png_path
        else:
            image_path = await replied.download(file_name=input_path + ".png")

        # Validate image file is an actual image
        if not imghdr.what(image_path):
            await message.reply("Downloaded file is not a valid image.")
            os.remove(image_path)
            return

        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as e:
            await message.reply(f"Failed to open the image: {e}")
            os.remove(image_path)
            return

        meme = draw_meme_text(img, top_text, bottom_text)
        meme_output = output_path + ".jpg"
        meme.save(meme_output, "JPEG")

        await message.reply_photo(meme_output, caption="Here's your meme!")

        os.remove(image_path)
        os.remove(meme_output)

    else:
        await message.reply("Unsupported media. Reply to an image, video, or static sticker.")

mmf_handler = MessageHandler(mmf_command, filters.command("mmf"))
