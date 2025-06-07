from client import app
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, FloodWait
from datetime import timedelta, datetime
import logging
from typing import Optional, Union, Dict, List
import json
import os
import re
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Warning system storage
WARNINGS_FILE = "warnings.json"

# Anti-spam settings
SPAM_SETTINGS_FILE = "spam_settings.json"
DEFAULT_SPAM_SETTINGS = {
    "message_limit": 5,  # messages
    "time_window": 10,   # seconds
    "link_limit": 3,     # links
    "media_limit": 5,    # media messages
    "action": "mute",    # action to take: mute, warn, or ban
    "mute_duration": 3600  # mute duration in seconds (1 hour)
}

# Message tracking for spam detection
message_tracker = defaultdict(lambda: {"messages": [], "links": 0, "media": 0})

def load_warnings() -> Dict[str, Dict[str, List[Dict]]]:
    """Load warnings from file."""
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Error loading warnings file")
            return {}
    return {}

def save_warnings(warnings: Dict[str, Dict[str, List[Dict]]]):
    """Save warnings to file."""
    try:
        with open(WARNINGS_FILE, 'w') as f:
            json.dump(warnings, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving warnings: {e}")

def get_user_warnings(chat_id: str, user_id: str) -> List[Dict]:
    """Get warnings for a specific user in a chat."""
    warnings = load_warnings()
    return warnings.get(str(chat_id), {}).get(str(user_id), [])

def add_warning(chat_id: str, user_id: str, admin_id: str, reason: str):
    """Add a warning for a user."""
    warnings = load_warnings()
    if str(chat_id) not in warnings:
        warnings[str(chat_id)] = {}
    if str(user_id) not in warnings[str(chat_id)]:
        warnings[str(chat_id)][str(user_id)] = []
    
    warnings[str(chat_id)][str(user_id)].append({
        "admin_id": admin_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    save_warnings(warnings)

def remove_warning(chat_id: str, user_id: str, warning_index: int):
    """Remove a specific warning for a user."""
    warnings = load_warnings()
    if str(chat_id) in warnings and str(user_id) in warnings[str(chat_id)]:
        if 0 <= warning_index < len(warnings[str(chat_id)][str(user_id)]):
            warnings[str(chat_id)][str(user_id)].pop(warning_index)
            save_warnings(warnings)
            return True
    return False

async def is_admin(client, message: Message) -> bool:
    """Check if the user is an admin in the chat."""
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def is_target_admin(client, chat_id: int, user_id: int) -> bool:
    """Check if the target user is an admin in the chat."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Error checking target admin status: {e}")
        return False

async def is_bot_admin(client, chat_id: int) -> bool:
    """Check if the bot is an admin in the chat."""
    try:
        bot = await client.get_me()
        member = await client.get_chat_member(chat_id, bot.id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Error checking bot admin status: {e}")
        return False

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parse duration string (e.g., '1h', '30m', '2d') into timedelta."""
    try:
        unit = duration_str[-1].lower()
        value = int(duration_str[:-1])
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'd':
            return timedelta(days=value)
        else:
            return None
    except (ValueError, IndexError):
        return None

@app.on_message(filters.command(["kick", "k"]) & filters.group)
async def kick_user(client, message: Message):
    """Kick a user from the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not await is_bot_admin(client, message.chat.id):
        return await message.reply("❌ I need to be an admin to perform this action.")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to the user you want to kick.\nUsage: `/kick` (reply to user)")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("❌ I can't kick an admin.")

    try:
        await client.kick_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has been kicked.")
    except ChatAdminRequired:
        await message.reply("❌ I don't have permission to kick users.")
    except UserAdminInvalid:
        await message.reply("❌ I can't kick this user.")
    except Exception as e:
        logger.error(f"Error in kick command: {e}")
        await message.reply("❌ An error occurred while trying to kick the user.")

@app.on_message(filters.command(["ban", "b"]) & filters.group)
async def ban_user(client, message: Message):
    """Ban a user from the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not await is_bot_admin(client, message.chat.id):
        return await message.reply("❌ I need to be an admin to perform this action.")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to ban.\nUsage: `/ban` (reply to user)")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("❌ I can't ban an admin.")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has been banned.")
    except ChatAdminRequired:
        await message.reply("❌ I don't have permission to ban users.")
    except UserAdminInvalid:
        await message.reply("❌ I can't ban this user.")
    except Exception as e:
        logger.error(f"Error in ban command: {e}")
        await message.reply("❌ An error occurred while trying to ban the user.")

@app.on_message(filters.command(["unban", "ub"]) & filters.group)
async def unban_user(client, message: Message):
    """Unban a user from the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not await is_bot_admin(client, message.chat.id):
        return await message.reply("❌ I need to be an admin to perform this action.")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to unban.\nUsage: `/unban` (reply to user)")

    user_id = message.reply_to_message.from_user.id

    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has been unbanned.")
    except ChatAdminRequired:
        await message.reply("❌ I don't have permission to unban users.")
    except Exception as e:
        logger.error(f"Error in unban command: {e}")
        await message.reply("❌ An error occurred while trying to unban the user.")

@app.on_message(filters.command(["mute", "m"]) & filters.group)
async def mute_user(client, message: Message):
    """Mute a user in the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not await is_bot_admin(client, message.chat.id):
        return await message.reply("❌ I need to be an admin to perform this action.")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to mute.\nUsage: `/mute [duration]` (reply to user)\nExample: `/mute 1h` or `/mute 30m`")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("❌ I can't mute an admin.")

    # Parse duration from command
    duration = timedelta(hours=1)  # Default duration
    if len(message.command) > 1:
        parsed_duration = parse_duration(message.command[1])
        if parsed_duration:
            duration = parsed_duration
        else:
            return await message.reply("❌ Invalid duration format. Use: 1h, 30m, 2d")

    until_date = datetime.utcnow() + duration

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(),
            until_date=until_date
        )
        duration_str = f"{duration.total_seconds()/3600:.1f} hours" if duration.total_seconds() >= 3600 else f"{duration.total_seconds()/60:.0f} minutes"
        await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has been muted for {duration_str}.")
    except ChatAdminRequired:
        await message.reply("❌ I don't have permission to mute users.")
    except UserAdminInvalid:
        await message.reply("❌ I can't mute this user.")
    except Exception as e:
        logger.error(f"Error in mute command: {e}")
        await message.reply("❌ An error occurred while trying to mute the user.")

@app.on_message(filters.command(["unmute", "um"]) & filters.group)
async def unmute_user(client, message: Message):
    """Unmute a user in the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not await is_bot_admin(client, message.chat.id):
        return await message.reply("❌ I need to be an admin to perform this action.")

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to unmute.\nUsage: `/unmute` (reply to user)")

    user_id = message.reply_to_message.from_user.id

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has been unmuted.")
    except ChatAdminRequired:
        await message.reply("❌ I don't have permission to unmute users.")
    except UserAdminInvalid:
        await message.reply("❌ I can't unmute this user.")
    except Exception as e:
        logger.error(f"Error in unmute command: {e}")
        await message.reply("❌ An error occurred while trying to unmute the user.")

@app.on_message(filters.command(["warn", "w"]) & filters.group)
async def warn_user(client, message: Message):
    """Warn a user in the group."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to warn.\nUsage: `/warn [reason]` (reply to user)")

    user_id = message.reply_to_message.from_user.id
    
    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("❌ I can't warn an admin.")

    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
    
    # Add warning
    add_warning(str(message.chat.id), str(user_id), str(message.from_user.id), reason)
    
    # Get current warnings
    warnings = get_user_warnings(str(message.chat.id), str(user_id))
    
    # Check if user should be banned (3 warnings)
    if len(warnings) >= 3:
        try:
            await client.ban_chat_member(message.chat.id, user_id)
            await message.reply(
                f"⚠️ User {message.reply_to_message.from_user.mention} has been banned after receiving 3 warnings.\n"
                f"Last warning reason: {reason}"
            )
        except Exception as e:
            logger.error(f"Error banning user after warnings: {e}")
            await message.reply("❌ Failed to ban user after 3 warnings.")
    else:
        await message.reply(
            f"⚠️ User {message.reply_to_message.from_user.mention} has been warned.\n"
            f"Reason: {reason}\n"
            f"Warnings: {len(warnings)}/3"
        )

@app.on_message(filters.command(["warnings", "warns"]) & filters.group)
async def view_warnings(client, message: Message):
    """View warnings for a user."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to view their warnings.\nUsage: `/warnings` (reply to user)")

    user_id = message.reply_to_message.from_user.id
    warnings = get_user_warnings(str(message.chat.id), str(user_id))
    
    if not warnings:
        return await message.reply(f"✅ User {message.reply_to_message.from_user.mention} has no warnings.")
    
    warning_text = f"⚠️ Warnings for {message.reply_to_message.from_user.mention}:\n\n"
    for i, warning in enumerate(warnings, 1):
        admin = await client.get_users(int(warning['admin_id']))
        warning_text += (
            f"{i}. Reason: {warning['reason']}\n"
            f"   By: {admin.mention}\n"
            f"   Date: {datetime.fromisoformat(warning['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
    
    await message.reply(warning_text)

@app.on_message(filters.command(["delwarn", "dw"]) & filters.group)
async def delete_warning(client, message: Message):
    """Delete a warning for a user."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if not message.reply_to_message:
        return await message.reply("❌ Reply to a user to delete their warning.\nUsage: `/delwarn [warning_number]` (reply to user)")

    if len(message.command) < 2:
        return await message.reply("❌ Please specify the warning number to delete.")

    try:
        warning_index = int(message.command[1]) - 1
    except ValueError:
        return await message.reply("❌ Invalid warning number.")

    user_id = message.reply_to_message.from_user.id
    
    if remove_warning(str(message.chat.id), str(user_id), warning_index):
        await message.reply(f"✅ Warning #{warning_index + 1} has been removed for {message.reply_to_message.from_user.mention}.")
    else:
        await message.reply("❌ Failed to remove warning. Warning number may be invalid.")

def load_spam_settings() -> Dict:
    """Load spam settings from file."""
    if os.path.exists(SPAM_SETTINGS_FILE):
        try:
            with open(SPAM_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Error loading spam settings file")
            return DEFAULT_SPAM_SETTINGS
    return DEFAULT_SPAM_SETTINGS

def save_spam_settings(settings: Dict):
    """Save spam settings to file."""
    try:
        with open(SPAM_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving spam settings: {e}")

def is_spam_message(message: Message, settings: Dict) -> bool:
    """Check if a message is spam based on current settings."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    current_time = datetime.utcnow()
    
    # Initialize user tracking if not exists
    if user_id not in message_tracker[chat_id]:
        message_tracker[chat_id][user_id] = {
            "messages": [],
            "links": 0,
            "media": 0
        }
    
    # Clean old messages
    message_tracker[chat_id][user_id]["messages"] = [
        msg for msg in message_tracker[chat_id][user_id]["messages"]
        if (current_time - msg["time"]).total_seconds() < settings["time_window"]
    ]
    
    # Check for links
    if message.text:
        links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.text)
        if links:
            message_tracker[chat_id][user_id]["links"] += len(links)
            if message_tracker[chat_id][user_id]["links"] > settings["link_limit"]:
                return True
    
    # Check for media
    if message.media:
        message_tracker[chat_id][user_id]["media"] += 1
        if message_tracker[chat_id][user_id]["media"] > settings["media_limit"]:
            return True
    
    # Add message to tracker
    message_tracker[chat_id][user_id]["messages"].append({
        "time": current_time
    })
    
    # Check message frequency
    if len(message_tracker[chat_id][user_id]["messages"]) > settings["message_limit"]:
        return True
    
    return False

async def handle_spam(client, message: Message, settings: Dict):
    """Handle spam detection and take appropriate action."""
    action = settings["action"]
    
    try:
        if action == "mute":
            until_date = datetime.utcnow() + timedelta(seconds=settings["mute_duration"])
            await client.restrict_chat_member(
                message.chat.id,
                message.from_user.id,
                permissions=ChatPermissions(),
                until_date=until_date
            )
            await message.reply(f"⚠️ {message.from_user.mention} has been muted for {settings['mute_duration']//3600} hours due to spam.")
        
        elif action == "warn":
            add_warning(str(message.chat.id), str(message.from_user.id), str(client.me.id), "Spam detected")
            await message.reply(f"⚠️ {message.from_user.mention} has been warned for spam.")
        
        elif action == "ban":
            await client.ban_chat_member(message.chat.id, message.from_user.id)
            await message.reply(f"🚫 {message.from_user.mention} has been banned for spam.")
    
    except Exception as e:
        logger.error(f"Error handling spam: {e}")
        await message.reply("❌ Failed to take action against spammer.")

@app.on_message(filters.group & ~filters.service)
async def spam_check(client, message: Message):
    """Check messages for spam."""
    if await is_admin(client, message):
        return  # Skip spam check for admins
    
    settings = load_spam_settings()
    if is_spam_message(message, settings):
        await handle_spam(client, message, settings)

@app.on_message(filters.command(["spamsettings", "ss"]) & filters.group)
async def spam_settings(client, message: Message):
    """View or modify spam settings."""
    if not await is_admin(client, message):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    settings = load_spam_settings()
    
    if len(message.command) == 1:
        # Show current settings
        settings_text = "📊 Current Spam Settings:\n\n"
        settings_text += f"• Message Limit: {settings['message_limit']} messages\n"
        settings_text += f"• Time Window: {settings['time_window']} seconds\n"
        settings_text += f"• Link Limit: {settings['link_limit']} links\n"
        settings_text += f"• Media Limit: {settings['media_limit']} media messages\n"
        settings_text += f"• Action: {settings['action']}\n"
        settings_text += f"• Mute Duration: {settings['mute_duration']//3600} hours\n\n"
        settings_text += "To modify settings, use:\n"
        settings_text += "/spamsettings [setting] [value]\n"
        settings_text += "Example: /spamsettings message_limit 10"
        
        await message.reply(settings_text)
        return
    
    if len(message.command) != 3:
        return await message.reply("❌ Invalid format. Use: /spamsettings [setting] [value]")
    
    setting = message.command[1].lower()
    try:
        value = int(message.command[2])
    except ValueError:
        return await message.reply("❌ Value must be a number.")
    
    if setting not in settings:
        return await message.reply("❌ Invalid setting. Available settings: message_limit, time_window, link_limit, media_limit, mute_duration")
    
    if setting == "action":
        if value not in ["mute", "warn", "ban"]:
            return await message.reply("❌ Invalid action. Use: mute, warn, or ban")
        settings[setting] = value
    else:
        if value < 1:
            return await message.reply("❌ Value must be greater than 0.")
        settings[setting] = value
    
    save_spam_settings(settings)
    await message.reply(f"✅ {setting} has been updated to {value}")
