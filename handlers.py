import random
import time
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)
from config import *
from utils import *
from datetime import datetime, timedelta

captcha_store = {}
ptrst_withdraw_mode = {}
ton_withdraw_mode = {}
wallet_input_mode = set()
pending_withdrawals = {}
reminder_opt_in = set()
pending_support = {}
pending_quiz = {}
blind_box_timers = {}
pending_reject_reason = {}

LANGUAGES = {"en": "English", "es": "Español"}

def main_menu():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['new_task']} New Task", f"{EMOJIS['account']} Account", "📈 My Analytics"],
        [f"{EMOJIS['ptrst']} $PTRST", f"{EMOJIS['friends']} Friends", "🏆 Weekly Referral Contest"],
        [f"{EMOJIS['ton']} TON", f"{EMOJIS['about']} About", "🌳 My Referral Tree"],
        [f"🏆 Leaderboard", f"📜 Transaction History", "🎖️ Badges"],
        ["🔔 Notifications", "🎁 Blind Box", "🎂 Set Birthday", "🎂 Claim Birthday Reward"],
        ["🧠 Quiz", "🆘 Help", "❓ FAQ"],
        ["🌐 Language", "🚏BACK"]
    ], resize_keyboard=True)

def admin_panel_keyboard():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['total_user']} Total User", f"{EMOJIS['total_payout']} Total Payout"],
        [f"{EMOJIS['broadcast']} Broadcast", f"{EMOJIS['set_new_task']} Set New Task"],
        [f"💸 Airdrop $PTRST", "📊 Analytics"],
        ["🚏BACK"]
    ], resize_keyboard=True)

def is_verified(user_id):
    return get_user(user_id).get("verified", False)

def set_verified(user_id):
    u = get_user(user_id)
    u["verified"] = True
    save_user(user_id, u)

def notify_referrers(context, new_user_id, ref1_id=None, ref2_id=None):
    if ref1_id:
        try:
            context.bot.send_message(
                ref1_id,
                f"🎉 Someone has joined using your referral link! (Level 1)\nUser ID: {new_user_id}"
            )
        except Exception:
            pass
    if ref2_id:
        try:
            context.bot.send_message(
                ref2_id,
                f"🎉 Someone has joined using your Level 2 referral! (Level 2)\nUser ID: {new_user_id}"
            )
        except Exception:
            pass

def create_user_with_ref(context, user_id, username, ref=None):
    if not user_exists(user_id):
        if ref:
            ref1_id = int(ref)
            ref1_data = get_user(ref1_id)
            ref2_id = ref1_data.get("referrer") if ref1_data else None
            create_user(user_id, username, ref)
            notify_referrers(context, user_id, ref1_id=ref1_id, ref2_id=ref2_id)
        else:
            create_user(user_id, username)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    if is_verified(user_id):
        show_main_menu(update, context)
        return

    if context.args:
        ref = context.args[0]
        create_user_with_ref(context, user_id, username, ref)
    else:
        create_user_with_ref(context, user_id, username)

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
    query.answer()
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
    answer = update.message.text.strip()
    if not answer.isdigit():
        update.message.reply_text("❌ Please enter a number for captcha.")
        return
    if int(answer) == captcha_store[user_id]:
        set_verified(user_id)
        del captcha_store[user_id]
        update.message.reply_text("✅ Verified! Welcome!")
        show_main_menu(update, context)
    else:
        update.message.reply_text("❌ Wrong captcha. Try /start again.")

def onboarding(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome! Here’s how to use the bot:\n"
        "1. /start and subscribe to channels\n"
        "2. Set your wallet\n"
        "3. Claim airdrops & invite friends\n"
        "4. Withdraw to your wallet\n"
        "5. Use /help at any time!"
    )

