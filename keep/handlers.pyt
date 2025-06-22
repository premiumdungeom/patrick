# handlers.py

import random
import time
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)
from config import *
from utils import *
from datetime import datetime

# Global dictionary to track captcha and withdrawal states
captcha_store = {}
pending_withdrawals = {}
wallet_input_mode = set()
ptrst_withdraw_mode = {}
ton_withdraw_mode = {}

# Main menu reply buttons
def main_menu():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['new_task']} New Task", f"{EMOJIS['account']} Account"],
        [f"{EMOJIS['ptrst']} $PTRST", f"{EMOJIS['friends']} Friends"],
        [f"{EMOJIS['ton']} TON", f"{EMOJIS['about']} About"]
    ] + [[f"{EMOJIS['admin_panel']} Admin Panel"]] if True else [],
        resize_keyboard=True)

# /start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    if context.args:
        ref = context.args[0]
        create_user(user_id, username, ref)
    else:
        create_user(user_id, username)

    subs_message = (
        f"{EMOJIS['start']} **Subscribe to all resources:**\n\n"
        "1️⃣ [Patrick Official](https://t.me/minohamsterdailys)\n"
        "2️⃣ [Combo Hamster](https://t.me/gouglenetwork)\n"
        "3️⃣ [AI Isaac](https://t.me/AIIsaac_bot/sponsor)\n"
        "4️⃣ [AI Isaac BNB](https://t.me/aiisaac_bnb)\n\n"
        "Then click below 👇"
    )
    btn = InlineKeyboardButton("✅ I've Subscribed", callback_data="check_subscription")
    update.message.reply_text(subs_message, reply_markup=InlineKeyboardMarkup([[btn]]), parse_mode="Markdown")

# Subscription check and captcha
def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    chat_member = context.bot.get_chat_member("@gouglenetwork", user_id)

    if chat_member.status in ["member", "administrator", "creator"]:
        a, b = random.randint(1, 9), random.randint(1, 9)
        captcha_store[user_id] = a + b
        context.bot.send_message(user_id, f"❇️ Enter the captcha: {a} + {b}", reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True))
    else:
        msg = (
            "❌ You haven't joined all channels (@gouglenetwork)\n\n"
            f"{EMOJIS['start']} Subscribe to all resources:\n\n"
            "1️⃣ [Patrick Official](https://t.me/minohamsterdailys)\n"
            "2️⃣ [Combo Hamster](https://t.me/gouglenetwork)\n"
            "3️⃣ [AI Isaac](https://t.me/AIIsaac_bot/sponsor)\n"
            "4️⃣ [AI Isaac BNB](https://t.me/aiisaac_bnb)\n\n"
            "After subscribing, click below 👇"
        )
        btn = InlineKeyboardButton("✅ I've Subscribed", callback_data="check_subscription")
        context.bot.send_message(user_id, msg, reply_markup=InlineKeyboardMarkup([[btn]]), parse_mode="Markdown")

# Handle captcha input
def handle_captcha(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in captcha_store:
        try:
            if int(text) == captcha_store[user_id]:
                del captcha_store[user_id]
                context.bot.send_message(user_id,
                    "**👑 Participate in Airdrop 100,000,000 $PTRST**\n\n"
                    "🚧 Invite your friends and get:\n"
                    "- Level 1: 150 PTRST\n"
                    "- Level 2: 75 PTRST\n\n"
                    "🎁 Collect $PTRST every 30 minutes: +75\n"
                    "💎 Collect TON every 8 hours: +0.025 TON\n\n"
                    "🗓️ Listing $PTRST on May 20 at 16:00 (UTC+3)\n"
                    "🔥 Unallocated tokens will be burned!", parse_mode="Markdown"
                )
                context.bot.send_message(user_id,
                    "💎 [Click here](https://t.me/pengu_clash_bot?start=invite-fvhgw8) (Bonus 0.01 TON)\n"
                    "💲 [Click here](https://t.me/gouglenetwork) (Bonus 20 $PTRST)", parse_mode="Markdown"
                )
                context.bot.send_message(user_id,
                    "🎁 [9 FREE NFT GIFTS](https://x.com/somebitcoin/status/1923703977813622882)", parse_mode="Markdown")
                context.bot.send_message(user_id, "✅ You're in!", reply_markup=main_menu())
            else:
                a, b = random.randint(1, 9), random.randint(1, 9)
                captcha_store[user_id] = a + b
                update.message.reply_text(f"❌ Wrong captcha... Retry:\n❇️ Enter the captcha: {a} + {b}")
        except:
            update.message.reply_text("❌ Invalid input. Send the number.")

# 🆕 New Task
def new_task(update: Update, context: CallbackContext):
    task = open("new_task.txt").read()
    update.message.reply_text(task)

# 💰 Account
def account(update: Update, context: CallbackContext):
    user = update.effective_user
    data = get_user(user.id)
    txt = (
        f"✔️ Airdrop status: Eligible\n"
        f"🎩 User: {user.username}\n"
        f"🆔 ID: {user.id}\n"
        f"🚧 Invited:\n"
        f"1️⃣ LVL - {len(data['referrals_lvl1'])}\n"
        f"2️⃣ LVL - {len(data['referrals_lvl2'])}\n"
        f"👑 Balance $PTRST: {data['balance_ptrst']}\n"
        f"💎 Balance TON: {round(data['balance_ton'], 3)}\n"
        f"📝 Wallet Address: {data['wallet'] or 'Not set'}"
    )
    update.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup([
        ["📤 $PTRST", "📤 TON"],
        ["🏮SET_WALLET", "🚏BACK"]
    ], resize_keyboard=True))

