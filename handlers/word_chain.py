from client import app
from pyrogram import filters
from pyrogram.types import Message
import logging
from typing import Dict, Set
import json
import os
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Game state storage
GAME_STATE_FILE = "data/word_chain_games.json"

# Minimum word length
MIN_WORD_LENGTH = 3

# Game timeout in minutes
GAME_TIMEOUT = 5

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

class WordChainGame:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.used_words: Set[str] = set()
        self.last_word: str = ""
        self.last_user_id: int = 0
        self.start_time: datetime = datetime.now()
        self.is_active: bool = True
        self.score: Dict[int, int] = {}  # user_id: score

    def is_valid_word(self, word: str, last_word: str) -> bool:
        """Check if the word is valid for the chain."""
        if not word or len(word) < MIN_WORD_LENGTH:
            return False
        
        if word in self.used_words:
            return False
        
        if last_word and word[0].lower() != last_word[-1].lower():
            return False
        
        return True

    def add_word(self, word: str, user_id: int) -> bool:
        """Add a word to the chain and update score."""
        if not self.is_valid_word(word, self.last_word):
            return False
        
        self.used_words.add(word.lower())
        self.last_word = word
        self.last_user_id = user_id
        self.start_time = datetime.now()
        
        # Update score
        if user_id not in self.score:
            self.score[user_id] = 0
        self.score[user_id] += 1
        
        return True

    def is_timed_out(self) -> bool:
        """Check if the game has timed out."""
        return (datetime.now() - self.start_time) > timedelta(minutes=GAME_TIMEOUT)

    def to_dict(self) -> dict:
        """Convert game state to dictionary for storage."""
        return {
            "chat_id": self.chat_id,
            "used_words": list(self.used_words),
            "last_word": self.last_word,
            "last_user_id": self.last_user_id,
            "start_time": self.start_time.isoformat(),
            "is_active": self.is_active,
            "score": self.score
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WordChainGame':
        """Create game instance from dictionary."""
        game = cls(data["chat_id"])
        game.used_words = set(data["used_words"])
        game.last_word = data["last_word"]
        game.last_user_id = data["last_user_id"]
        game.start_time = datetime.fromisoformat(data["start_time"])
        game.is_active = data["is_active"]
        game.score = data["score"]
        return game

# Global game storage
active_games: Dict[int, WordChainGame] = {}

def load_games():
    """Load games from file."""
    if os.path.exists(GAME_STATE_FILE):
        try:
            with open(GAME_STATE_FILE, 'r') as f:
                data = json.load(f)
                for chat_id, game_data in data.items():
                    active_games[int(chat_id)] = WordChainGame.from_dict(game_data)
        except Exception as e:
            logger.error(f"Error loading games: {e}")

def save_games():
    """Save games to file."""
    try:
        data = {str(chat_id): game.to_dict() for chat_id, game in active_games.items()}
        with open(GAME_STATE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving games: {e}")

# Load existing games
load_games()

@app.on_message(filters.command(["wordchain", "wc"]) & filters.group)
async def start_word_chain(client, message: Message):
    """Start a new word chain game."""
    try:
        chat_id = message.chat.id
        
        if chat_id in active_games and active_games[chat_id].is_active:
            return await message.reply("❌ A game is already in progress in this chat!")
        
        # Start new game
        game = WordChainGame(chat_id)
        active_games[chat_id] = game
        
        # Save game state
        save_games()
        
        await message.reply(
            "🎮 Word Chain Game Started!\n\n"
            "Rules:\n"
            f"• Words must be at least {MIN_WORD_LENGTH} letters long\n"
            "• Each word must start with the last letter of the previous word\n"
            "• No repeating words\n"
            "• Game times out after 5 minutes of inactivity\n\n"
            "Start by sending any word!"
        )
    except Exception as e:
        logger.error(f"Error in start_word_chain: {e}")
        await message.reply("❌ An error occurred while starting the game.")

@app.on_message(filters.command(["endchain", "ec"]) & filters.group)
async def end_word_chain(client, message: Message):
    """End the current word chain game."""
    try:
        chat_id = message.chat.id
        
        if chat_id not in active_games or not active_games[chat_id].is_active:
            return await message.reply("❌ No active game in this chat!")
        
        game = active_games[chat_id]
        game.is_active = False
        
        # Generate scoreboard
        if game.score:
            scoreboard = "🏆 Final Scores:\n\n"
            sorted_scores = sorted(game.score.items(), key=lambda x: x[1], reverse=True)
            for user_id, score in sorted_scores:
                try:
                    user = await client.get_users(user_id)
                    scoreboard += f"• {user.mention}: {score} points\n"
                except:
                    scoreboard += f"• User {user_id}: {score} points\n"
        else:
            scoreboard = "No words were played in this game."
        
        await message.reply(f"🎮 Game Over!\n\n{scoreboard}")
        
        # Remove game
        del active_games[chat_id]
        save_games()
    except Exception as e:
        logger.error(f"Error in end_word_chain: {e}")
        await message.reply("❌ An error occurred while ending the game.")

@app.on_message(filters.command(["chainstats", "cs"]) & filters.group)
async def show_chain_stats(client, message: Message):
    """Show current game statistics."""
    try:
        chat_id = message.chat.id
        
        if chat_id not in active_games or not active_games[chat_id].is_active:
            return await message.reply("❌ No active game in this chat!")
        
        game = active_games[chat_id]
        
        stats = "📊 Current Game Stats:\n\n"
        stats += f"• Total Words: {len(game.used_words)}\n"
        stats += f"• Last Word: {game.last_word}\n"
        
        if game.score:
            stats += "\n🏆 Current Scores:\n"
            sorted_scores = sorted(game.score.items(), key=lambda x: x[1], reverse=True)
            for user_id, score in sorted_scores[:5]:  # Show top 5
                try:
                    user = await client.get_users(user_id)
                    stats += f"• {user.mention}: {score} points\n"
                except:
                    stats += f"• User {user_id}: {score} points\n"
        
        await message.reply(stats)
    except Exception as e:
        logger.error(f"Error in show_chain_stats: {e}")
        await message.reply("❌ An error occurred while fetching game stats.")

@app.on_message(filters.group & ~filters.service & filters.text)
async def handle_word(client, message: Message):
    """Handle incoming words in the game."""
    try:
        chat_id = message.chat.id
        
        if chat_id not in active_games or not active_games[chat_id].is_active:
            return
        
        game = active_games[chat_id]
        
        # Check for timeout
        if game.is_timed_out():
            game.is_active = False
            await message.reply(
                "⏰ Game timed out due to inactivity!\n"
                "Use /wordchain to start a new game."
            )
            del active_games[chat_id]
            save_games()
            return
        
        # Get word from message
        word = message.text.strip().lower()
        
        # Skip if message is a command
        if word.startswith('/'):
            return
        
        # Validate and add word
        if game.add_word(word, message.from_user.id):
            # Save game state
            save_games()
            
            # Send confirmation
            await message.reply(
                f"✅ {message.from_user.mention} added: {word}\n"
                f"Next word should start with: {word[-1].upper()}"
            )
        else:
            if word in game.used_words:
                await message.reply("❌ This word has already been used!")
            elif len(word) < MIN_WORD_LENGTH:
                await message.reply(f"❌ Word must be at least {MIN_WORD_LENGTH} letters long!")
            elif game.last_word and word[0].lower() != game.last_word[-1].lower():
                await message.reply(f"❌ Word must start with '{game.last_word[-1].upper()}'!")
            else:
                await message.reply("❌ Invalid word!")
    except Exception as e:
        logger.error(f"Error in handle_word: {e}")
        await message.reply("❌ An error occurred while processing your word.") 
