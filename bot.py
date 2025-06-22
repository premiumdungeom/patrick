from telegram.ext import Updater
from handlers import register_handlers
from config import TOKEN, WEBHOOK_URL

import os
from flask import Flask, request

# Create a Flask web server
app = Flask(__name__)

# Create the Updater and Dispatcher
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Register all handlers
register_handlers(dispatcher)

@app.route('/')
def index():
    return "🤖 Bot is live!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = updater.bot.get_update(request.get_json(force=True))
    updater.dispatcher.process_update(update)
    return 'OK'

if __name__ == '__main__':
    # Set webhook
    updater.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print("✅ Webhook set and bot is running on Render...")
    
    # Run Flask app (Render looks for port from env var)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
