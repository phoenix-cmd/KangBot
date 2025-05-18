import io
import re
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyrogram import filters, Client
from pyrogram.types import Message
import tempfile
import os

FONT_PATH_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def is_hex_color(s):
    return bool(re.fullmatch(r"#?[0-9a-fA-F]{6}", s))

async def get_image_bytes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
    return None

async def fetch_user_photo(client, user):
    """Fetch user profile photo and return PIL Image or None"""
    try:
        photos = await client.get_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            bio = io.BytesIO()
            await client.download_media(photos.photos[0], file=bio)
            bio.seek(0)
            img = Image.open(bio).convert("RGBA")
            return img
    except:
        pass
    return None

def make_rounded_avatar(img, size=40):
    img = img.resize((size, size), Image.ANTIALIAS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    output.putalpha(mask)
    return output

def draw_text(draw, position, text, font, max_width, fill=(0,0,0)):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        w, _ = draw.textsize(test_line, font=font)
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)
    y = position[1]
    for line in lines:
        draw.text((position[0], y), line, font=font, fill=fill)
        y += font.getsize(line)[1] + 4
    return y

async def get_sticker_png(client, sticker):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "sticker.webp")
        await sticker.download(file_path)
        img = Image.open(file_path).convert("RGBA")
        return img

async def gather_messages(message: Message):
    messages = []
    current = message.reply_to_message
    while current:
        messages.insert(0, current)
        current = current.reply_to_message
    return messages

# FIXED decorator: no () calling filters, just combine with &
@Client.on_message(filters.command("q") & filters.reply)
async def quotely_handler(client: Client, message: Message):
    # Default background
    bg_color = "white"
    if len(message.command) > 1:
        requested_color = message.command[1].lower()
        # Allow basic colors or hex (#RRGGBB)
        if requested_color in ("white", "black", "red", "green", "blue", "yellow", "pink", "purple", "orange", "gray"):
            bg_color = requested_color
        elif is_hex_color(requested_color):
            bg_color = requested_color if requested_color.startswith("#") else f"#{requested_color}"

    messages = await gather_messages(message)

    # Load fonts
    try:
        font_username = ImageFont.truetype(FONT_PATH_BOLD, 22)
        font_message = ImageFont.truetype(FONT_PATH_REGULAR, 18)
    except:
        font_username = ImageFont.load_default()
        font_message = ImageFont.load_default()

    padding = 20
    max_width = 512 - padding * 2
    line_spacing = 10
    avatar_size = 40
    spacing_between_messages = 25
    total_height = padding

    # Cache avatars
    avatars = {}
    for msg in messages:
        user = msg.from_user
        if user and user.id not in avatars:
            avatars[user.id] = await fetch_user_photo(client, user)

    # Calculate height
    for msg in messages:
        total_height += avatar_size + 5  # avatar + some margin

        # username height
        total_height += font_username.getsize(msg.from_user.first_name if msg.from_user else "Unknown")[1] + 5

        if msg.text:
            dummy_img = Image.new("RGBA", (max_width, 1000))
            draw = ImageDraw.Draw(dummy_img)
            y_end = draw_text(draw, (0, 0), msg.text, font_message, max_width)
            total_height += y_end + line_spacing
        elif msg.sticker:
            total_height += 150 + line_spacing
        else:
            total_height += font_message.getsize("[Unsupported content]")[1] + line_spacing

        total_height += spacing_between_messages

    total_height += padding

    # Create base image
    img = Image.new("RGBA", (512, total_height), bg_color)
    draw = ImageDraw.Draw(img)

    y_offset = padding

    for msg in messages:
        user = msg.from_user
        username = user.first_name if user else "Unknown"
        avatar = avatars.get(user.id) if user else None

        # Draw avatar
        if avatar:
            rounded_avatar = make_rounded_avatar(avatar, avatar_size)
            img.paste(rounded_avatar, (padding, y_offset), rounded_avatar)
        else:
            # Draw placeholder circle if no avatar
            draw.ellipse((padding, y_offset, padding + avatar_size, y_offset + avatar_size), fill=(180, 180, 180, 255))

        x_text = padding + avatar_size + 10
        y_text = y_offset

        # Draw username bold
        draw.text((x_text, y_text), username, font=font_username, fill=(0, 0, 0))
        y_text += font_username.getsize(username)[1] + 5

        # Draw message content
        if msg.text:
            y_text = draw_text(draw, (x_text, y_text), msg.text, font_message, max_width - avatar_size - 10)
            y_text += line_spacing
        elif msg.sticker:
            sticker_img = await get_sticker_png(client, msg.sticker)
            max_sticker_width = 150
            ratio = min(max_sticker_width / sticker_img.width, 1)
            new_size = (int(sticker_img.width * ratio), int(sticker_img.height * ratio))
            sticker_img = sticker_img.resize(new_size, Image.ANTIALIAS)
            img.paste(sticker_img, (x_text, y_text), sticker_img)
            y_text += new_size[1] + line_spacing
        else:
            draw.text((x_text, y_text), "[Unsupported content]", font=font_message, fill=(0, 0, 0))
            y_text += font_message.getsize("[Unsupported content]")[1] + line_spacing

        y_offset += max(avatar_size + 5, y_text - y_offset)
        y_offset += spacing_between_messages

    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)

    await message.reply_photo(photo=bio, caption=f"Quoted with background color: {bg_color}")
