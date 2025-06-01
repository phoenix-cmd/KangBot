from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatMemberStatus
from datetime import timedelta, datetime


async def is_admin(client, message: Message):
    if message.from_user is None:
        return False  # Handles anonymous admins
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


async def is_target_admin(client, chat_id: int, user_id: int):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


async def kick_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to the user you want to kick.")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("I can't kick an admin.")

    try:
        await client.kick_chat_member(message.chat.id, user_id)
        await message.reply("User kicked successfully.")
    except Exception as e:
        await message.reply(f"Error: {e}")


async def ban_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to a user to ban.")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("I can't ban an admin.")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await message.reply("User banned successfully.")
    except Exception as e:
        await message.reply(f"Failed to ban: {e}")


async def unban_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to a user to unban.")

    user_id = message.reply_to_message.from_user.id

    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply("User unbanned.")
    except Exception as e:
        await message.reply(f"Error: {e}")


async def mute_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to a user to mute.")

    user_id = message.reply_to_message.from_user.id

    if await is_target_admin(client, message.chat.id, user_id):
        return await message.reply("I can't mute an admin.")

    until_date = datetime.utcnow() + timedelta(hours=1)

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(),
            until_date=until_date
        )
        await message.reply("User muted for 1 hour.")
    except Exception as e:
        await message.reply(f"Error: {e}")


async def unmute_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to a user to unmute.")

    user_id = message.reply_to_message.from_user.id

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await message.reply("User unmuted.")
    except Exception as e:
        await message.reply(f"Error: {e}")


# ✅ Admincheck command
async def admin_check(client, message: Message):
    if message.chat.type not in ["supergroup", "group"]:
        return await message.reply("This command only works in groups.")

    if message.from_user is None:
        return await message.reply(
            "❌ You're using 'Anonymous Admin Mode'. Turn it off in group settings to use admin commands."
        )

    try:
        user = await client.get_chat_member(message.chat.id, message.from_user.id)
        bot = await client.get_chat_member(message.chat.id, (await client.get_me()).id)

        text = f"👤 **Your Admin Status:** `{user.status}`\n"
        text += f"🤖 **Bot Status:** `{bot.status}`\n\n"

        if bot.status == ChatMemberStatus.ADMINISTRATOR:
            perms = bot.privileges if hasattr(bot, "privileges") else bot
            text += "**Bot Permissions:**\n"
            text += f"  ├─ Can Restrict: `{getattr(perms, 'can_restrict_members', False)}`\n"
            text += f"  ├─ Can Delete: `{getattr(perms, 'can_delete_messages', False)}`\n"
            text += f"  └─ Can Promote: `{getattr(perms, 'can_promote_members', False)}`\n"

        await message.reply(text)
    except Exception as e:
        await message.reply(f"Error checking admin status:\n`{e}`")


# ✅ Handler list
group_admin_handlers = [
    MessageHandler(kick_user, filters.command("kick") & filters.group),
    MessageHandler(ban_user, filters.command("ban") & filters.group),
    MessageHandler(unban_user, filters.command("unban") & filters.group),
    MessageHandler(mute_user, filters.command("mute") & filters.group),
    MessageHandler(unmute_user, filters.command("unmute") & filters.group),
    MessageHandler(admin_check, filters.command("admincheck") & filters.group),
]
