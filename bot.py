from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, JobQueue
from handlers import register_handlers, schedule_weekly_contest
from config import TOKEN, WEBHOOK_URL

app = Flask(__name__)

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# Explicitly create a job queue for webhook mode
job_queue = JobQueue()
job_queue.set_dispatcher(dispatcher)
dispatcher.job_queue = job_queue
job_queue.start()

register_handlers(dispatcher)
schedule_weekly_contest(bot)

@app.route('/')
def index():
    return "🤖 Telegram Airdrop Bot is live!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

if __name__ == '__main__':
    import os
    bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook set and bot is running on Render...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
