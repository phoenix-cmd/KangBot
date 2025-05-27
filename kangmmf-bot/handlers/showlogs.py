import os
from pyrogram import filters
from pyrogram.types import Message

LOG_FILE_PATH = "bot.log"
OWNER_ID = int(os.environ.get("OWNER_ID", 123456789))  # replace with your owner ID

async def tail(file_path, lines=50):
    try:
        with open(file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            buffer = bytearray()
            pointer = f.tell() - 1
            count = 0

            while pointer >= 0 and count < lines:
                f.seek(pointer)
                byte = f.read(1)
                if byte == b'\n' and buffer:
                    count += 1
                buffer.extend(byte)
                pointer -= 1

            result = buffer[::-1].decode(errors='ignore')
            return '\n'.join(result.splitlines()[-lines:])
    except Exception as e:
        return f"Error reading log file: {e}"

@app.on_message(filters.command("getlogs") & filters.user(OWNER_ID))
async def send_logs(client, message: Message):
    if not os.path.exists(LOG_FILE_PATH):
        open(LOG_FILE_PATH, "a").close()  # create empty log file if missing

    logs = await tail(LOG_FILE_PATH, 50)
    if not logs.strip():
        await message.reply_text("Log file is empty.")
        return

    # Reply with logs as plain text
    # Telegram messages have a max length, so truncate if needed (~4096 chars)
    max_length = 4000
    if len(logs) > max_length:
        logs = logs[-max_length:]
        logs = "…(truncated)…\n" + logs

    await message.reply_text(f"Last 50 lines of logs:\n\n<pre>{logs}</pre>", parse_mode="html")
