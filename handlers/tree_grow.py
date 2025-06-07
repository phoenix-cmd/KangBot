import random
import time
from pymongo import MongoClient
from pyrogram import filters
from pyrogram.types import Message
from client import app
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# Helper to get user data from DB
def get_user_tree(user_id):
    return collection.find_one({"user_id": user_id})

# Helper to update user data in DB
def update_user_tree(user_id, update_dict):
    collection.update_one({"user_id": user_id}, {"$set": update_dict}, upsert=True)

# /growtree command
@app.on_message(filters.command("growdih"))
async def grow_tree(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    now = int(time.time())

    user_data = get_user_tree(user_id)

    if user_data and now - user_data.get("last_grow", 0) < 86400:
        remaining = 86400 - (now - user_data["last_grow"])
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply(
            f"🌳 You already grew your dih today!\nTry again in {hours}h {minutes}m."
        )

    growth = random.randint(1, 15)
    new_height = growth
    if user_data:
        new_height += user_data.get("height", 0)

    update_user_tree(user_id, {
        "height": new_height,
        "last_grow": now,
        "name": username
    })

    await message.reply(
        f"🌱 Your dih grew by **{growth} cm** today!\n"
        f"🌳 Current height: **{new_height} cm**"
    )

# /mytree command
@app.on_message(filters.command("mydih"))
async def check_tree(client, message: Message):
    user_id = message.from_user.id
    user_data = get_user_tree(user_id)

    if not user_data:
        return await message.reply("🌱 You haven't started growing your dih yet. Use /growdih!")

    await message.reply(
        f"🌳 Your current dih height is **{user_data.get('height', 0)} cm**.\nKeep growing it every day!"
    )

# /treeboard command
@app.on_message(filters.command("dihboard"))
async def tree_leaderboard(client, message: Message):
    # Find top 10 users by height descending
    top_users = collection.find().sort("height", -1).limit(10)

    board = "🌳 **Top 10 Tallest Dih** 🌳\n\n"
    rank = 1
    empty = True
    for user_data in top_users:
        empty = False
        name = user_data.get("name", f"User {user_data.get('user_id')}")
        height = user_data.get("height", 0)
        board += f"{rank}. **{name}** — {height} cm\n"
        rank += 1

    if empty:
        return await message.reply("No dih has been grown yet 🌱")

    await message.reply(board)
