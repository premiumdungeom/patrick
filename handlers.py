import random
import time
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
)
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)
from config import *
from utils import *
from datetime import datetime

ADMINS = [5650788149, 8108410868]

captcha_store = {}
pending_withdrawals = {}  # withdrawal_id -> dict
pending_rejections = {}   # admin_id -> withdrawal_id
wallet_input_mode = set()
ptrst_withdraw_mode = {}
ton_withdraw_mode = {}
reminder_opt_in = set()

def main_menu():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['new_task']} New Task", f"{EMOJIS['account']} Account"],
        [f"{EMOJIS['ptrst']} $PTRST", f"{EMOJIS['friends']} Friends"],
        [f"{EMOJIS['ton']} TON", f"{EMOJIS['about']} About"],
        [f"🏆 Leaderboard", f"📜 Transaction History"],
        [f"🔔 Notifications"]
    ], resize_keyboard=True)

def admin_panel_keyboard():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['total_user']} Total User", f"{EMOJIS['total_payout']} Total Payout"],
        [f"{EMOJIS['broadcast']} Broadcast", f"{EMOJIS['set_new_task']} Set New Task"],
        [f"💸 Airdrop $PTRST"],
        ["🚏BACK"]
    ], resize_keyboard=True)

def is_verified(user_id):
    return get_user(user_id).get("verified", False)

def set_verified(user_id):
    u = get_user(user_id)
    u["verified"] = True
    save_user(user_id, u)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    if is_verified(user_id):
        show_main_menu(update, context)
        return

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

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        update.message.reply_text("❌ You are not an admin.")
        return
    update.message.reply_text("💘 Admin Panel", reply_markup=admin_panel_keyboard())

def show_main_menu(update: Update, context: CallbackContext, edit=False):
    update.message.reply_text("🏠 Main Menu", reply_markup=main_menu())

def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()  # Remove Telegram's loading spinner!
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