def choose_language(update: Update, context: CallbackContext):
    kb = [[l] for l in LANGUAGES.values()]
    update.message.reply_text("Please choose your language / Por favor, elige tu idioma:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

def set_language(update: Update, context: CallbackContext):
    chosen = update.message.text
    for k, v in LANGUAGES.items():
        if v == chosen:
            set_lang(update.effective_user.id, k)
            update.message.reply_text(f"Language set to {v}.", reply_markup=main_menu())
            return
    update.message.reply_text("Unknown language.", reply_markup=main_menu())

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🆘 *Help*\n"
        "- Use the main menu to claim, invite, withdraw, and more.\n"
        "- Use /faq for answers to common questions.\n"
        "- Use /support to contact the admin.",
        parse_mode="Markdown"
    )

def faq_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "❓ *FAQ*\n"
        "Q: How do I claim rewards?\n"
        "A: Use the $PTRST or TON buttons in the main menu.\n\n"
        "Q: How do I set my wallet?\n"
        "A: Press 'SET_WALLET' in Account.\n\n"
        "Q: How do referrals work?\n"
        "A: Share your invite link. You get rewards for Level 1 and Level 2 invites.",
        parse_mode="Markdown"
    )

def support_command(update: Update, context: CallbackContext):
    update.message.reply_text("Please type your issue or question. The admin will reply as soon as possible.")
    pending_support[update.effective_user.id] = True

