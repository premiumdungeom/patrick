import random
import time
import threading
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)
from config import *
from utils import *
from datetime import datetime, timedelta
from utils import user_exists, load_users

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
captcha_store = {}
ptrst_withdraw_mode = {}
ton_withdraw_mode = {}
wallet_input_mode = set()
pending_withdrawals = {}
reminder_opt_in = set()
pending_support = {}
pending_quiz = {}
withdraw_cooldowns = {}
WITHDRAWAL_START_DATE = datetime(2025, 8, 1)
blind_box_timers = {}
pending_reject_reason = {}
airdrop_ptrst_state = {}
give_ton_state = {}

weekly_contest_leaderboard = []
weekly_contest_last_update = 0
weekly_contest_week = None
weekly_prize_usd = 40000
weekly_prize_ton = 0  # This should be set according to TON price or by admin

LANGUAGES = {"en": "English", "es": "Español"}
def main_menu(user_id=None):
    kb = [
        [f"{EMOJIS['new_task']} New Task", f"{EMOJIS['account']} Account", "📈 My Analytics"],
        [f"{EMOJIS['ptrst']} $PTRST", f"{EMOJIS['friends']} Friends", f"{EMOJIS['ton']} TON"],
        [f"{EMOJIS['about']} About"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_panel_keyboard():
    return ReplyKeyboardMarkup([
        [f"{EMOJIS['total_user']} Total User", f"{EMOJIS['total_payout']} Total Payout"],
        [f"{EMOJIS['broadcast']} Broadcast", f"{EMOJIS['set_new_task']} Set New Task"],
        ["💸 Airdrop $PTRST", "💵Give TON", "📊 Analytics"],
        ["🚏BACK"]
    ], resize_keyboard=True)

def analytics_menu():
    kb = [
        ["📜 Transaction History", "🏆 Leaderboard"],
        ["🎁 Blind Box", "🎖️ Badges"],
        ["🔔 Notifications", "🌳 My Referral Tree"],
        ["🔥 Final Invite Rush"],
        ["🚏BACK"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

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
        except Exception as e:
            logger.error(f"Error notifying referrer 1: {e}")
    if ref2_id:
        try:
            context.bot.send_message(
                ref2_id,
                f"🎉 Someone has joined using your Level 2 referral! (Level 2)\nUser ID: {new_user_id}"
            )
        except Exception as e:
            logger.error(f"Error notifying referrer 2: {e}")

def create_user_with_ref(context, user_id, username, ref=None):
    if not user_exists(user_id):
        if ref:
            try:
                ref1_id = int(ref)
                ref1_data = get_user(ref1_id)
                ref2_id = ref1_data.get("referrer") if ref1_data else None
                create_user(user_id, username, ref)
                notify_referrers(context, user_id, ref1_id=ref1_id, ref2_id=ref2_id)
            except ValueError:
                logger.error(f"Invalid referral ID: {ref}")
                create_user(user_id, username)
        else:
            create_user(user_id, username)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    logger.info(f"Start command received from {user_id} ({username})")

    if is_verified(user_id):
        show_main_menu(update, context)
        return

    # Handle referral if present
    if context.args and len(context.args) > 0:
        ref = context.args[0]
        logger.info(f"User came from referral: {ref}")
        create_user_with_ref(context, user_id, username, ref)
    else:
        create_user_with_ref(context, user_id, username)

    # Subscription message with inline button
    subs_message = (
        f"{EMOJIS['start']} **Subscribe to all resources:**\n\n"
        "1️⃣ [Patrick Official](https://t.me/ptrst_official)\n"
        "2️⃣ [Patrick Association](https://t.me/patrickstarsfarm)\n"
        "3️⃣ [Detective](https://t.me/AirdropDetective)\n"
        "4️⃣ [Promotion](https://t.me/airdropinspector)\n\n"
        "Then click below 👇"
    )
    btn = InlineKeyboardButton("✅ I've Subscribed", callback_data="check_subscription")
    update.message.reply_text(
        subs_message, 
        reply_markup=InlineKeyboardMarkup([[btn]]), 
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

def check_subscription(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    
    try:
        # Check if user is member of required channel
        chat_member = context.bot.get_chat_member("@gouglenetwork", user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            a, b = random.randint(1, 9), random.randint(1, 9)
            captcha_store[user_id] = a + b
            context.bot.send_message(
                user_id, 
                f"❇️ Enter the captcha: {a} + {b}", 
                reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
            )
        else:
            msg = (
                "❌ You haven't joined all channels (@gouglenetwork)\n\n"
                f"{EMOJIS['start']} Subscribe to all resources:\n\n"
                "1️⃣ [Patrick Official](https://t.me/ptrst_official)\n"
                "2️⃣ [Patrick Association](https://t.me/patrickstarsfarm)\n"
                "3️⃣ [Detective](https://t.me/AirdropDetective)\n"
                "4️⃣ [Promotion](https://t.me/airdropinspector)\n\n"
                "Then click below 👇"
                "After subscribing, click below 👇"
            )
            btn = InlineKeyboardButton("✅ I've Subscribed", callback_data="check_subscription")
            query.edit_message_text(
                msg, 
                reply_markup=InlineKeyboardMarkup([[btn]]), 
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error in check_subscription: {e}")
        query.edit_message_text("An error occurred. Please try again.")

def handle_captcha(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    answer = update.message.text.strip()
    
    if user_id not in captcha_store:
        update.message.reply_text("Please start over with /start")
        return
        
    if not answer.isdigit():
        update.message.reply_text("❌ Please enter a number for captcha.")
        return
        
    if int(answer) == captcha_store[user_id]:
        set_verified(user_id)
        del captcha_store[user_id]
        update.message.reply_text(
            "👑 Participate in Airdrop 100,000,000 $PTRST\n\n"
            "🚧 Invite your friends and get:\n"
            "For level 1 - 150 $PTRST\n"
            "For level 2 - 75 $PTRST\n\n"
            "👑 Collect the bonus $PTRST every 30 minutes and get 1000 $PTRST.\n"
            "Every time your friend picks up the bonus you will get 25% of the amount\n\n"
            "💎 Collect TON bonus every 8 hours and get up to 0.070 TON.\n"
            "Every time your friend picks up the bonus you will get 25% of the amount\n\n"
            "🚩 Distribution Date | AUGUST 1ST at 12:00 (UTC+4)\n\n"
            "🗓️ Listing $PTRST on AUGUST 15TH at 15:00 (UTC+3)\n\n"
            "🏆 The more $PTRST you have, the more you will earn from the listing\n\n"
            "🔥 All unallocated $PTRST will be burned, which will add to the price of $PTRST"
      )
        show_main_menu(update, context)
    else:
        update.message.reply_text("❌ Wrong captcha. Try /start again.")

def show_main_menu(update: Update, context: CallbackContext, edit=False):
    if hasattr(update, 'message'):
        update.message.reply_text(
            "😘 Follow and drop your telegram user ID in the comment session to Receive 200 $PTRST\n\n"
            "https://x.com/Megabolly/status/1940331835277574594\n\n"
           " Follow check will be detected 👑",
            reply_markup=main_menu(update.effective_user.id))
    elif hasattr(update, 'callback_query'):
        context.bot.send_message(
            update.callback_query.from_user.id,
            "💎 [Click here](https://t.me/pengu_clash_bot?start=invite-fvhgw8) (Bonus 0.027 TON)",
            reply_markup=main_menu(update.callback_query.from_user.id)
        )

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        update.message.reply_text("❌ You are not an admin.")
        return
    update.message.reply_text("💘 Admin Panel", reply_markup=admin_panel_keyboard())

def onboarding(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome! Here's how to use the bot:\n"
        "1. /start and subscribe to channels\n"
        "2. Set your wallet\n"
        "3. Claim airdrops & invite friends\n"
        "4. Withdraw to your wallet\n"
        "5. Use /help at any time!"
    )

def choose_language(update: Update, context: CallbackContext):
    kb = [[l] for l in LANGUAGES.values()]
    update.message.reply_text(
        "Please choose your language / Por favor, elige tu idioma:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

def set_language(update: Update, context: CallbackContext):
    chosen = update.message.text
    for k, v in LANGUAGES.items():
        if v == chosen:
            set_lang(update.effective_user.id, k)
            update.message.reply_text(
                f"Language set to {v}.",
                reply_markup=main_menu(update.effective_user.id)
            )
            return
    update.message.reply_text("Unknown language.", reply_markup=main_menu(update.effective_user.id))
def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🆘 *Help*\n"
        "- Use the main menu to claim, invite, withdraw, /onboarding and more.\n"
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
            context.bot.send_message(
                admin,
                f"📩 Support ticket from @{update.effective_user.username or user_id}:\n{update.message.text}"
            )
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
    update.message.reply_text(
        txt,
        reply_markup=ReplyKeyboardMarkup([
            ["📤 $PTRST", "📤 TON"],
            ["🏮SET_WALLET", "🚏BACK"]
        ], resize_keyboard=True)
    )

def friends(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🚧 Invite your friends and get $PTRST:\n"
        "1️⃣ Level - 150 $PTRST\n"
        "2️⃣ Level - 75 $PTRST\n\n"
        f"https://t.me/ptrstr_bot?start={update.effective_user.id}"
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
    context.user_data["setting_birthday"] = True

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
    context.user_data["setting_birthday"] = False

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

    if datetime.now() < WITHDRAWAL_START_DATE:
        countdown = get_withdrawal_countdown()
        update.message.reply_text(
            f"⏳ Withdrawals will open on August 1st, 2025!\n"
            f"Time remaining: {countdown}\n\n"
            "You can still earn and accumulate $PTRST and TON until then!",
            reply_markup=ReplyKeyboardMarkup([
                ["📤 $PTRST", "📤 TON"],
                ["🏮SET_WALLET", "🚏BACK"]
            ], resize_keyboard=True)
        )
        return

    if user_id in ptrst_withdraw_mode:
        token = "PTRST"
        try:
            amount = int(txt)
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number for $PTRST amount.")
            return
        
        # Check minimum amount first
        if amount < MIN_WITHDRAWAL_PTRST:
            ptrst_withdraw_mode.pop(user_id, None)  # Clear withdrawal mode
            update.message.reply_text(
                f"⚠️ Minimum amount is {MIN_WITHDRAWAL_PTRST} $PTRST\n"
                "Returning to account menu...",
                reply_markup=ReplyKeyboardMarkup([
                    ["📤 $PTRST", "📤 TON"],
                    ["🏮SET_WALLET", "🚏BACK"]
                ], resize_keyboard=True)
            )
            return
            
        # Then check balance
        user = get_user(user_id)
        if user["balance_ptrst"] < amount:
            ptrst_withdraw_mode.pop(user_id, None)  # Clear withdrawal mode
            update.message.reply_text(
                "❌ Not enough balance\n"
                "Returning to account menu...",
                reply_markup=ReplyKeyboardMarkup([
                    ["📤 $PTRST", "📤 TON"],
                    ["🏮SET_WALLET", "🚏BACK"]
                ], resize_keyboard=True)
            )
            return
            
        # If all checks pass, proceed with withdrawal
        deduct_balance(user_id, "ptrst", amount)
        del ptrst_withdraw_mode[user_id]
        
    elif user_id in ton_withdraw_mode:
        token = "TON"
        try:
            amount = float(txt)
        except ValueError:
            update.message.reply_text("❌ Please enter a valid number for TON amount.")
            return
            
        # Check minimum amount first
        if amount < MIN_WITHDRAWAL_TON:
            ton_withdraw_mode.pop(user_id, None)  # Clear withdrawal mode
            update.message.reply_text(
                f"⚠️ Minimum amount is {MIN_WITHDRAWAL_TON} TON\n"
                "Returning to account menu...",
                reply_markup=ReplyKeyboardMarkup([
                    ["📤 $PTRST", "📤 TON"],
                    ["🏮SET_WALLET", "🚏BACK"]
                ], resize_keyboard=True)
            )
            return
            
        # Then check balance
        user = get_user(user_id)
        if user["balance_ton"] < amount:
            ton_withdraw_mode.pop(user_id, None)  # Clear withdrawal mode
            update.message.reply_text(
                "❌ Not enough balance\n"
                "Returning to account menu...",
                reply_markup=ReplyKeyboardMarkup([
                    ["📤 $PTRST", "📤 TON"],
                    ["🏮SET_WALLET", "🚏BACK"]
                ], resize_keyboard=True)
            )
            return
            
        # If all checks pass, proceed with withdrawal
        deduct_balance(user_id, "ton", amount)
        del ton_withdraw_mode[user_id]
    else:
        return

    # Process successful withdrawal request
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

def check_withdrawal_start(context: CallbackContext):
    if datetime.now() >= WITHDRAWAL_START_DATE:
        users = load_users()
        for user_id in users:
            try:
                context.bot.send_message(
                    user_id,
                    "🎉 Withdrawals are now open! You can now withdraw your $PTRST and TON tokens!"
                )
            except Exception as e:
                logger.error(f"Error notifying user {user_id}: {e}")

def schedule_withdrawal_check(dispatcher):
    if not hasattr(dispatcher, 'job_queue') or dispatcher.job_queue is None:
        logger.warning("Job queue not available - running in webhook mode?")
        return
        
    # Only schedule if we have a job queue
    dispatcher.job_queue.run_repeating(
        check_withdrawal_start,
        interval=3600,
        first=0
    )

def return_to_account(context: CallbackContext):
    user_id = context.job.context
    context.bot.send_message(
        user_id,
        "Returning to account menu...",
        reply_markup=ReplyKeyboardMarkup([
            ["📤 $PTRST", "📤 TON"],
            ["🏮SET_WALLET", "🚏BACK"]
        ], resize_keyboard=True)
    )

def trigger_withdraw(update: Update, context: CallbackContext):
    txt = update.message.text
    user_id = update.effective_user.id
    
    # Check if withdrawals are open
    countdown = get_withdrawal_countdown()
    if countdown:
        update.message.reply_text(
            f"⏳ Withdrawals will open on August 1st, 2025!\n"
            f"Time remaining: {countdown}\n\n"
            "You can still earn and accumulate $PTRST and TON until then!",
            reply_markup=ReplyKeyboardMarkup([
                ["📤 $PTRST", "📤 TON"],
                ["🏮SET_WALLET", "🚏BACK"]
            ], resize_keyboard=True)
        )
        return
    
    # Rest of your existing withdraw trigger code...
    if user_id in withdraw_cooldowns and time.time() - withdraw_cooldowns[user_id] < 5:
        update.message.reply_text("⏳ Please wait a moment before trying again.")
        return
    
    # Remove from both if switching
    ptrst_withdraw_mode.pop(user_id, None)
    ton_withdraw_mode.pop(user_id, None)

    if txt == "📤 $PTRST":
        ptrst_withdraw_mode[user_id] = True
        update.message.reply_text("Enter amount to withdraw in $PTRST:", reply_markup=ReplyKeyboardRemove())
    elif txt == "📤 TON":
        ton_withdraw_mode[user_id] = True
        update.message.reply_text("Enter amount to withdraw in TON:", reply_markup=ReplyKeyboardRemove())

def handle_withdraw_amount(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text
    
    if user_id in ptrst_withdraw_mode or user_id in ton_withdraw_mode:
        return withdraw_request(update, context)
    return None

def process_rejection_reason(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text.strip()
    
    if txt == "🚫 Cancel":
        del pending_reject_reason[user_id]
        update.message.reply_text("Rejection cancelled.", reply_markup=admin_panel_keyboard())
        return
    
    withdrawal_id = pending_reject_reason[user_id]
    wd = pending_withdrawals.pop(withdrawal_id, None)
    
    if wd:
        target_user_id = wd["user_id"]
        amount = wd["amount"]
        token = wd["token"]
        
        # Return funds to user's balance
        if token == "PTRST":
            update_balance(target_user_id, "ptrst", amount)
        elif token == "TON":
            update_balance(target_user_id, "ton", amount)
        
        # Notify user
        context.bot.send_message(
            target_user_id,
            f"❌ Your withdrawal of {amount} {token} was rejected by admin.\nReason: {txt}"
        )
        
        # Add transaction record
        add_tx(target_user_id, "Withdraw Rejected", amount, f"{token} Withdraw rejected: {txt}")
        
        update.message.reply_text(
            f"❌ Withdrawal rejected and user notified with your reason.",
            reply_markup=admin_panel_keyboard()
        )
    else:
        update.message.reply_text("Withdrawal already processed or not found.", reply_markup=admin_panel_keyboard())
    
    del pending_reject_reason[user_id]

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
    user_id = update.effective_user.id
    if user_id in ADMINS:
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

def get_weekly_prizes():
    prizes = {}
    for i in range(1, 11):
        prizes[i] = [500, 350, 250, 200, 150, 100, 90, 80, 70, 60][i-1]
    for i in range(11, 51):
        prizes[i] = 40
    for i in range(51, 101):
        prizes[i] = 20
    for i in range(101, 251):
        prizes[i] = 10
    return prizes

def update_weekly_leaderboard(force=False):
    global weekly_contest_leaderboard, weekly_contest_last_update, weekly_contest_week
    now = int(time.time())
    week = datetime.utcnow().isocalendar()[1]
    if not force and now - weekly_contest_last_update < 600 and weekly_contest_week == week:
        return
    weekly_contest_last_update = now
    weekly_contest_week = week
    users = load_users()
    scores = []
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_start_ts = int(time.mktime(week_start.replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
    for uid, data in users.items():
        if isinstance(data, dict):
            refs_this_week = [
                r for r in data.get("referral_timestamps", [])
                if "date" in r and int(datetime.strptime(r["date"], "%Y-%m-%d").timestamp()) >= week_start_ts
            ]
            scores.append((uid, len(refs_this_week)))
    scores = sorted(scores, key=lambda x: -x[1])[:250]
    weekly_contest_leaderboard = scores

def get_withdrawal_countdown():
    now = datetime.now()
    if now >= WITHDRAWAL_START_DATE:
        return None  # Countdown expired
    
    delta = WITHDRAWAL_START_DATE - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} days {hours} hours {minutes} mins {seconds} secs"

def payout_weekly_contest(context=None):
    update_weekly_leaderboard(force=True)
    prizes = get_weekly_prizes()
    users = load_users()
    ton_per_usd = weekly_prize_ton / weekly_prize_usd if weekly_prize_usd > 0 and weekly_prize_ton > 0 else 1
    winners_info = []
    for rank, (uid, refs) in enumerate(weekly_contest_leaderboard, 1):
        user = get_user(uid)
        prize_usd = prizes.get(rank, 0)
        if prize_usd > 0:
            prize_ton = round(prize_usd * ton_per_usd, 3)
            update_balance(uid, "ton", prize_ton)
            add_tx(uid, "Contest", prize_ton, f"Weekly Referral Contest Prize (Rank #{rank})")
            winners_info.append(f"{rank}. @{user.get('username') or uid} - {prize_usd}$ ≈ {prize_ton} TON (refs: {refs})")
    winners_msg = "🏆 Weekly Referral Contest Winners\n\n" + "\n".join(winners_info)
    if context is not None:
        for admin in ADMINS:
            context.bot.send_message(admin, winners_msg)
    return winners_msg

def schedule_weekly_contest(bot):
    # Get the job queue from the bot's dispatcher
    if not hasattr(bot, 'dispatcher') or not hasattr(bot.dispatcher, 'job_queue'):
        logger.warning("No job queue available for weekly contest scheduling")
        return

    job_queue = bot.dispatcher.job_queue

    def contest_runner(context):
        payout_weekly_contest(context)

    # Schedule to run every Sunday at 23:59 UTC
    job_queue.run_daily(
        contest_runner,
        time=datetime.time(hour=23, minute=59),
        days=(6,)  # Sunday is day 6 (0=Monday)
    )

def referral_contest_leaderboard(update: Update, context: CallbackContext):
    update_weekly_leaderboard()
    prizes = get_weekly_prizes()
    now = datetime.utcnow()
    deadline = datetime(2025, 8, 1)
    days_left = (deadline - now).days

    msg = (
        f"🔥 <b>Final Invite Rush</b>\n\n"
        f"Top 250 inviters share $10,000 in TON by <b>August 1, 2025</b>!\n"
        f"<i>{days_left} days left!</i>\n\n"
        f"Leaderboard updates every 10 minutes.\n\n"
    )
    for rank, (uid, refs) in enumerate(weekly_contest_leaderboard, 1):
        user = get_user(uid)
        uname = user.get("username") or str(uid)
        prize = prizes.get(rank, 0)
        msg += f"{rank}. @{uname} - {refs} referrals"
        if prize:
            msg += f" | ${prize}"
        msg += "\n"
        if rank == 20:
            msg += "...\n"
            break
    msg += "\n<b>Prize breakdown:</b>\n"
    msg += "1st: $500, 2nd: $350, 3rd: $250, 4th: $200, 5th: $150\n"
    msg += "6th: $100, 7th: $90, 8th: $80, 9th: $70, 10th: $60\n"
    msg += "11-50: $40 | 51-100: $20 | 101-250: $10\n"
    msg += "\nPrizes paid in TON at the end of the event!"
    update.message.reply_text(msg, parse_mode="HTML")

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
    update.message.reply_text(msg, parse_mode="Markdown", reply_markup=analytics_menu())

def start_airdrop_ptrst(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in ADMINS:
        airdrop_ptrst_state[user_id] = "amount"
        update.message.reply_text("Enter amount of $PTRST to airdrop to user:", reply_markup=ReplyKeyboardRemove())

def handle_airdrop_ptrst(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in airdrop_ptrst_state:
        return
    
    if airdrop_ptrst_state[user_id] == "amount":
        try:
            amount = int(update.message.text)
            if amount <= 0:
                raise ValueError
            context.user_data['airdrop_amount'] = amount
            airdrop_ptrst_state[user_id] = "target"
            update.message.reply_text("Enter the target user ID (numeric):")
        except ValueError:
            update.message.reply_text("Please enter a valid positive integer amount.")
            del airdrop_ptrst_state[user_id]
    elif airdrop_ptrst_state[user_id] == "target":
        try:
            target_id = int(update.message.text)
            amount = context.user_data['airdrop_amount']
            update_balance(target_id, "ptrst", amount)
            add_tx(target_id, "Airdrop", amount, "Admin airdrop")
            update.message.reply_text(
                f"✅ Successfully sent {amount} $PTRST to user {target_id}",
                reply_markup=admin_panel_keyboard()
            )
            del airdrop_ptrst_state[user_id]
            del context.user_data['airdrop_amount']
        except ValueError:
            update.message.reply_text("Please enter a valid user ID (numbers only).")
        except Exception as e:
            update.message.reply_text(f"Error: {str(e)}")
            del airdrop_ptrst_state[user_id]
            if 'airdrop_amount' in context.user_data:
                del context.user_data['airdrop_amount']

def start_give_ton(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in ADMINS:
        give_ton_state[user_id] = "amount"
        update.message.reply_text("Enter amount of TON to send:", reply_markup=ReplyKeyboardRemove())
def handle_give_ton(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in give_ton_state:
        return
    
    if give_ton_state[user_id] == "amount":
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError
            context.user_data['give_ton_amount'] = amount
            give_ton_state[user_id] = "target"
            update.message.reply_text("Enter the target username (e.g., @premiumdungeon):")
        except ValueError:
            update.message.reply_text("Please enter a valid positive number.")
            del give_ton_state[user_id]
    elif give_ton_state[user_id] == "target":
        try:
            username = update.message.text.strip().lstrip('@')
            # Find user by username
            users = load_users()
            target_id = None
            for uid, data in users.items():
                if isinstance(data, dict) and data.get('username', '').lower() == username.lower():
                    target_id = uid
                    break
            
            if not target_id:
                raise ValueError("User not found")
                
            amount = context.user_data['give_ton_amount']
            update_balance(target_id, "ton", amount)
            add_tx(target_id, "Airdrop", amount, "Admin TON gift")
            update.message.reply_text(
                f"✅ Successfully sent {amount} TON to @{username}",
                reply_markup=admin_panel_keyboard()
            )
            del give_ton_state[user_id]
            del context.user_data['give_ton_amount']
        except Exception as e:
            update.message.reply_text(f"Error: {str(e)}")
            del give_ton_state[user_id]
            if 'give_ton_amount' in context.user_data:
                del context.user_data['give_ton_amount']

def inline_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    query.answer()

    try:
        if data == "check_subscription":
            check_subscription(update, context)
        elif data.startswith("wd_accept_"):
            withdrawal_id = data[len("wd_accept_"):]
            wd = pending_withdrawals.pop(withdrawal_id, None)
            if wd:
                user_id = wd["user_id"]
                amount = wd["amount"]
                token = wd["token"]
                context.bot.send_message(
                    user_id, 
                    f"✅ Your withdrawal of {amount} {token} has been approved by admin."
                )
                query.edit_message_text(f"✅ Withdrawal accepted and user notified.")
            else:
                query.edit_message_text("Withdrawal already processed or not found.")
        elif data.startswith("wd_reject_"):
            withdrawal_id = data[len("wd_reject_"):]
            if withdrawal_id in pending_withdrawals:
                pending_reject_reason[query.from_user.id] = withdrawal_id
                query.edit_message_text("Please type the reason for rejection. Or send 🚫 Cancel")
                context.bot.send_message(
                    query.from_user.id,
                    "Please enter rejection reason:",
                    reply_markup=ReplyKeyboardMarkup([["🚫 Cancel"]], resize_keyboard=True)
                )
            else:
                query.edit_message_text("Withdrawal already processed or not found.")
        else:
            query.edit_message_text("Unknown button action")
    except Exception as e:
        logger.error(f"Error in inline_callback_handler: {e}")
        query.edit_message_text("An error occurred. Please try again.")

def add_tx(user_id, tx_type, amount, desc):
    user = get_user(user_id)
    if "txs" not in user:
        user["txs"] = []
    user["txs"].append({"date": get_datetime(), "type": tx_type, "amount": amount, "desc": desc})
    save_user(user_id, user)

def main_menu_router(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    txt = update.message.text.strip()

    # Check withdraw modes first
    if user_id in ptrst_withdraw_mode or user_id in ton_withdraw_mode:
        return withdraw_request(update, context)
        
    if user_id in pending_reject_reason:
        return process_rejection_reason(update, context)
    if user_id in captcha_store:
        return handle_captcha(update, context)
    if txt in LANGUAGES.values():
        return set_language(update, context)
    if user_id in pending_support and pending_support[user_id]:
        return handle_support(update, context)
    if context.user_data.get("set_task"):
        return handle_task_text(update, context)
    if context.user_data.get("broadcast"):
        return handle_broadcast(update, context)
    if user_id in wallet_input_mode:
        return wallet_handler(update, context)
    if user_id in airdrop_ptrst_state:
        return handle_airdrop_ptrst(update, context)
    if user_id in give_ton_state:
        return handle_give_ton(update, context)
    if context.user_data.get("setting_birthday"):
        return save_birthday(update, context)

    # Main menu button handlers
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
        update.message.reply_text(
    "**🎬 Imagine this...**\n"
    "A token, not just created for hype — but *engineered for impact.*\n"
    "Born on TON. **Powered by people.** Controlled by no one.\n"
    "🔥 **This is $PTRST.**\n\n"
    
    "---\n\n"
    
    "**👑 Welcome to Patrick Star** — a new era where **rewards flow endlessly** to those who dare to take the first step.\n"
    "While others chase charts, you're here **mining value with every tap.**\n\n"
    
    "---\n\n"
    
    "**💰 You don’t buy $PTRST — you earn it.**\n"
    "✅ Complete tasks\n"
    "✅ Invite friends\n"
    "✅ Claim drops every 30 minutes\n"
    "✅ Stack TON bonuses\n"
    "✅ Earn up to *225 $PTRST* per referral chain\n\n"
    
    "**🔐 Withdraw via Tonkeeper only** — fast, secure, and reliable.\n"
    "💵 You earn it? You keep it.\n\n"
    
    "**📅 LISTING DATE:** August 15 @ 16:00 (UTC+3)\n"
    "**DEXES:** DeDust | StonFi | SwapCoffee\n"
    "**💥 Sell instantly on listing!**\n\n"
    
    "**📊 Tokenomics:**\n"
    "• 100,000,000 Total Supply\n"
    "• 70% Airdrop\n"
    "• 15% Listings\n"
    "• 10% Marketing\n"
    "• 5% Team\n"
    "• ✅ Ownership Revoked — **community-owned forever.**\n\n"
    
    "**🎯 Goal:** 10,000 unique Tonkeeper wallets\n\n"
    
    "**🚀 Are you early? Are you ready?**\n"
    "**Then it's time to claim what’s yours.**\n\n"
    
    "**👉 Start now:** @ptrstr_bot\n"
    "💘 Telegram: https://t.me/ptrst_official\n"
    "🐦 Twitter: https://twitter.com/Megabolly"
        )
    elif txt == "📜 Transaction History":
        return transaction_history(update, context)
    elif txt == "🏆 Leaderboard":
        return leaderboard(update, context)
    elif txt == "🎁 Blind Box":
        return blind_box(update, context)
    elif txt == "🎖️ Badges":
        return check_achievements(update, context)
    elif txt == "🔔 Notifications":
        return notifications(update, context)
    elif txt == "🌳 My Referral Tree":
        return referral_tree(update, context)
    elif txt == "🔥 Final Invite Rush":
        return referral_contest_leaderboard(update, context)
    elif txt == "🚏BACK":
        return show_main_menu(update, context)
    elif txt == "📤 $PTRST" or txt == "📤 TON":
        return trigger_withdraw(update, context)
    elif txt == "🏮SET_WALLET":
        return wallet_handler(update, context)
    elif txt == "📈 My Analytics":
        return user_analytics(update, context)
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
    elif txt == "💸 Airdrop $PTRST" and user_id in ADMINS:
        return start_airdrop_ptrst(update, context)
    elif txt == "💵Give TON" and user_id in ADMINS:
        return start_give_ton(update, context)
    elif txt == "📊 Analytics":
        return analytics(update, context)
    elif txt == "/admin":
        return admin(update, context)
    elif txt == "/start":
        return start(update, context)
    else:
        update.message.reply_text("❓ Unrecognized command. Use the menu or /start.")
def register_handlers(dispatcher):
    schedule_withdrawal_check(dispatcher)
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("onboarding", onboarding))
    dispatcher.add_handler(CommandHandler("support", support_command))
    
    # Callback query handler
    dispatcher.add_handler(CallbackQueryHandler(inline_callback_handler))
    
    # Specific button handlers (added before the general text handler)
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📤 \$PTRST$'), trigger_withdraw))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📤 TON$'), trigger_withdraw))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🏮SET_WALLET$'), wallet_handler))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📈 My Analytics$'), user_analytics))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🎖️ Badges$'), check_achievements))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^📜 Transaction History$'), transaction_history))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🏆 Leaderboard$'), leaderboard))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🌳 My Referral Tree$'), referral_tree))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🔔 Notifications$'), notifications))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🎁 Blind Box$'), blind_box))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^🚏BACK$'), show_main_menu))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^💸 Airdrop \$PTRST$'), start_airdrop_ptrst))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^💵Give TON$'), start_give_ton))
    
    # Withdraw amount handler
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & 
        (Filters.user(ptrst_withdraw_mode.keys()) | Filters.user(ton_withdraw_mode.keys())),
        withdraw_request
    ))
    
    # Airdrop and Give TON handlers
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.user(airdrop_ptrst_state.keys()),
        handle_airdrop_ptrst
    ))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.user(give_ton_state.keys()),
        handle_give_ton
    ))
    

    # General text handler (fallback)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, main_menu_router))
    
    # Error handler
    dispatcher.add_error_handler(error_handler)

    # Error handler
    dispatcher.add_error_handler(error_handler)
def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        update.effective_message.reply_text("An error occurred. Please try again.")