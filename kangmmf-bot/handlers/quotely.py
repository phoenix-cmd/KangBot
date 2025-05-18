import io
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.types import Message
import requests
import tempfile
import os

# You can change font path to a ttf font available in your environment
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

async def get_sticker_png(client, sticker):
    """Download a sticker (static or animated) and convert to PNG if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "sticker.webp")
        await sticker.download(file_path)
        img = Image.open(file_path).convert("RGBA")
        return img

def draw_text(draw, position, text, font, max_width, fill=(0,0,0)):
    """Draw multiline text wrapped to max_width."""
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
    return y  # Return y position after drawing text

async def gather_messages(message: Message):
    """Gather a list of messages to quote starting from replied message
    following reply_to_message chain."""
    messages = []
    current = message.reply_to_message
    while current:
        messages.insert(0, current)  # insert at beginning to keep order oldest -> newest
        current = current.reply_to_message
    return messages

@filters.command("q") & filters.reply
async def quotely_handler(client, message: Message):
    # Parse background color or default white
    bg_color = "white"
    if len(message.command) > 1:
        bg_color = message.command[1].lower()

    # Gather all messages in chain
    messages = await gather_messages(message)

    # Prepare fonts
    try:
        font_username = ImageFont.truetype(FONT_PATH, 22)
        font_message = ImageFont.truetype(FONT_PATH, 18)
    except:
        # fallback to default PIL font
        font_username = ImageFont.load_default()
        font_message = ImageFont.load_default()

    padding = 20
    max_width = 512 - padding * 2
    line_spacing = 10
    total_height = padding  # start with padding on top

    # First pass: calculate total height of image
    # We'll sum heights of username + message or sticker for each message
    for msg in messages:
        # username height
        total_height += font_username.getsize(msg.from_user.first_name if msg.from_user else "Unknown")[1] + 5

        if msg.text:
            # estimate text height with wrapping
            dummy_img = Image.new("RGBA", (max_width, 1000))
            draw = ImageDraw.Draw(dummy_img)
            y_end = draw_text(draw, (0,0), msg.text, font_message, max_width)
            total_height += y_end + line_spacing
        elif msg.sticker:
            # Sticker height ~ 150 px
            total_height += 150 + line_spacing
        else:
            # Unknown content height fallback
            total_height += 50 + line_spacing

    total_height += padding  # bottom padding

    # Create base image
    img = Image.new("RGBA", (512, total_height), bg_color)
    draw = ImageDraw.Draw(img)

    y_offset = padding

    for msg in messages:
        username = msg.from_user.first_name if msg.from_user else "Unknown"
        # Draw username
        draw.text((padding, y_offset), username, font=font_username, fill=(0,0,0))
        y_offset += font_username.getsize(username)[1] + 5

        # Draw message content
        if msg.text:
            y_offset = draw_text(draw, (padding, y_offset), msg.text, font_message, max_width)
            y_offset += line_spacing
        elif msg.sticker:
            # Download and embed sticker as PNG
            sticker_img = await get_sticker_png(client, msg.sticker)
            # Resize sticker to max width 150 and maintain aspect ratio
            max_sticker_width = 150
            ratio = min(max_sticker_width / sticker_img.width, 1)
            new_size = (int(sticker_img.width * ratio), int(sticker_img.height * ratio))
            sticker_img = sticker_img.resize(new_size, Image.ANTIALIAS)
            img.paste(sticker_img, (padding, y_offset), sticker_img)
            y_offset += new_size[1] + line_spacing
        else:
            draw.text((padding, y_offset), "[Unsupported content]", font=font_message, fill=(0,0,0))
            y_offset += font_message.getsize("[Unsupported content]")[1] + line_spacing

    # Save to bytes
    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)

    await message.reply_photo(photo=bio, caption=f"Quoted with background color: {bg_color}")
