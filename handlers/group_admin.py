from client import app
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from datetime import timedelta, datetime


async def is_admin(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ("administrator", "creator")


async def is_target_admin(client, chat_id: int, user_id: int):
    member = await client.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


@app.on_message(filters.command("kick") & filters.group)
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


@app.on_message(filters.command("ban") & filters.group)
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


@app.on_message(filters.command("unban") & filters.group)
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


@app.on_message(filters.command("mute") & filters.group)
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


@app.on_message(filters.command("unmute") & filters.group)
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
