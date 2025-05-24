import asyncio
from collections import deque
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from py_tgcalls import PyTgCalls
from py_tgcalls.exceptions import NoActiveGroupCall
from py_tgcalls.types import Update, StreamType
from py_tgcalls.types.stream import StreamAudioEnded
from yt_dlp import YoutubeDL

# Globals for queues and states per chat_id
queues = {}          # chat_id -> deque of dict { "url": str, "title": str, "requested_by": str }
playback_states = {} # chat_id -> dict with "paused":bool etc.

# YTDL options for crisp audio
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'extract_flat': 'in_playlist',
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'source_address': '0.0.0.0',
}

ydl = YoutubeDL(YTDL_OPTS)

pytgcalls = None
client = None

def keyboard(chat_id):
    buttons = [
        [
            InlineKeyboardButton("⏸ Pause", callback_data=f"music_pause:{chat_id}"),
            InlineKeyboardButton("▶ Resume", callback_data=f"music_resume:{chat_id}"),
            InlineKeyboardButton("⏭ Skip", callback_data=f"music_skip:{chat_id}"),
            InlineKeyboardButton("⏹ Stop", callback_data=f"music_stop:{chat_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

async def get_audio_url(search: str):
    """
    Get direct audio URL from YouTube search or URL
    """
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: ydl.extract_info(search, download=False))
    if 'entries' in info:
        info = info['entries'][0]  # first search result
    return info['url'], info.get('title', 'Unknown title')

async def start_playback(chat_id):
    """
    Start playing audio for chat_id if queue is not empty
    """
    if chat_id not in queues or not queues[chat_id]:
        # No more songs in queue
        playback_states.pop(chat_id, None)
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        return

    song = queues[chat_id][0]  # current song
    audio_url = song["url"]

    try:
        await pytgcalls.join_group_call(
            chat_id,
            PyTgCalls.streams.AudioPiped(audio_url),
            stream_type=StreamType().pulse_stream
        )
    except NoActiveGroupCall:
        await client.send_message(chat_id, "❌ Please start a voice chat in this group first!")
        queues.pop(chat_id, None)
        playback_states.pop(chat_id, None)
        return
    except Exception as e:
        await client.send_message(chat_id, f"⚠️ Failed to join voice chat: {e}")
        return

    playback_states[chat_id] = {"paused": False}

    await client.send_message(
        chat_id,
        f"🎵 Now playing: **{song['title']}**\nRequested by: {song['requested_by']}",
        reply_markup=keyboard(chat_id)
    )

async def play_next(chat_id):
    """
    Remove current song and play next if available
    """
    if chat_id not in queues or not queues[chat_id]:
        playback_states.pop(chat_id, None)
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        await client.send_message(chat_id, "Playlist ended, leaving voice chat.")
        return

    queues[chat_id].popleft()
    if not queues[chat_id]:
        playback_states.pop(chat_id, None)
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        await client.send_message(chat_id, "Playlist ended, leaving voice chat.")
        return

    await start_playback(chat_id)

# === Command handlers ===

async def cmd_play(client: Client, message: Message):
    chat_id = message.chat.id

    if len(message.command) < 2:
        await message.reply("Usage: /play <YouTube URL or search keywords>")
        return

    query = " ".join(message.command[1:])

    try:
        url, title = await get_audio_url(query)
    except Exception as e:
        await message.reply(f"Failed to find audio: {e}")
        return

    if chat_id not in queues:
        queues[chat_id] = deque()

    queues[chat_id].append({
        "url": url,
        "title": title,
        "requested_by": message.from_user.mention if message.from_user else "Unknown"
    })

    await message.reply(f"Added to queue: **{title}**")

    # If nothing is playing, start playback
    if chat_id not in playback_states and len(queues[chat_id]) == 1:
        await start_playback(chat_id)

async def cmd_skip(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]:
        await message.reply("No music is currently playing.")
        return
    await play_next(chat_id)
    await message.reply("⏭ Skipped current track.")

async def cmd_pause(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in playback_states or playback_states[chat_id].get("paused", False):
        await message.reply("Music is not playing.")
        return
    try:
        await pytgcalls.pause_stream(chat_id)
        playback_states[chat_id]["paused"] = True
        await message.reply("⏸ Paused playback.")
    except Exception as e:
        await message.reply(f"Failed to pause: {e}")

async def cmd_resume(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in playback_states or not playback_states[chat_id].get("paused", False):
        await message.reply("Music is not paused.")
        return
    try:
        await pytgcalls.resume_stream(chat_id)
        playback_states[chat_id]["paused"] = False
        await message.reply("▶ Resumed playback.")
    except Exception as e:
        await message.reply(f"Failed to resume: {e}")

async def cmd_stop(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in queues:
        await message.reply("No music is playing.")
        return
    queues.pop(chat_id, None)
    playback_states.pop(chat_id, None)
    try:
        await pytgcalls.leave_group_call(chat_id)
    except Exception:
        pass
    await message.reply("⏹ Stopped playback and cleared the queue.")

# === Callback query handler for inline buttons ===

async def callback_handler(client: Client, cq: CallbackQuery):
    data = cq.data
    chat_id = int(data.split(":")[1])

    if data.startswith("music_pause"):
        if chat_id in playback_states and not playback_states[chat_id].get("paused", False):
            try:
                await pytgcalls.pause_stream(chat_id)
                playback_states[chat_id]["paused"] = True
                await cq.answer("Paused ✅", show_alert=False)
                await client.edit_message_reply_markup(chat_id, cq.message.message_id, reply_markup=keyboard(chat_id))
            except Exception as e:
                await cq.answer(f"Error: {e}", show_alert=True)
        else:
            await cq.answer("Already paused.", show_alert=False)

    elif data.startswith("music_resume"):
        if chat_id in playback_states and playback_states[chat_id].get("paused", False):
            try:
                await pytgcalls.resume_stream(chat_id)
                playback_states[chat_id]["paused"] = False
                await cq.answer("Resumed ✅", show_alert=False)
                await client.edit_message_reply_markup(chat_id, cq.message.message_id, reply_markup=keyboard(chat_id))
            except Exception as e:
                await cq.answer(f"Error: {e}", show_alert=True)
        else:
            await cq.answer("Not paused.", show_alert=False)

    elif data.startswith("music_skip"):
        if chat_id in queues and queues[chat_id]:
            await play_next(chat_id)
            await cq.answer("Skipped ✅", show_alert=False)
            await client.edit_message_reply_markup(chat_id, cq.message.message_id, reply_markup=keyboard(chat_id))
        else:
            await cq.answer("No song to skip.", show_alert=False)

    elif data.startswith("music_stop"):
        if chat_id in queues:
            queues.pop(chat_id, None)
        playback_states.pop(chat_id, None)
        try:
            await pytgcalls.leave_group_call(chat_id)
        except Exception:
            pass
        await cq.answer("Stopped playback ✅", show_alert=False)
        await client.edit_message_reply_markup(chat_id, cq.message.message_id, reply_markup=None)

def init_music(app: Client):
    global client, pytgcalls
    client = app
    pytgcalls = PyTgCalls(client)

    # Register event handlers
    app.add_handler(filters.command("play")(cmd_play))
    app.add_handler(filters.command("skip")(cmd_skip))
    app.add_handler(filters.command("pause")(cmd_pause))
    app.add_handler(filters.command("resume")(cmd_resume))
    app.add_handler(filters.command("stop")(cmd_stop))
    app.add_handler(filters.callback_query(filters.regex("^music_"))(callback_handler))

    # Start pytgcalls
    pytgcalls.start()

    # Listen for audio end event to play next track
    @pytgcalls.on_stream_end()
    async def on_stream_end(_, update: Update):
        if isinstance(update, StreamAudioEnded):
            chat_id = update.chat_id
            await play_next(chat_id)
