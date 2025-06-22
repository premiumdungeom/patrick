from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import ADMINS, CHANNEL_USERNAME, EMOJIS
from telegram import ParseMode
from utils import create_user, get_user, check_subscription, update_balance, update_total_payout, get_total_payouts

# Handler for /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    if not check_subscription(context.bot, user_id):  # ✅ PASS THE BOT!
        update.message.reply_text(
            "❌ You didn't join all our resources.\n\n"
            "⚠️ Subscribe to all resources:\n"
            "1️⃣ [Patrick Official](https://t.me/minohamsterdailys)\n"
            "2️⃣ [Combo Hamster](https://t.me/gouglenetwork)\n"
            "3️⃣ [AI Isaac](https://t.me/AIIsaac_bot/sponsor)\n"
            "4️⃣ [AI Isaac BNB](https://t.me/aiisaac_bnb)\n\n"
            "Then click /start again 👇",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    user_data = get_user(user_id)

    if not user_data:
        create_user(user_id, username)

    keyboard = [
        [KeyboardButton(EMOJIS["new_task"] + " New Task")],
        [KeyboardButton(EMOJIS["account"] + " Account")],
        [KeyboardButton(EMOJIS["ptrst"] + " $PTRST")],
        [KeyboardButton(EMOJIS["friends"] + " Friends")],
        [KeyboardButton(EMOJIS["bonus"] + " Bonus")],
        [KeyboardButton(EMOJIS["ton"] + " TON")],
        [KeyboardButton(EMOJIS["about"] + " About")],
        [KeyboardButton(EMOJIS["admin_panel"] + " Admin Panel")],
    ]

    update.message.reply_text(
        "Welcome! 👋 Please choose an option below:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Handler for buttons (TON, About, Admin Panel)
def handle_ton(update: Update, context: CallbackContext):
    update.message.reply_text("⛏️ TON mining is under development. Stay tuned!")

def handle_about(update: Update, context: CallbackContext):
    update.message.reply_text("🛠️ This bot allows you to earn $PTRST and TON through tasks, referrals, and bonuses.")

def handle_admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return update.message.reply_text("❌ You are not an admin.")
    
    keyboard = [
        [KeyboardButton(EMOJIS["pending_withdraw"] + " Pending Withdraw"), KeyboardButton(EMOJIS["total_user"] + " Total User")],
        [KeyboardButton(EMOJIS["total_payout"] + " Total Payout"), KeyboardButton(EMOJIS["broadcast"] + " Broadcast")],
        [KeyboardButton(EMOJIS["set_new_task"] + " Set New Task")]
    ]
    update.message.reply_text("💘 Admin Panel", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# Handler for /account
def account(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user(user_id)

    if not user_data:
        return update.message.reply_text("❌ User data not found. Please start again.")
    
    balance_ptrst = user_data["balance_ptrst"]
    balance_ton = user_data["balance_ton"]
    referrals_lvl1 = len(user_data["referrals_lvl1"])
    referrals_lvl2 = len(user_data["referrals_lvl2"])

    update.message.reply_text(
        f"💰 Your Account:\n\n"
        f"🔹 $PTRST Balance: {balance_ptrst}\n"
        f"🔹 TON Balance: {balance_ton} TON\n"
        f"🔹 Level 1 Referrals: {referrals_lvl1}\n"
        f"🔹 Level 2 Referrals: {referrals_lvl2}\n\n"
        "Use the menu below to interact with the bot."
    )

# Handle new tasks
def new_task(update: Update, context: CallbackContext):
    update.message.reply_text("📝 New task description coming soon.")

# Handle Bonus
def bonus(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user(user_id)

    if not user_data:
        return update.message.reply_text("❌ User data not found. Please start again.")

    # Simulate a bonus claim
    balance_ptrst = user_data["balance_ptrst"] + 100  # Just an example of adding 100 $PTRST
    update_balance(user_id, "ptrst", 100)

    update.message.reply_text(f"🎁 You claimed 100 $PTRST. Your new balance: {balance_ptrst} $PTRST.")

# Handle Friends
def friends(update: Update, context: CallbackContext):
    update.message.reply_text("👫 Share your referral link to earn rewards.")

# Handle commands for all buttons
def handle_unknown(update: Update, context: CallbackContext):
    update.message.reply_text("❓ I didn't understand that. Please use the menu.")

# Register all handlers
def register_handlers(dp):
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["new_task"]), new_task))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["account"]), account))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["ptrst"]), bonus))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["friends"]), friends))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["bonus"]), bonus))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["ton"]), handle_ton))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["about"]), handle_about))
    dp.add_handler(MessageHandler(Filters.text(EMOJIS["admin_panel"]), handle_admin_panel))
    dp.add_handler(MessageHandler(Filters.text, handle_unknown))
