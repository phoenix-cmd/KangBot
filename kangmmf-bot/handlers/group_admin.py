from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.handlers import MessageHandler
from datetime import timedelta


async def is_admin(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


async def kick_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")

    if not message.reply_to_message:
        return await message.reply("Reply to the user you want to kick.")

    user_id = message.reply_to_message.from_user.id
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

    try:
        await client.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply("User banned successfully.")
    except Exception as e:
        await message.reply(f"Failed to ban: {e}")


async def unban_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")
    if not message.reply_to_message:
        return await message.reply("Reply to a user to unban.")

    try:
        await client.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await message.reply("User unbanned.")
    except Exception as e:
        await message.reply(f"Error: {e}")


async def mute_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")
    if not message.reply_to_message:
        return await message.reply("Reply to a user to mute.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            permissions=ChatPermissions(),
            until_date=timedelta(hours=1)  # mute for 1 hour
        )
        await message.reply("User muted for 1 hour.")
    except Exception as e:
        await message.reply(f"Error: {e}")


async def unmute_user(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply("You need to be an admin to use this.")
    if not message.reply_to_message:
        return await message.reply("Reply to a user to unmute.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            message.reply_to_message.from_user.id,
            permissions=ChatPermissions(can_send_messages=True)
        )
        await message.reply("User unmuted.")
    except Exception as e:
        await message.reply(f"Error: {e}")


# Handler list
group_admin_handlers = [
    MessageHandler(kick_user, filters.command("kick") & filters.group),
    MessageHandler(ban_user, filters.command("ban") & filters.group),
    MessageHandler(unban_user, filters.command("unban") & filters.group),
    MessageHandler(mute_user, filters.command("mute") & filters.group),
    MessageHandler(unmute_user, filters.command("unmute") & filters.group),
]
