import os
from dotenv import load_dotenv
from pyrogram import filters
from huggingface_hub import InferenceClient

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")

hf_client = InferenceClient(provider="hf-inference", api_key=HF_API_TOKEN)

async def ai_chat_reply(client, message):
    user_text = message.text
    try:
        response = hf_client.conversational(
            user_text,
            model="microsoft/DialoGPT-medium"
        )
        reply = response.get("generated_text", "Sorry, I don't know what to say.")
    except Exception:
        reply = "Oops, something went wrong."
    await message.reply(reply)

# Expose filter for handler registration
ai_handler = filters.text & ~filters.command()
