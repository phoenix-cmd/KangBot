import os
import html
from datetime import datetime
from pyrogram.types import Message
from pyrogram import Client

LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", -1001234567890))

def get_human_readable_size(size_bytes):
    if size_bytes is None:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def get_media_info(message: Message):
    media = message.reply_to_message
    if not media:
        return "📎 No media"
    
    if media.photo:
        return f"🖼️ Photo - Size: {get_human_readable_size(media.photo.file_size)}"
    elif media.video:
        return f"🎬 Video - Duration: {media.video.duration}s, Size: {get_human_readable_size(media.video.file_size)}"
    elif media.animation:
        return f"📽️ Animation (GIF) - Duration: {media.animation.duration}s, Size: {get_human_readable_size(media.animation.file_size)}"
    elif media.document:
        return f"📄 Document - MIME: {media.document.mime_type}, Size: {get_human_readable_size(media.document.file_size)}"
    elif media.sticker:
        format_type = "🖼️ Static" if not media.sticker.is_animated and not media.sticker.is_video else (
            "🎞️ Animated" if media.sticker.is_animated else "🎥 Video"
        )
        return f"💟 Sticker - {format_type}, Size: {get_human_readable_size(media.sticker.file_size)}"
    else:
        return "📎 Unknown media type"

def get_log_text(message: Message, command: str | None = None):
    user = message.from_user
    chat = message.chat
    cmd_text = command or (message.text or "<no text>")
    
    safe_user_name = html.escape(user.first_name)
    safe_chat_title = html.escape(chat.title) if chat.title else "Private"
    safe_cmd_text = html.escape(cmd_text)
    safe_media_info = html.escape(get_media_info(message))

    return (
        f"📝 <b>Command Log</b>\n"
        f"👤 <b>User:</b> {safe_user_name} (<code>{user.id}</code>)\n"
        f"💬 <b>Chat:</b> {safe_chat_title} (<code>{chat.id}</code>)\n"
        f"🔠 <b>Command:</b> <code>{safe_cmd_text}</code>\n"
        f"🕓 <b>Time:</b> <code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</code>\n"
        f"{safe_media_info}"
    )


async def log_to_channel(client: Client, message: Message, command: str | None = None):
    try:
        log_text = get_log_text(message, command)
        await client.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=log_text,
            parse_mode="html",
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"[LOG ERROR] Failed to log to channel: {e}")

