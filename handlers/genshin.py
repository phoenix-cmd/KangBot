import os
import json
import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GAME_DATA_FILE = "data/genshin_data.json"
ENKA_API_BASE = "https://enka.network/api/uid/"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def load_game_data():
    """Load saved Genshin Impact UIDs"""
    if os.path.exists(GAME_DATA_FILE):
        with open(GAME_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_game_data(data):
    """Save Genshin Impact UIDs"""
    with open(GAME_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def get_genshin_profile(uid: str):
    """Fetch Genshin Impact profile data from Enka Network API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ENKA_API_BASE}{uid}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch profile: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return None

async def get_character_card(uid: str, character_id: str):
    """Fetch character card from Enka Network API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ENKA_API_BASE}{uid}/character/{character_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch character card: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error fetching character card: {e}")
        return None

@app.on_message(filters.command("gilogin"))
async def save_genshin_uid(_, message: Message):
    """Save Genshin Impact UID for a user"""
    try:
        # Get UID from command arguments
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("❌ Please provide your Genshin Impact UID.\nUsage: `/gilogin <uid>`")
            return

        uid = args[1].strip()
        if not uid.isdigit() or len(uid) != 9:
            await message.reply_text("❌ Invalid UID format. Please provide a valid 9-digit UID.")
            return

        # Load existing data
        data = load_game_data()
        
        # Save UID for the user
        user_id = str(message.from_user.id)
        data[user_id] = uid
        save_game_data(data)

        await message.reply_text(f"✅ Successfully saved your Genshin Impact UID: `{uid}`")
    except Exception as e:
        logger.error(f"Error in save_genshin_uid: {e}")
        await message.reply_text("❌ An error occurred while saving your UID.")

@app.on_message(filters.command("myc"))
async def show_genshin_profile(_, message: Message):
    """Show Genshin Impact profile and character list"""
    try:
        # Load saved UID
        data = load_game_data()
        user_id = str(message.from_user.id)
        
        if user_id not in data:
            await message.reply_text("❌ You haven't set your Genshin Impact UID yet.\nUse `/gilogin <uid>` to set it.")
            return

        uid = data[user_id]
        
        # Fetch profile data
        profile = await get_genshin_profile(uid)
        if not profile:
            await message.reply_text("❌ Failed to fetch profile data. Please try again later.")
            return

        # Create profile message
        profile_text = f"🎮 **Genshin Impact Profile**\n\n"
        profile_text += f"UID: `{uid}`\n"
        profile_text += f"Adventure Rank: {profile.get('adventureRank', 'N/A')}\n"
        profile_text += f"World Level: {profile.get('worldLevel', 'N/A')}\n\n"
        profile_text += "**Available Characters:**\n"

        # Create inline keyboard for characters
        characters = profile.get('characters', [])
        keyboard = []
        for char in characters:
            char_id = char.get('id')
            char_name = char.get('name', 'Unknown')
            char_level = char.get('level', 0)
            profile_text += f"• {char_name} (Lvl {char_level})\n"
            keyboard.append([InlineKeyboardButton(
                f"{char_name} (Lvl {char_level})",
                callback_data=f"char_{uid}_{char_id}"
            )])

        # Add refresh button
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{uid}")])

        await message.reply_text(
            profile_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_genshin_profile: {e}")
        await message.reply_text("❌ An error occurred while fetching your profile.")

@app.on_callback_query(filters.regex(r"^char_"))
async def show_character_card(_, callback_query: CallbackQuery):
    """Show character card when a character is selected"""
    try:
        # Parse callback data
        _, uid, char_id = callback_query.data.split('_')
        
        # Fetch character card
        card = await get_character_card(uid, char_id)
        if not card:
            await callback_query.answer("Failed to fetch character card", show_alert=True)
            return

        # Create character card message
        char_name = card.get('name', 'Unknown')
        char_level = card.get('level', 0)
        char_element = card.get('element', 'Unknown')
        char_weapon = card.get('weapon', {}).get('name', 'Unknown')
        char_weapon_level = card.get('weapon', {}).get('level', 0)

        card_text = f"🎭 **{char_name}**\n\n"
        card_text += f"Level: {char_level}\n"
        card_text += f"Element: {char_element}\n"
        card_text += f"Weapon: {char_weapon} (Lvl {char_weapon_level})\n\n"

        # Add artifacts
        card_text += "**Artifacts:**\n"
        for artifact in card.get('artifacts', []):
            card_text += f"• {artifact.get('name', 'Unknown')} ({artifact.get('set', 'Unknown')})\n"

        # Add talents
        card_text += "\n**Talents:**\n"
        for talent in card.get('talents', []):
            card_text += f"• {talent.get('name', 'Unknown')}: Lvl {talent.get('level', 0)}\n"

        # Create back button
        keyboard = [[InlineKeyboardButton("⬅️ Back to Profile", callback_data=f"refresh_{uid}")]]

        await callback_query.edit_message_text(
            card_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in show_character_card: {e}")
        await callback_query.answer("An error occurred", show_alert=True)

@app.on_callback_query(filters.regex(r"^refresh_"))
async def refresh_profile(_, callback_query: CallbackQuery):
    """Refresh the profile view"""
    try:
        uid = callback_query.data.split('_')[1]
        # Reuse the show_genshin_profile logic
        await show_genshin_profile(_, callback_query.message)
        await callback_query.answer("Profile refreshed!")
    except Exception as e:
        logger.error(f"Error in refresh_profile: {e}")
        await callback_query.answer("Failed to refresh profile", show_alert=True) 
