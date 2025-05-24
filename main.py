from fastapi import FastAPI, Request
import uvicorn
import openai
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Set up bot and scheduler
bot = Bot(token=TELEGRAM_TOKEN)
scheduler = AsyncIOScheduler()
scheduler.start()

# FastAPI app
app = FastAPI()

# Telegram bot app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ChatGPT query function
async def chat_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    response = await chat_with_gpt(user_input)
    await update.message.reply_text(response)

# Reminder command
async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /remind <seconds> <message>")
        return
    delay = int(context.args[0])
    reminder_text = ' '.join(context.args[1:])
    scheduler.add_job(lambda: asyncio.create_task(bot.send_message(chat_id=update.effective_chat.id, text=reminder_text)), 'date', run_date=(update.message.date + timedelta(seconds=delay)))
    await update.message.reply_text(f"Reminder set for {delay} seconds from now.")

# Register handlers
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CommandHandler("remind", set_reminder))

# Webhook endpoint (optional if using polling)
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# Startup event to run Telegram bot in polling mode
@app.on_event("startup")
async def start_bot():
    asyncio.create_task(telegram_app.run_polling())

# Run locally (for testing)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
