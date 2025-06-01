import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from huggingface_hub import InferenceClient

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# Initialize Hugging Face client
hf_client = InferenceClient(provider="hf-inference", api_key=HF_API_TOKEN)

app = Client("ai_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Chat handler: reply to any text message that is not a command
@app.on_message(filters.text & ~filters.command)
async def chat_reply(client, message):
    user_text = message.text

    # Use Hugging Face conversational model, e.g. microsoft/DialoGPT-medium
    try:
        response = hf_client.conversational(
            user_text,
            model="microsoft/DialoGPT-medium"
        )
        # response is a dict with key 'generated_text'
        reply = response.get("generated_text", "Sorry, I don't know what to say.")
    except Exception as e:
        reply = "Oops, something went wrong."

    await message.reply(reply)

if __name__ == "__main__":
    print("Bot started!")
    app.run()
