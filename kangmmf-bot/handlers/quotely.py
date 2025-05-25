import io
import re
import os
import aiohttp
import tempfile
import logging
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyrogram import filters
from pyrogram.types import Message
from client import app

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
FONT_PATH_BOLD = "fonts/Roboto-Bold.ttf"
FONT_PATH_REGULAR = "fonts/Roboto-Medium.ttf"
IMG_WIDTH = 512
PADDING = 20
AVATAR_SIZE = 40
LINE_SPACING = 10
SPACING_BETWEEN_MESSAGES = 25
MAX_STICKER_WIDTH = 150

def is_hex_color(s):
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", s))

def truncate_text(text, max_width, font, draw):
    while True:
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] <= max_width:
            break
        if len(text) == 0:
            break
        text = text[:-1]
    if len(text) == 0:
        return ""
    return text + "…" if bbox[2] > max_width else text

def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height

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

def draw_initials(draw, initials, position, font):
    w, h = get_text_size(draw, initials, font)
    x, y = position
    draw.text(
        (x + (AVATAR_SIZE - w) / 2, y + (AVATAR_SIZE - h) / 2),
        initials,
        font=font,
        fill=(255, 255, 255),
    )

def draw_text(draw, position, text, font, max_width, fill=(0, 0, 0)):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
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
        line_height = draw.textbbox((0, 0), line, font=font)[3]
        y += line_height + 4
    return y

async def get_sticker_png(client, sticker):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "sticker.webp")
        await sticker.download(file_path)
        return Image.open(file_path).convert("RGBA")

async def gather_messages(message: Message, count: int = 1):
    messages = []
    if message.reply_to_message:
        current = message.reply_to_message
        for _ in range(count):
            if current:
                messages.insert(0, current)
                current = current.reply_to_message
    else:
        chat_id = message.chat.id
        current_id = message.id - 1
        while len(messages) < count and current_id > 0:
            try:
                msg = await message.client.get_messages(chat_id, current_id)
                if msg:
                    messages.insert(0, msg)
                current_id -= 1
            except Exception:
                break
    messages.append(message)
    return messages

@app.on_message(filters.command("q"))
async def quotely_handler(client, message: Message):
    count = 1
    bg_color = "white"
    show_avatar = True

    if len(message.command) > 1:
        for arg in message.command[1:]:
            if arg.isdigit():
                count = min(int(arg), 10)
            elif arg.lower() == "avataroff":
                show_avatar = False
            elif is_hex_color(arg) or arg.lower() in (
                "white", "black", "red", "green", "blue",
                "yellow", "pink", "purple", "orange", "gray"
            ):
                # Ensure proper hex color formatting
                if is_hex_color(arg):
                    bg_color = arg if arg.startswith("#") else f"#{arg}"
                else:
                    bg_color = arg.lower()

    messages = await gather_messages(message, count=count)
    if not messages:
        await message.reply("No messages to quote!")
        return

    # Load fonts (make sure these font files exist at these paths)
    font_username = ImageFont.truetype(FONT_PATH_BOLD, 23)
    font_message = ImageFont.truetype(FONT_PATH_REGULAR, 18)
    max_width = IMG_WIDTH - PADDING * 2

    avatars = {}
    total_height = PADDING

    for msg in messages:
        user = msg.from_user
        if show_avatar and user and user.id not in avatars:
            avatar_img = await fetch_user_photo(client, user)
            if avatar_img:
                avatars[user.id] = avatar_img

    # Precompute total height
    for msg in messages:
        total_height += AVATAR_SIZE + 5 if show_avatar else 5
        username = msg.from_user.first_name if msg.from_user else (msg.forward_sender_name or "Unknown")

        # Create a temporary draw for measuring text
        dummy_img = Image.new("RGBA", (max_width, 1000))
        dummy_draw = ImageDraw.Draw(dummy_img)

        username = truncate_text(username, max_width, font_username, dummy_draw)
        _, username_height = get_text_size(dummy_draw, username, font_username)
        total_height += username_height + 5

        text_content = msg.text or msg.caption
        if text_content:
            y_end = draw_text(dummy_draw, (0, 0), text_content, font_message, max_width)
            total_height += y_end + LINE_SPACING
        elif msg.sticker:
            total_height += 150 + LINE_SPACING
        else:
            unsupported_height = get_text_size(dummy_draw, "[Unsupported content]", font_message)[1]
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

        if show_avatar:
            if avatar:
                rounded = make_rounded_avatar(avatar)
                img.paste(rounded, (PADDING, y_offset), rounded)
            else:
                # Draw initials if no avatar available
                draw.ellipse((PADDING, y_offset, PADDING + AVATAR_SIZE, y_offset + AVATAR_SIZE), fill=(180, 180, 180, 255))
                initials = "".join([n[0].upper() for n in username.split() if n])
                draw_initials(draw, initials, (PADDING, y_offset), font_username)

        x_text = PADDING + AVATAR_SIZE + 10 if show_avatar else PADDING
        y_text = y_offset

        username = truncate_text(username, max_width - AVATAR_SIZE - 10 if show_avatar else max_width, font_username, draw)
        draw.text((x_text, y_text), username, font=font_username, fill=(0, 0, 0))
        username_height = get_text_size(draw, username, font_username)[1]
        y_text += username_height + 5

        text_content = msg.text or msg.caption
        if text_content:
            y_text = draw_text(draw, (x_text, y_text), text_content, font_message, max_width - AVATAR_SIZE - 10 if show_avatar else max_width)
            y_text += LINE_SPACING
        elif msg.sticker:
            sticker_img = await get_sticker_png(client, msg.sticker)
            ratio = min(MAX_STICKER_WIDTH / sticker_img.width, 1)
            sticker_img = sticker_img.resize((int(sticker_img.width * ratio), int(sticker_img.height * ratio)), Image.ANTIALIAS)
            img.paste(sticker_img, (x_text, y_text), sticker_img)
            y_text += sticker_img.height + LINE_SPACING
        else:
            draw.text((x_text, y_text), "[Unsupported content]", font=font_message, fill=(100, 100, 100))
            y_text += get_text_size(draw, "[Unsupported content]", font_message)[1] + LINE_SPACING

        y_offset = max(y_offset + AVATAR_SIZE, y_text) + SPACING_BETWEEN_MESSAGES

    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)

    await message.reply_photo(photo=bio)