def handle_support(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if pending_support.get(user_id):
        for admin in ADMINS:
            context.bot.send_message(admin, f"📩 Support ticket from @{update.effective_user.username or user_id}:\n{update.message.text}")
        update.message.reply_text("Your message was sent to the admin. Thank you!")
        pending_support[user_id] = False

def new_task(update: Update, context: CallbackContext):
    try:
        task = open("new_task.txt").read()
        update.message.reply_text(task)
    except:
        update.message.reply_text("No new task set.")

def account(update: Update, context: CallbackContext):
    user = update.effective_user
    data = get_user(user.id)
    txt = (
        f"✔️ Airdrop status: Eligible\n"
        f"🎩 User: {user.username}\n"
        f"🆔 ID: {user.id}\n"
        f"🚧 Invited:\n"
        f"1️⃣ LVL - {len(data.get('referrals_lvl1',[]))}\n"
        f"2️⃣ LVL - {len(data.get('referrals_lvl2',[]))}\n"
        f"👑 Balance $PTRST: {data.get('balance_ptrst',0)}\n"
        f"💎 Balance TON: {round(data.get('balance_ton',0), 3)}\n"
        f"📝 Wallet Address: {data.get('wallet') or 'Not set'}"
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
        f"https://t.me/patricxst_bot?start={update.effective_user.id}"
    )

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

def grant_badge(user_id, badge):
    u = get_user(user_id)
    badges = u.get("badges", {})
    if badge in badges:
        badges[badge] += 1
    else:
        badges[badge] = 1
    u["badges"] = badges
    save_user(user_id, u)

def check_achievements(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    u = get_user(user_id)
    badges = u.get("badges", {})
    msg = "🎖️ Your achievement badges:\n"
    if not badges:
        msg += "No badges yet. Earn them by being active!"
    else:
        msg += "\n".join(f"- {b} ({n})" if n > 1 else f"- {b}" for b, n in badges.items())
    update.message.reply_text(msg)

def update_streak(user_id):
    u = get_user(user_id)
    today = datetime.utcnow().date()
    last = u.get("last_claim_date")
    streak = u.get("daily_streak", 0)
    if last:
        last_dt = datetime.strptime(last, "%Y-%m-%d").date()
        if (today - last_dt).days == 1:
            streak += 1
        elif (today - last_dt).days > 1:
            streak = 1
    else:
        streak = 1
    u["last_claim_date"] = today.strftime("%Y-%m-%d")
    u["daily_streak"] = streak
    save_user(user_id, u)
    return streak

def claim_ptrst(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = get_user(user_id)
    left = check_cooldown(data, "ptrst")
    if left > 0:
        update.message.reply_text(f"⏳ Next bonus in {format_time(left)}")
        return
    reward = random.randint(100, 1000)
    streak = update_streak(user_id)
    if streak >= 3:
        reward += 150
        grant_badge(user_id, f"Streak {streak} days")
    update_balance(user_id, "ptrst", reward)
    update_claim_time(user_id, "ptrst")
    inviter = data.get("referrer")
    if inviter:
        bonus = int(reward * 0.25)
        update_balance(inviter, "ptrst", bonus)
    add_tx(user_id, "Airdrop", reward, "You claimed bonus $PTRST")
    update.message.reply_text(f"👑 Successful! You got {reward} $PTRST\n🔥 Streak: {streak} day(s)")

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

def blind_box(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    now = time.time()
    cooldown = 21600
    last_time = blind_box_timers.get(user_id, 0)
    if now - last_time < cooldown:
        left = int(cooldown - (now - last_time))
        update.message.reply_text(f"⏳ You can open the Blind Box again in {format_time(left)}")
        return
    blind_box_timers[user_id] = now
    prize = random.choice([50, 100, 200, 0, "badge"])
    if prize == "badge":
        grant_badge(user_id, "Lucky Box Winner")
        update.message.reply_text("🎁 You got a special badge: Lucky Box Winner!")
    elif prize > 0:
        update_balance(user_id, "ptrst", prize)
        update.message.reply_text(f"🎁 You won {prize} $PTRST!")
    else:
        update.message.reply_text("🎁 Sorry, nothing this time. Try again later!")

def referral_tree(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    u = get_user(user_id)
    tree = []
    for uid in u.get("referrals_lvl1", []):
        user = get_user(uid)
        subtree = [f"  └ {s}" for s in user.get("referrals_lvl1", [])]
        tree.append(f"{uid} ({len(user.get('referrals_lvl1', []))}):\n" + "\n".join(subtree))
    if not tree:
        update.message.reply_text("No downline yet!")
    else:
        update.message.reply_text("Your referral tree:\n" + "\n".join(tree))

def set_birthday(update: Update, context: CallbackContext):
    update.message.reply_text("Send your birthday in YYYY-MM-DD format.")

def save_birthday(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        dt = datetime.strptime(text, "%Y-%m-%d")
        u = get_user(user_id)
        u["birthday"] = text
        save_user(user_id, u)
        update.message.reply_text("Birthday saved!")
    except:
        update.message.reply_text("Invalid format. Try again.")

def birthday_claim(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    u = get_user(user_id)
    today = datetime.utcnow().strftime("%m-%d")
    if u.get("birthday", "")[5:] == today and not u.get("birthday_claimed") == datetime.utcnow().strftime("%Y"):
        update_balance(user_id, "ptrst", 500)
        u["birthday_claimed"] = datetime.utcnow().strftime("%Y")
        save_user(user_id, u)
        update.message.reply_text("🎂 Happy birthday! You got 500 $PTRST!")
    else:
        update.message.reply_text("It's not your birthday, or you already claimed this year.")

def withdraw_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text
    token = None

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
            pending_reject_reason[update.effective_user.id] = withdrawal_id
            query.message.reply_text("Please type the reason for rejection. Or send 🚫 Cancel", reply_markup=ReplyKeyboardMarkup([["🚫 Cancel"]], resize_keyboard=True))
            query.edit_message_text("Waiting for rejection reason or cancel…")
        else:
            query.answer("Already processed or not found.", show_alert=True)

def process_rejection_reason(update: Update, context: CallbackContext):
    admin_id = update.effective_user.id
    withdrawal_id = pending_reject_reason.get(admin_id)
    if not withdrawal_id:
        return

    txt = update.message.text.strip()
    if txt == "🚫 Cancel":
        update.message.reply_text("❎ Rejection cancelled.", reply_markup=ReplyKeyboardRemove())
        pending_reject_reason.pop(admin_id, None)
        return

    wd = pending_withdrawals.pop(withdrawal_id, None)
    if wd:
        user_id = wd["user_id"]
        amount = wd["amount"]
        token = wd["token"]
        if token == "PTRST":
            update_balance(user_id, "ptrst", amount)
        elif token == "TON":
            update_balance(user_id, "ton", amount)
        context.bot.send_message(user_id, f"❌ Your withdrawal was rejected.\nReason: {txt}\nBalance returned.")
        update.message.reply_text("User notified and balance restored.", reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("Withdrawal not found.", reply_markup=ReplyKeyboardRemove())
    pending_reject_reason.pop(admin_id, None)

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

def analytics(update: Update, context: CallbackContext):
    users = load_users()
    total_users = len(users)
    now = datetime.utcnow()
    active_7d = 0
    total_referrals = 0
    total_withdraw_ptrst = 0
    total_withdraw_ton = 0
    top_ptrst = []
    top_invites = []
    for uid, data in users.items():
        if isinstance(data, dict):
            last_tx = data.get("txs", [])
            if last_tx and "date" in last_tx[-1]:
                try:
                    tx_dt = datetime.strptime(last_tx[-1]["date"], "%Y-%m-%d %H:%M:%S")
                    if (now - tx_dt).days < 7:
                        active_7d += 1
                except:
                    pass
            total_referrals += len(data.get('referrals_lvl1', []))
            bal_ptrst = data.get("balance_ptrst", 0)
            bal_ton = data.get("balance_ton", 0)
            for tx in data.get("txs", []):
                if tx["type"] == "Withdraw":
                    if "PTRST" in tx["desc"]:
                        total_withdraw_ptrst += abs(tx["amount"])
                    elif "TON" in tx["desc"]:
                        total_withdraw_ton += abs(tx["amount"])
            top_ptrst.append((uid, bal_ptrst))
            top_invites.append((uid, len(data.get('referrals_lvl1', []))))
    top_ptrst = sorted(top_ptrst, key=lambda x: -x[1])[:3]
    top_invites = sorted(top_invites, key=lambda x: -x[1])[:3]
    msg = (
        f"📊 <b>Analytics</b>\n"
        f"Total Users: {total_users}\n"
        f"Active (last 7d): {active_7d}\n"
        f"Total Referrals: {total_referrals}\n"
        f"Total $PTRST Withdrawn: {total_withdraw_ptrst}\n"
        f"Total TON Withdrawn: {total_withdraw_ton}\n\n"
        f"🏅 <b>Top 3 $PTRST Holders:</b>\n"
    )
    for i, (uid, bal) in enumerate(top_ptrst, 1):
        user = get_user(uid)
        uname = user.get("username") or uid
        msg += f"{i}. @{uname} - {bal} $PTRST\n"
    msg += "\n🏅 <b>Top 3 Inviters:</b>\n"
    for i, (uid, refs) in enumerate(top_invites, 1):
        user = get_user(uid)
        uname = user.get("username") or uid
        msg += f"{i}. @{uname} - {refs} invited\n"
    update.message.reply_text(msg, parse_mode="HTML")

def referral_contest_leaderboard(update: Update, context: CallbackContext):
    users = load_users()
    week = datetime.utcnow().isocalendar()[1]
    scores = []
    for uid, data in users.items():
        if isinstance(data, dict):
            week_refs = [r for r in data.get("referral_timestamps", []) if datetime.strptime(r["date"], "%Y-%m-%d").isocalendar()[1] == week]
            scores.append((uid, len(week_refs)))
    scores = sorted(scores, key=lambda x: -x[1])[:10]
    msg = "🏆 Weekly Referral Contest Leaderboard:\n"
    for i, (uid, refs) in enumerate(scores, 1):
        user = get_user(uid)
        uname = user.get("username") or str(uid)
        msg += f"{i}. @{uname} - {refs} new this week\n"
    update.message.reply_text(msg)

QUIZ_QUESTIONS = [
    {"q": "What is the symbol for TON?", "a": ["ton"]},
    {"q": "How many levels of referral rewards are there?", "a": ["2", "two"]},
]

def quiz_command(update: Update, context: CallbackContext):
    q = random.choice(QUIZ_QUESTIONS)
    pending_quiz[update.effective_user.id] = q
    update.message.reply_text(f"Quiz time!\n{q['q']}")

def handle_quiz_answer(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in pending_quiz:
        return
    answer = update.message.text.strip().lower()
    q = pending_quiz[user_id]
    if answer in q["a"]:
        update_balance(user_id, "ptrst", 100)
        update.message.reply_text("Correct! You win 100 $PTRST.")
        del pending_quiz[user_id]
    else:
        update.message.reply_text("Incorrect. Try again!")

def user_analytics(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    data = get_user(user_id)
    msg = (
        f"📈 *Your Analytics*\n"
        f"Total $PTRST earned: {sum([tx['amount'] for tx in data.get('txs', []) if tx['type']=='Airdrop'])}\n"
        f"Referrals level 1: {len(data.get('referrals_lvl1', []))}\n"
        f"Referrals level 2: {len(data.get('referrals_lvl2', []))}\n"
        f"Daily streak: {data.get('daily_streak', 0)}\n"
        f"Badges: {', '.join([f'{b} ({n})' if n > 1 else b for b, n in data.get('badges', {}).items()]) if data.get('badges', {}) else 'None'}"
    )
    update.message.reply_text(msg, parse_mode="Markdown")

def main_menu_router(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text.strip()

    if user_id in pending_reject_reason:
        return process_rejection_reason(update, context)
    if user_id in captcha_store:
        return handle_captcha(update, context)
    if txt in LANGUAGES.values():
        return set_language(update, context)
    if user_id in pending_support and pending_support[user_id]:
        return handle_support(update, context)
    if user_id in pending_quiz:
        return handle_quiz_answer(update, context)
    if getattr(context.user_data, "setting_birthday", False):
        context.user_data["setting_birthday"] = False
        return save_birthday(update, context)
    if context.user_data.get("set_task"):
        return handle_task_text(update, context)
    if context.user_data.get("broadcast"):
        return handle_broadcast(update, context)
    if user_id in ptrst_withdraw_mode or user_id in ton_withdraw_mode:
        return withdraw_request(update, context)
    if user_id in wallet_input_mode:
        return wallet_handler(update, context)

    # Menu entries
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
    elif txt == "🌐 Language":
        return choose_language(update, context)
    elif txt == "🆘 Help":
        return help_command(update, context)
    elif txt == "❓ FAQ":
        return faq_command(update, context)
    elif txt == "🎖️ Badges":
        return check_achievements(update, context)
    elif txt == "📈 My Analytics":
        return user_analytics(update, context)
    elif txt == "🌳 My Referral Tree":
        return referral_tree(update, context)
    elif txt == "🎁 Blind Box":
        return blind_box(update, context)
    elif txt == "🎂 Set Birthday":
        context.user_data["setting_birthday"] = True
        return set_birthday(update, context)
    elif txt == "🎂 Claim Birthday Reward":
        return birthday_claim(update, context)
    elif txt == "🏆 Weekly Referral Contest":
        return referral_contest_leaderboard(update, context)
    elif txt == "🧠 Quiz":
        return quiz_command(update, context)
    elif txt == "/onboarding":
        return onboarding(update, context)
    elif txt == "/support":
        return support_command(update, context)
    elif txt == f"{EMOJIS['total_user']} Total User":
        return total_user(update, context)
    elif txt == f"{EMOJIS['total_payout']} Total Payout":
        return total_payout(update, context)
    elif txt == f"{EMOJIS['broadcast']} Broadcast":
        return broadcast(update, context)
    elif txt == f"{EMOJIS['set_new_task']} Set New Task":
        return set_new_task(update, context)
    elif txt == "💸 Airdrop $PTRST":
        update.message.reply_text("Airdrop coming soon!")
        return
    elif txt == "📊 Analytics":
        return analytics(update, context)
    elif txt == "/admin":
        return admin(update, context)
    elif txt == "/start":
        return start(update, context)
    else:
        update.message.reply_text("❓ Unrecognized command. Use the menu or /help.")

def register_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("faq", faq_command))
    dispatcher.add_handler(CommandHandler("onboarding", onboarding))
    dispatcher.add_handler(CommandHandler("support", support_command))
    dispatcher.add_handler(CommandHandler("quiz", quiz_command))
    dispatcher.add_handler(CallbackQueryHandler(inline_callback_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, main_menu_router))

def add_tx(user_id, tx_type, amount, desc):
    user = get_user(user_id)
    if "txs" not in user:
        user["txs"] = []
    user["txs"].append({"date": get_datetime(), "type": tx_type, "amount": amount, "desc": desc})
    save_user(user_id, user)