def handle_captcha(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Auto-pass/cancel captcha for admins
    if user_id in ADMINS:
        if user_id in captcha_store:
            del captcha_store[user_id]
        set_verified(user_id)
        show_main_menu(update, context)
        return

    if user_id in captcha_store:
        try:
            if int(text) == captcha_store[user_id]:
                del captcha_store[user_id]
                set_verified(user_id)
                context.bot.send_message(user_id,
                    "**👑 Participate in Airdrop 100,000,000 $PTRST**\n\n"
                    "🚧 Invite your friends and get:\n"
                    "- Level 1: 150 PTRST\n"
                    "- Level 2: 75 PTRST\n\n"
                    "🎁 Collect $PTRST every 30 minutes: +75\n"
                    "💎 Collect TON every 8 hours: +0.025 TON\n\n"
                    "🗓️ Listing $PTRST on May 20 at 16:00 (UTC+3)\n\n"
                    "🏆The more $PTRST you have, the more you will earn from the listing\n\n"
                    "🔥 Unallocated tokens will be burned!", parse_mode="Markdown"
                )
                context.bot.send_message(user_id,
                    "💎 [Click here](https://t.me/pengu_clash_bot?start=invite-fvhgw8) (Bonus 0.01 TON)\n"
                    "💲 [Click here](https://t.me/gouglenetwork) (Bonus 20 $PTRST)", parse_mode="Markdown"
                )
                context.bot.send_message(user_id,
                    "🎁 [9 FREE NFT GIFTS](https://x.com/Megabolly)", parse_mode="Markdown")
                show_main_menu(update, context)
            else:
                a, b = random.randint(1, 9), random.randint(1, 9)
                captcha_store[user_id] = a + b
                update.message.reply_text("❌ Wrong captcha... Retry:\n❇️ Enter the captcha: {} + {}".format(a, b))
        except:
            update.message.reply_text("❌ Invalid input. Send the number.")

def new_task(update: Update, context: CallbackContext):
    task = open("new_task.txt").read()
    update.message.reply_text(task)

def account(update: Update, context: CallbackContext):
    user = update.effective_user
    data = get_user(user.id)
    txt = (
        f"✔️ Airdrop status: Eligible\n\n"
        f"🎩 User: {user.username}\n\n"
        f"🆔 ID: {user.id}\n\n"
        f"🚧 Invited:\n"
        f"1️⃣ LVL - {len(data['referrals_lvl1'])}\n"
        f"2️⃣ LVL - {len(data['referrals_lvl2'])}\n\n"
        f"👑 Balance $PTRST: {data['balance_ptrst']}\n"
        f"💎 Balance TON: {round(data['balance_ton'], 3)}\n\n"
        f"📝 Wallet Address: {data['wallet'] or 'Not set'}"
    )
    update.message.reply_text(txt, reply_markup=ReplyKeyboardMarkup([
        ["📤 $PTRST", "📤 TON"],
        ["🏮SET_WALLET", "🚏BACK"]
    ], resize_keyboard=True))

def friends(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🚧 Invite your friends and get $PTRST:\n"
        "1️⃣ Level - 150 $PTRST\n"
        "2️⃣ Level - 75 $PTRST\n\n"
        f"https://t.me/ptrstr_bot?start={update.effective_user.id}"
    )

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
    add_tx(user_id, "Airdrop", reward, "You claimed bonus $PTRST")
    update.message.reply_text(f"👑 Successful! You got {reward} $PTRST")

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
    add_tx(user_id, "Airdrop", reward, "You claimed bonus TON")
    update.message.reply_text(f"⛏️ Successful! You got {reward} TON")

def leaderboard(update: Update, context: CallbackContext):
    users = load_users()
    scores = []
    for uid, data in users.items():
        if isinstance(data, dict):
            scores.append((uid, len(data.get("referrals_lvl1", [])), data.get("balance_ptrst", 0)))
    scores = sorted(scores, key=lambda x: (-x[1], -x[2]))[:10]
    msg = "🏆 Top Inviters Leaderboard:\n\n"
    for i, (uid, refs, bal) in enumerate(scores, 1):
        user = get_user(uid)
        uname = user.get("username") or str(uid)
        msg += f"{i}. @{uname} - {refs} invited - {bal} $PTRST\n"
    update.message.reply_text(msg)

def transaction_history(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txs = get_user(user_id).get("txs", [])
    if not txs:
        update.message.reply_text("No transactions yet.")
        return
    msg = "📜 Your Transaction History:\n\n"
    for tx in txs[-20:][::-1]:
        msg += f"{tx['date']} | {tx['type']}: {tx['amount']} | {tx['desc']}\n"
    update.message.reply_text(msg)

def notifications(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in reminder_opt_in:
        reminder_opt_in.remove(user_id)
        update.message.reply_text("🔕 Notifications turned OFF.")
    else:
        reminder_opt_in.add(user_id)
        update.message.reply_text("🔔 Notifications turned ON.")

def airdrop_ptrst_init(update: Update, context: CallbackContext):
    update.message.reply_text("Enter amount of $PTRST to airdrop to all users:")
    context.user_data["airdrop_ptrst"] = True

def airdrop_ptrst_execute(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return
    try:
        amount = int(update.message.text)
    except ValueError:
        update.message.reply_text("Please enter a valid integer amount.")
        return
    context.user_data["airdrop_amount"] = amount
    update.message.reply_text("Enter the message to send with the airdrop:")
    context.user_data["airdrop_ptrst"] = False
    context.user_data["airdrop_ptrst_msg"] = True

def airdrop_ptrst_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return
    message = update.message.text
    amount = context.user_data.get("airdrop_amount", 10)
    users = load_users()
    count = 0
    for uid, data in users.items():
        try:
            update_balance(uid, "ptrst", amount)
            add_tx(uid, "Airdrop", amount, message)
            context.bot.send_message(int(uid), f"🎉 {message}\nYou received {amount} $PTRST!")
            count += 1
        except Exception:
            continue
    update.message.reply_text(f"✅ Sent {amount} $PTRST to {count} users.")
    context.user_data["airdrop_ptrst_msg"] = False

def withdraw_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text
    token = None

    # Check which mode
    if user_id in ptrst_withdraw_mode:
        token = "PTRST"
        try:
            amount = int(txt)
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number for $PTRST amount.")
            return
        if amount < MIN_WITHDRAWAL_PTRST:
            update.message.reply_text(f"⚠️ Minimum amount is {MIN_WITHDRAWAL_PTRST} $PTRST")
            return
        user = get_user(user_id)
        if user["balance_ptrst"] < amount:
            update.message.reply_text("❌ Not enough balance")
            return
        deduct_balance(user_id, "ptrst", amount)
        # remove mode
        del ptrst_withdraw_mode[user_id]
    elif user_id in ton_withdraw_mode:
        token = "TON"
        try:
            amount = float(txt)
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number for TON amount.")
            return
        if amount < MIN_WITHDRAWAL_TON:
            update.message.reply_text(f"⚠️ Minimum amount is {MIN_WITHDRAWAL_TON} TON")
            return
        user = get_user(user_id)
        if user["balance_ton"] < amount:
            update.message.reply_text("❌ Not enough balance")
            return
        deduct_balance(user_id, "ton", amount)
        del ton_withdraw_mode[user_id]
    else:
        return

    withdrawal_id = f"{user_id}_{int(datetime.now().timestamp())}_{token}"
    user = get_user(user_id)
    pending_withdrawals[withdrawal_id] = {
        "user_id": user_id,
        "amount": amount,
        "wallet": user["wallet"],
        "token": token,
    }

    add_tx(user_id, "Withdraw", -amount, f"{token} Withdraw requested")

    withdraw_msg = (
        f"💵 Withdraw Order Submitted\n━━━━━━━━━━━━━━━━━━━━\n"
        f"User: @{user.get('username', user_id)}\n"
        f"Amount: {amount} {token}\nWallet: {user['wallet']}\nTime: {get_datetime()}\n"
        f"UserID: {user_id}\nWithdrawalID: {withdrawal_id}"
    )
    inline_keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"wd_accept_{withdrawal_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject_{withdrawal_id}")
        ]
    ]
    for admin in ADMINS:
        context.bot.send_message(admin, withdraw_msg, reply_markup=InlineKeyboardMarkup(inline_keyboard))
    update.message.reply_text(f"{withdraw_msg}\nWait for approval.")

def inline_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    admin_id = query.from_user.id

    if data == "check_subscription":
        check_subscription(update, context)
        return

    if data.startswith("wd_accept_"):
        withdrawal_id = data[len("wd_accept_"):]
        wd = pending_withdrawals.pop(withdrawal_id, None)
        if wd:
            user_id = wd["user_id"]
            amount = wd["amount"]
            token = wd["token"]
            context.bot.send_message(user_id, f"✅ Your withdrawal of {amount} {token} has been approved by admin.")
            query.edit_message_text(f"✅ Withdrawal accepted and user notified.")
        else:
            query.answer("Already processed or not found.", show_alert=True)
    elif data.startswith("wd_reject_"):
        withdrawal_id = data[len("wd_reject_"):]
        if withdrawal_id in pending_withdrawals:
            pending_rejections[admin_id] = withdrawal_id
            query.message.reply_text("Please type the reason for rejection:", reply_markup=ReplyKeyboardMarkup([["🚫 Cancel"]], resize_keyboard=True))
            query.edit_message_text("Please reply with the rejection reason!")
        else:
            query.answer("Already processed or not found.", show_alert=True)

def process_rejection_reason(update: Update, context: CallbackContext):
    admin_id = update.effective_user.id
    if admin_id in pending_rejections:
        reason = update.message.text
        withdrawal_id = pending_rejections.pop(admin_id)
        wd = pending_withdrawals.pop(withdrawal_id, None)
        if wd:
            user_id = wd["user_id"]
            amount = wd["amount"]
            token = wd["token"]
            # Refund
            if token == "PTRST":
                update_balance(user_id, "ptrst", amount)
            elif token == "TON":
                update_balance(user_id, "ton", amount)
            context.bot.send_message(user_id, f"❌ Your withdrawal was rejected.\nReason: {reason}\nBalance returned.")
            update.message.reply_text("User notified and balance restored.")
        else:
            update.message.reply_text("Withdrawal not found.")

def trigger_withdraw(update: Update, context: CallbackContext):
    txt = update.message.text
    user_id = update.effective_user.id
    if txt == "📤 $PTRST":
        ptrst_withdraw_mode[user_id] = True
        update.message.reply_text("Enter amount to withdraw in $PTRST:")
    elif txt == "📤 TON":
        ton_withdraw_mode[user_id] = True
        update.message.reply_text("Enter amount to withdraw in TON:")

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

def total_user(update: Update, context: CallbackContext):
    users = load_users()
    total = len(users)
    update.message.reply_text(f"👥 Total users: {total}")

def total_payout(update: Update, context: CallbackContext):
    payout = get_total_payouts()
    update.message.reply_text(f"💸 Total paid:\n$PTRST: {payout['ptrst']}\nTON: {payout['ton']}")

def set_new_task(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in ADMINS:
        context.bot.send_message(user_id, "Send me the new task text.")
        context.user_data["set_task"] = True

def handle_task_text(update: Update, context: CallbackContext):
    if context.user_data.get("set_task"):
        text = update.message.text
        open("new_task.txt", "w").write(text)
        open("task_history.txt", "a").write(f"[{get_datetime()}] {text}\n\n")
        update.message.reply_text("✅ Task updated.")
        context.user_data["set_task"] = False

def broadcast(update: Update, context: CallbackContext):
    context.user_data["broadcast"] = True
    update.message.reply_text("Send the message (text/photo/video) to broadcast:")

def handle_broadcast(update: Update, context: CallbackContext):
    if context.user_data.get("broadcast"):
        users = load_users()
        count = 0
        for uid in users:
            try:
                update.message.copy(chat_id=int(uid))
                count += 1
            except:
                continue
        update.message.reply_text(f"✅ Sent to {count} users.")
        context.user_data["broadcast"] = False

def main_menu_router(update: Update, context: CallbackContext):
    txt = update.message.text
    user_id = update.effective_user.id

    if txt == f"{EMOJIS['new_task']} New Task":
        return new_task(update, context)
    elif txt == f"{EMOJIS['account']} Account":
        return account(update, context)
    elif txt == f"{EMOJIS['ptrst']} $PTRST":
        return claim_ptrst(update, context)
    elif txt == f"{EMOJIS['friends']} Friends":
        return friends(update, context)
    elif txt == f"{EMOJIS['ton']} TON":
        return claim_ton(update, context)
    elif txt == f"{EMOJIS['about']} About":
        update.message.reply_text("About this bot: ...")
    elif txt == "🏆 Leaderboard":
        return leaderboard(update, context)
    elif txt == "📜 Transaction History":
        return transaction_history(update, context)
    elif txt == "🔔 Notifications":
        return notifications(update, context)
    elif txt == "📤 $PTRST" or txt == "📤 TON":
        return trigger_withdraw(update, context)
    elif txt == "🏮SET_WALLET":
        return wallet_handler(update, context)
    elif txt == "🚏BACK":
        show_main_menu(update, context)
        return
    elif txt == f"{EMOJIS['total_user']} Total User":
        return total_user(update, context)
    elif txt == f"{EMOJIS['total_payout']} Total Payout":
        return total_payout(update, context)
    elif txt == f"{EMOJIS['broadcast']} Broadcast":
        return broadcast(update, context)
    elif txt == f"{EMOJIS['set_new_task']} Set New Task":
        return set_new_task(update, context)
    elif txt == "💸 Airdrop $PTRST":
        return airdrop_ptrst_init(update, context)
    if user_id in ptrst_withdraw_mode or user_id in ton_withdraw_mode:
        return withdraw_request(update, context)
    if user_id in wallet_input_mode:
        return wallet_handler(update, context)
    if context.user_data.get("set_task"):
        return handle_task_text(update, context)
    if context.user_data.get("broadcast"):
        return handle_broadcast(update, context)
    if context.user_data.get("airdrop_ptrst"):
        return airdrop_ptrst_execute(update, context)
    if context.user_data.get("airdrop_ptrst_msg"):
        return airdrop_ptrst_message(update, context)
    if user_id in captcha_store:
        return handle_captcha(update, context)
    update.message.reply_text("❓ Unrecognized command. Please use the menu.")

def register_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CallbackQueryHandler(inline_callback_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, main_menu_router))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.user(user_id=ADMINS), process_rejection_reason))

def add_tx(user_id, tx_type, amount, desc):
    user = get_user(user_id)
    if "txs" not in user:
        user["txs"] = []
    user["txs"].append({"date": get_datetime(), "type": tx_type, "amount": amount, "desc": desc})
    save_user(user_id, user)