from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Command handler for /start
def start(update: Update, context: CallbackContext):
    # Send the initial message with the buttons
    buttons = [
        ["💰 Account", "👫 Friends"],
        ["💞 Admin Panel", "👑 $PTRST"],
        ["⛏ TON", "🛠 About"],
        ["🆕 New Task"]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    update.message.reply_text("Welcome to the Bot! Select an option:", reply_markup=reply_markup)

# Check subscription handler
def check_subscription(update: Update, context: CallbackContext):
    # Logic to check if user is subscribed to channel
    user_id = update.message.from_user.id
    if is_user_subscribed(user_id):
        update.message.reply_text("✅ You're subscribed!")
    else:
        update.message.reply_text("🚫 You need to subscribe to the channel first!")

# Button Handlers for each button in the keyboard

def account_handler(update: Update, context: CallbackContext):
    # Logic for Account Button
    update.message.reply_text("📊 Here is your account info...")

def friends_handler(update: Update, context: CallbackContext):
    # Logic for Friends Button
    update.message.reply_text("👫 You have X referrals...")

def admin_panel_handler(update: Update, context: CallbackContext):
    # Logic for Admin Panel Button
    update.message.reply_text("💞 Accessing the Admin Panel...")

def ptrst_handler(update: Update, context: CallbackContext):
    # Logic for $PTRST Button
    update.message.reply_text("💰 Here are your $PTRST details...")

def ton_handler(update: Update, context: CallbackContext):
    # Logic for TON Button
    update.message.reply_text("⛏ Here's your TON balance...")

def about_handler(update: Update, context: CallbackContext):
    # Logic for About Button
    update.message.reply_text("🛠 About the bot...")

def new_task_handler(update: Update, context: CallbackContext):
    # Logic for New Task Button
    update.message.reply_text("🆕 New task details go here...")

# Register handlers
def register_handlers(dp):
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_subscription$"))

    # Add MessageHandlers for reply keyboard buttons
    dp.add_handler(MessageHandler(Filters.text("💰 Account"), account_handler))
    dp.add_handler(MessageHandler(Filters.text("👫 Friends"), friends_handler))
    dp.add_handler(MessageHandler(Filters.text("💞 Admin Panel"), admin_panel_handler))
    dp.add_handler(MessageHandler(Filters.text("👑 $PTRST"), ptrst_handler))
    dp.add_handler(MessageHandler(Filters.text("⛏ TON"), ton_handler))
    dp.add_handler(MessageHandler(Filters.text("🛠 About"), about_handler))
    dp.add_handler(MessageHandler(Filters.text("🆕 New Task"), new_task_handler))
