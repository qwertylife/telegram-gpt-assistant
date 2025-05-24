import os
from dotenv import load_dotenv
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import openai

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram bot app
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}],
            temperature=0.7
        )
        reply = response['choices'][0]['message']['content'].strip()
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Error: " + str(e))

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Startup: initialize bot (manual polling)
@app.on_event("startup")
async def start_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()

# Shutdown: cleanly stop bot
@app.on_event("shutdown")
async def stop_bot():
    await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()

# Optional healthcheck route
@app.get("/")
async def root():
    return {"status": "Bot is running"}
