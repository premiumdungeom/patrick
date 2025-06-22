from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher
from handlers import register_handlers
from config import TOKEN

app = Flask(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

# Register all your handlers
register_handlers(dispatcher)

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

    # Get your deployment URL (set in config.py as WEBHOOK_URL)
    from config import WEBHOOK_URL

    # Set webhook
    bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook set and bot is running on Render...")

    # Run Flask app
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
