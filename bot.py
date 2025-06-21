# bot.py

from telegram.ext import Updater
from handlers import register_handlers
from config import TOKEN

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register all command and message handlers
    register_handlers(dp)

    # Start the Bot
    print("✅ Bot is running...")
    updater.start_polling()

    # Run the bot until you press Ctrl+C or the process receives SIGINT/SIGTERM
    updater.idle()

if __name__ == '__main__':
    main()