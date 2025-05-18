import io
import re
import os
import aiohttp
import tempfile
import logging
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyrogram import filters, Client
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
IMG_WIDTH = 512
PADDING = 20
AVATAR_SIZE = 40
LINE_SPACING = 10
SPACING_BETWEEN_MESSAGES = 25
MAX_STICKER_WIDTH = 150

def is_hex_color(s):
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", s))

def truncate_text(text, max_width, font):
    # Use textbbox for accurate width measurement
    while font.getbbox(text + "…")[2] > max_width and len(text) > 0:
        text = text[:-1]
    return text + "…" if len(text) > 0 else text

async def fetch_user_photo(client, user):
    try:
        photos = await client.get_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            bio = io.BytesIO()
            await client.download_media(photos.photos[0], file=bio)
            bio.seek(0)
            return Image.open(bio).convert("RGBA")
    except Exception as e:
        logger.warning(f"Failed to fetch photo for {user.id if user else 'unknown'}: {e}")
    return None

def make_rounded_avatar(img, size=AVATAR_SIZE):
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

def draw_text(draw, position, text, font, max_width, fill=(0,0,0)):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        w = draw.textbbox((0, 0), test_line, font=font)[2]
        if w <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    y = position[1]
    for line in lines:
        draw.text((position[0], y), line, font=font, fill=fill)
        line_height = draw.textbbox((0,0), line, font=font)[3] - draw.textbbox((0,0), line, font=font)[1]
        y += line_height + 4
    return y

async def get_sticker_png(client, sticker):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "sticker.webp")
        await sticker.download(file_path)
        return Image.open(file_path).convert("RGBA")

async def gather_messages(message: Message):
    messages = []
    # Include original replied message
    if message.reply_to_message:
        current = message.reply_to_message
        while current:
            messages.insert(0, current)
            current = current.reply_to_message
    # Also include the current message itself
    messages.append(message)
    return messages

@Client.on_message(filters.command("q") & filters.reply)
async def quotely_handler(client: Client, message: Message):
    bg_color = "white"
    if len(message.command) > 1:
        requested_color = message.command[1].lower()
        if requested_color in ("white", "black", "red", "green", "blue", "yellow", "pink", "purple", "orange", "gray"):
            bg_color = requested_color
        elif is_hex_color(requested_color):
            bg_color = requested_color if requested_color.startswith("#") else f"#{requested_color}"

    messages = await gather_messages(message)
    if not messages:
        await message.reply("No messages to quote!")
        return

    font_username = ImageFont.truetype(FONT_PATH_BOLD, 22)
    font_message = ImageFont.truetype(FONT_PATH_REGULAR, 18)
    max_width = IMG_WIDTH - PADDING * 2

    avatars = {}
    total_height = PADDING

    # Fetch avatars async
    for msg in messages:
        user = msg.from_user
        if user and user.id not in avatars:
            avatars[user.id] = await fetch_user_photo(client, user)

    # Calculate total height needed
    for msg in messages:
        total_height += AVATAR_SIZE + 5
        username = msg.from_user.first_name if msg.from_user else (msg.forward_sender_name or "Unknown")
        username_height = draw_text(ImageDraw.Draw(Image.new("RGBA", (1,1))), (0,0), username, font_username, max_width) - 0
        total_height += username_height + 5

        text_content = msg.text or msg.caption
        if text_content:
            dummy_img = Image.new("RGBA", (max_width, 1000))
            draw = ImageDraw.Draw(dummy_img)
            y_end = draw_text(draw, (0, 0), text_content, font_message, max_width)
            total_height += y_end + LINE_SPACING
        elif msg.sticker:
            total_height += 150 + LINE_SPACING
        else:
            unsupported_height = draw_text(ImageDraw.Draw(Image.new("RGBA", (1,1))), (0,0), "[Unsupported content]", font_message, max_width) - 0
            total_height += unsupported_height + LINE_SPACING

        total_height += SPACING_BETWEEN_MESSAGES

    total_height += PADDING
    img = Image.new("RGBA", (IMG_WIDTH, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    y_offset = PADDING

    for msg in messages:
        user = msg.from_user
        username = user.first_name if user else (msg.forward_sender_name or "Unknown")
        avatar = avatars.get(user.id) if user else None

        if avatar:
            rounded = make_rounded_avatar(avatar)
            img.paste(rounded, (PADDING, y_offset), rounded)
        else:
            draw.ellipse((PADDING, y_offset, PADDING + AVATAR_SIZE, y_offset + AVATAR_SIZE), fill=(180, 180, 180, 255))

        x_text = PADDING + AVATAR_SIZE + 10
        y_text = y_offset
        username = truncate_text(username, max_width - AVATAR_SIZE, font_username)
        draw.text((x_text, y_text), username, font=font_username, fill=(0, 0, 0))
        username_height = draw.textbbox((0,0), username, font=font_username)[3]
        y_text += username_height + 5

        text_content = msg.text or msg.caption
        if text_content:
            y_text = draw_text(draw, (x_text, y_text), text_content, font_message, max_width - AVATAR_SIZE - 10)
            y_text += LINE_SPACING
        elif msg.sticker:
            sticker_img = await get_sticker_png(client, msg.sticker)
            ratio = min(MAX_STICKER_WIDTH / sticker_img.width, 1)
            new_size = (int(sticker_img.width * ratio), int(sticker_img.height * ratio))
            sticker_img = sticker_img.resize(new_size, Image.LANCZOS)
            img.paste(sticker_img, (x_text, y_text), sticker_img)
            y_text += new_size[1] + LINE_SPACING
        else:
            draw.text((x_text, y_text), "[Unsupported content]", font=font_message, fill=(0, 0, 0))
            unsupported_height = draw.textbbox((0,0), "[Unsupported content]", font=font_message)[3]
            y_text += unsupported_height + LINE_SPACING

        y_offset += max(AVATAR_SIZE + 5, y_text - y_offset)
        y_offset += SPACING_BETWEEN_MESSAGES

    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    await message.reply_photo(photo=bio, caption=f"Quoted with background color: {bg_color}")
