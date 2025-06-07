import json
import random
import time
from pyrogram import filters
from pyrogram.types import Message
from client import app  # Your Pyrogram client

TREE_DATA_FILE = "tree_data.json"

def load_tree_data():
    try:
        with open(TREE_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_tree_data(data):
    with open(TREE_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# /growtree - grow the user's tree
@app.on_message(filters.command("growtree"))
async def grow_tree(client, message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.first_name
    tree_data = load_tree_data()
    now = int(time.time())

    user_data = tree_data.get(user_id, {"height": 0, "last_grow": 0})
    last_grow = user_data["last_grow"]

    # Check cooldown (1 day)
    if now - last_grow < 86400:
        remaining = 86400 - (now - last_grow)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return await message.reply(
            f"🌳 You already grew your tree today!\nTry again in {hours}h {minutes}m."
        )

    growth = random.randint(1, 15)
    user_data["height"] += growth
    user_data["last_grow"] = now
    user_data["name"] = username
    tree_data[user_id] = user_data
    save_tree_data(tree_data)

    await message.reply(
        f"🌱 Your tree grew by **{growth} cm** today!\n"
        f"🌳 Current height: **{user_data['height']} cm**"
    )

# /mytree - check tree height
@app.on_message(filters.command("mytree"))
async def check_tree(client, message: Message):
    user_id = str(message.from_user.id)
    tree_data = load_tree_data()
    user_data = tree_data.get(user_id)

    if not user_data:
        return await message.reply("🌱 You haven't started growing your tree yet. Use /growtree!")

    await message.reply(
        f"🌳 Your current tree height is **{user_data['height']} cm**.\nKeep growing it every day!"
    )

# /treeboard - top 10 tallest trees
@app.on_message(filters.command("treeboard"))
async def tree_leaderboard(client, message: Message):
    tree_data = load_tree_data()

    # Sort by height
    top_users = sorted(
        tree_data.items(), key=lambda x: x[1].get("height", 0), reverse=True
    )[:10]

    if not top_users:
        return await message.reply("No trees have been grown yet 🌱")

    board = "🌳 **Top 10 Tallest Trees** 🌳\n\n"
    for idx, (user_id, data) in enumerate(top_users, start=1):
        name = data.get("name", f"User {user_id}")
        height = data["height"]
        board += f"{idx}. **{name}** — {height} cm\n"

    await message.reply(board)