# 👫 Friends
def friends(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🚧 Invite your friends and get $PTRST:\n"
        "1️⃣ Level - 150 $PTRST\n"
        "2️⃣ Level - 75 $PTRST\n\n"
        f"https://t.me/patricxst_bot?start={update.effective_user.id}"
    )

# 💘 Admin Panel
def admin_panel(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        return
    update.message.reply_text("💘 Admin Panel", reply_markup=ReplyKeyboardMarkup([
        [f"{EMOJIS['total_user']} Total User", f"{EMOJIS['total_payout']} Total Payout"],
        [f"{EMOJIS['broadcast']} Broadcast", f"{EMOJIS['set_new_task']} Set New Task"],
        ["🚏BACK"]
    ], resize_keyboard=True))

# 📤 Withdraw handlers
def withdraw_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text

    if user_id in ptrst_withdraw_mode:
        try:
            amount = int(txt)
            if amount < MIN_WITHDRAWAL_PTRST:
                update.message.reply_text(f"⚠️ Minimum amount is {MIN_WITHDRAWAL_PTRST} $PTRST")
                return
            user = get_user(user_id)
            if user["balance_ptrst"] < amount:
                update.message.reply_text("❌ Not enough balance")
                return
            deduct_balance(user_id, "ptrst", amount)
            update_total_payout("ptrst", amount)
            msg = f"💵 Withdraw Order Submitted\n━━━━━━━━━━━━━━━━━━━━\nAmount: {amount} $PTRST\nWallet: {user['wallet']}\nTime: {get_datetime()}"
            for admin in ADMINS:
                context.bot.send_message(admin, f"New $PTRST withdraw:\n{msg}")
            update.message.reply_text(f"{msg}\nWait for approval.")
            del ptrst_withdraw_mode[user_id]
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number")

    elif user_id in ton_withdraw_mode:
        try:
            amount = float(txt)
            if amount < MIN_WITHDRAWAL_TON:
                update.message.reply_text(f"⚠️ Minimum amount is {MIN_WITHDRAWAL_TON} TON")
                return
            user = get_user(user_id)
            if user["balance_ton"] < amount:
                update.message.reply_text("❌ Not enough balance")
                return
            deduct_balance(user_id, "ton", amount)
            update_total_payout("ton", amount)
            msg = f"💎 TON Withdraw Request\n━━━━━━━━━━━━━━━━━━━━\nAmount: {amount}\nWallet: {user['wallet']}\nTime: {get_datetime()}"
            for admin in ADMINS:
                context.bot.send_message(admin, f"New TON withdraw:\n{msg}")
            update.message.reply_text(f"{msg}\nWait for approval.")
            del ton_withdraw_mode[user_id]
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number")

# 📤 Trigger withdraw
def trigger_withdraw(update: Update, context: CallbackContext):
    txt = update.message.text
    user_id = update.effective_user.id
    if txt == "📤 $PTRST":
        ptrst_withdraw_mode[user_id] = True
        update.message.reply_text(f"Enter amount to withdraw in $PTRST (Min: {MIN_WITHDRAWAL_PTRST}):")
    elif txt == "📤 TON":
        ton_withdraw_mode[user_id] = True
        update.message.reply_text(f"Enter amount to withdraw in TON (Min: {MIN_WITHDRAWAL_TON}):")

# 📝 Wallet
def wallet_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text
    if txt == "🏮SET_WALLET":
        wallet_input_mode.add(user_id)
        update.message.reply_text("Please send your wallet address:")
    elif user_id in wallet_input_mode:
        update_wallet(user_id, txt)
        wallet_input_mode.remove(user_id)
        update.message.reply_text("✅ Wallet address updated!")

# 🎁 Claim PTRST
def claim_ptrst(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = get_user(user_id)
    left = check_cooldown(data, "ptrst")
    if left > 0:
        update.message.reply_text(f"⏳ Next bonus in {format_time(left)}")
        return
    reward = random.randint(100, 1000)
    update_balance(user_id, "ptrst", reward)
    update_claim_time(user_id, "ptrst")
    inviter = data.get("referrer")
    if inviter:
        bonus = int(reward * 0.25)
        update_balance(inviter, "ptrst", bonus)
    update.message.reply_text(f"👑 Successful! You got {reward} $PTRST")

# 💎 Claim TON
def claim_ton(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = get_user(user_id)
    left = check_cooldown(data, "ton")
    if left > 0:
        update.message.reply_text(f"⏳ Next bonus in {format_time(left)}")
        return
    reward = round(random.uniform(0.005, 0.025), 3)
    update_balance(user_id, "ton", reward)
    update_claim_time(user_id, "ton")
    inviter = data.get("referrer")
    if inviter:
        bonus = round(reward * 0.33, 3)
        update_balance(inviter, "ton", bonus)
    update.message.reply_text(f"⛏️ Successful! You got {reward} TON")

# 🚀 Total User
def total_user(update: Update, context: CallbackContext):
    users = load_users()
    total = len(users)
    update.message.reply_text(f"👥 Total users: {total}")

# 💱 Total Payout
def total_payout(update: Update, context: CallbackContext):
    payout = get_total_payouts()
    update.message.reply_text(f"💸 Total paid:\n$PTRST: {payout['ptrst']}\nTON: {payout['ton']}")

# 🍍 Set New Task
def set_new_task(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in ADMINS:
        context.bot.send_message(user_id, "Send me the new task text.")
        context.user_data["set_task"] = True

# Handle set task content
def handle_task_text(update: Update, context: CallbackContext):
    if context.user_data.get("set_task"):
        text = update.message.text
        open("new_task.txt", "w").write(text)
        open("task_history.txt", "a").write(f"[{get_datetime()}] {text}\n\n")
        update.message.reply_text("✅ Task updated.")
        context.user_data["set_task"] = False

# 👗 Broadcast
def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id in ADMINS:
        context.user_data["broadcast"] = True
        update.message.reply_text("Send the message (text/photo/video) to broadcast:")

# Handle broadcast
def handle_broadcast(update: Update, context: CallbackContext):
    if context.user_data.get("broadcast") and update.effective_user.id in ADMINS:
        users = load_users()
        count = 0
        for uid in users:
            try:
                update.message.copy(chat_id=int(uid))
                count += 1
                time.sleep(0.1)  # Avoid rate limiting
            except:
                continue
        update.message.reply_text(f"✅ Sent to {count} users.")
        context.user_data["broadcast"] = False

# Register handlers in bot.py
def register_handlers(dispatcher):
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_captcha))

    # Main menu button handlers
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🆕 New Task$'), new_task))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^💰 Account$'), account))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^👫 Friends$'), friends))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^💘 Admin Panel$'), admin_panel))

    # Account sub-menu handlers
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📤 \$PTRST$'), trigger_withdraw))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📤 TON$'), trigger_withdraw))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🏮SET_WALLET$'), wallet_handler))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🚏BACK$'), start))

    # Claim handlers
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^👑 Claim PTRST$'), claim_ptrst))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^⛏️ Claim TON$'), claim_ton))

    # Admin panel handlers
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🚀 Total User$'), total_user))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^💱 Total Payout$'), total_payout))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🍍 Set New Task$'), set_new_task))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^👗 Broadcast$'), broadcast))

    # Text input handlers (must come after specific handlers)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, withdraw_request))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, wallet_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_task_text))
    dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_broadcast))
