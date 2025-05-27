# # client.py
# import os
# from pyrogram import Client

# app = Client(
#     "my_bot",
#     api_id=int(os.environ["API_ID"]),
#     api_hash=os.environ["API_HASH"],
#     bot_token=os.environ["BOT_TOKEN"]
# )
# client.py
import os
import logging
from pyrogram import Client

app = Client(
    "my_bot",
    api_id=int(os.environ["API_ID"]),
    api_hash=os.environ["API_HASH"],
    bot_token=os.environ["BOT_TOKEN"]
)

# Setup logging to file
logging.basicConfig(
    filename="bot.log",      # Log file name
    filemode="a",            # Append mode
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO       # Log level
)

logging.info("Bot started")  # Log bot start event
