from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from config import ADMINS, CHANNEL_USERNAME, EMOJIS
from utils import *

# Reply Keyboard
main_menu = ReplyKeyboardMarkup([
    ["🧠 New Task", "👤 Account"],
    ["💰 $PTRST", "🪙 TON"],
    ["👥 Friends", "🎁 Bonus"],
    ["ℹ️ About", "💘 Admin Panel"]
], resize_keyboard=True)

# Start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or "NoUsername"
    args = context.args
    referrer_id = args[0] if args else None

    # Must Join Check
    chat_member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
    if chat_member.status not in ["member", "creator", "administrator"]:
        update.message.reply_text(
            f"🚨 You must join our channel first:\n👉 https://t.me/{CHANNEL_USERNAME[1:]}",
            disable_web_page_preview=True
        )
        return

    create_user(user_id, username, referrer_id)
    update.message.reply_text(
        f"👋 Welcome *{user.first_name}* to *Patricked Airdrop Bot*!\n\nUse the menu below to earn *$PTRST* and *TON*.",
        reply_markup=main_menu,
        parse_mode="Markdown"
    )

# Account handler
def account(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = get_user(user_id)
    wallet = data.get("wallet") or "Not set"

    msg = (
        f"👤 *Your Account*\n"
        f"🔹 Balance: {data['balance_ptrst']} $PTRST\n"
        f"🔸 TON: {data['balance_ton']} TON\n"
        f"👛 Wallet: `{wallet}`\n"
        f"👥 Referrals: {len(data['referrals_lvl1'])} (L1), {len(data['referrals_lvl2'])} (L2)"
    )
    update.message.reply_text(msg, parse_mode="Markdown")

# TON claim
def claim_ton(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    cooldown = check_cooldown(user_data, "ton")

    if cooldown > 0:
        return update.message.reply_text(f"⏳ Wait {format_time(cooldown)} before claiming TON again.")

    update_balance(user_id, "ton", 0.05)
    update_claim_time(user_id, "ton")
    update.message.reply_text("🪙 You claimed 0.05 TON!")

# PTRST claim
def claim_ptrst(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    cooldown = check_cooldown(user_data, "ptrst")

    if cooldown > 0:
        return update.message.reply_text(f"⏳ Wait {format_time(cooldown)} before claiming $PTRST again.")

    update_balance(user_id, "ptrst", 100)
    update_claim_time(user_id, "ptrst")
    update.message.reply_text("💰 You claimed 100 $PTRST!")

# Friends / referrals
def friends(update: Update, context: CallbackContext):
    user = update.effective_user
    data = get_user(user.id)
    invite_link = f"https://t.me/{context.bot.username}?start={user.id}"

    msg = (
        f"👥 *Your Referral Stats*\n"
        f"🔗 Invite Link: {invite_link}\n"
        f"👤 Level 1: {len(data['referrals_lvl1'])} (150 $PTRST each)\n"
        f"👥 Level 2: {len(data['referrals_lvl2'])} (75 $PTRST each)"
    )
    update.message.reply_text(msg, parse_mode="Markdown")

# Bonus (same as PTRST claim)
def bonus(update: Update, context: CallbackContext):
    return claim_ptrst(update, context)

# About
def about(update: Update, context: CallbackContext):
    update.message.reply_text(
        "ℹ️ *About Patricked Airdrop Bot*\n\n"
        "Earn *$PTRST* and *TON* by referring friends, completing tasks, and claiming daily bonuses."
        "\nWithdrawals processed manually by admin.",
        parse_mode="Markdown"
    )

# Admin Panel
def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if str(user_id) not in ADMINS:
        return update.message.reply_text("❌ You are not an admin.")

    payouts = get_total_payouts()
    users = load_users()
    update.message.reply_text(
        f"💘 *Admin Panel*\n\n"
        f"👥 Total Users: {len(users)}\n"
        f"💱 Total Payouts: {payouts['ptrst']} $PTRST, {payouts['ton']} TON",
        parse_mode="Markdown"
    )

# Set New Task (admin only)
def new_task(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if str(user_id) not in ADMINS:
        return update.message.reply_text("❌ You are not an admin.")

    update.message.reply_text("📝 Send the new task text now.")
    return

# Main text dispatcher

def register_handlers(dp):
    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(MessageHandler(Filters.regex("(?i)new task"), new_task))
    dp.add_handler(MessageHandler(Filters.regex("(?i)account"), account))
    dp.add_handler(MessageHandler(Filters.regex("(?i)ton"), claim_ton))
    dp.add_handler(MessageHandler(Filters.regex("(?i)\$ptrst"), claim_ptrst))
    dp.add_handler(MessageHandler(Filters.regex("(?i)friends"), friends))
    dp.add_handler(MessageHandler(Filters.regex("(?i)bonus"), bonus))
    dp.add_handler(MessageHandler(Filters.regex("(?i)about"), about))
    dp.add_handler(MessageHandler(Filters.regex("(?i)admin panel"), admin_panel))
