import json, os, time
from datetime import datetime
from telegram import ChatMember
from config import REQUIRED_CHANNELS
from config import REFERRAL_REWARDS, PTRST_COOLDOWN, TON_COOLDOWN

USERS_FILE = "users.json"
PAYOUTS_FILE = "payouts.json"

def user_exists(user_id: int) -> bool:
    """Check if a user exists in the database"""
    users = load_users()
    return str(user_id) in users

def load_users() -> dict:
    """Load all users from JSON file"""
    if not os.path.exists('users.json'):
        return {}
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(user_id):
    users = load_users()
    # Always return a dict, if the user does not exist, return a blank profile for new users (helps with txs etc)
    return users.get(str(user_id), {
        "id": user_id,
        "username": "",
        "referrer": None,
        "referrals_lvl1": [],
        "referrals_lvl2": [],
        "balance_ptrst": 0,
        "balance_ton": 0.0,
        "wallet": None,
        "last_ptrst_claim": 0,
        "last_ton_claim": 0,
        "last_active": time.time(),
        "verified": False,
        "txs": []
    })

def save_user(user_id, user_data):
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

def create_user(user_id, username, referrer_id=None):
    users = load_users()
    str_uid = str(user_id)
    if str_uid in users:
        return users[str_uid]

    users[str_uid] = {
        "id": user_id,
        "username": username,
        "referrer": str(referrer_id) if referrer_id else None,
        "referrals_lvl1": [],
        "referrals_lvl2": [],
        "balance_ptrst": 0,
        "balance_ton": 0.0,
        "wallet": None,
        "last_ptrst_claim": 0,
        "last_ton_claim": 0,
        "last_active": time.time(),
        "verified": False,
        "txs": []
    }

    # reward the referrer
    if referrer_id and str(referrer_id) in users:
        users[str(referrer_id)]["referrals_lvl1"].append(str_uid)
        users[str(referrer_id)]["balance_ptrst"] += REFERRAL_REWARDS["level_1"]

        lvl2 = users[str(referrer_id)].get("referrer")
        if lvl2 and lvl2 in users:
            users[lvl2]["referrals_lvl2"].append(str_uid)
            users[lvl2]["balance_ptrst"] += REFERRAL_REWARDS["level_2"]

    save_users(users)
    return users[str_uid]

def check_cooldown(user_data, token_type):
    now = time.time()
    last = user_data.get(f"last_{token_type}_claim", 0)
    cooldown = PTRST_COOLDOWN if token_type == "ptrst" else TON_COOLDOWN
    return max(0, int(cooldown - (now - last)))

def update_claim_time(user_id, token_type):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)][f"last_{token_type}_claim"] = time.time()
        save_users(users)

def update_wallet(user_id, wallet_address):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["wallet"] = wallet_address
        save_users(users)

def update_balance(user_id, token_type, amount):
    users = load_users()
    if str(user_id) in users:
        if token_type == "ptrst":
            users[str(user_id)]["balance_ptrst"] += int(amount)
        elif token_type == "ton":
            users[str(user_id)]["balance_ton"] += float(amount)
        save_users(users)

def deduct_balance(user_id, token_type, amount):
    users = load_users()
    if str(user_id) in users:
        if token_type == "ptrst":
            users[str(user_id)]["balance_ptrst"] -= int(amount)
        elif token_type == "ton":
            users[str(user_id)]["balance_ton"] -= float(amount)
        save_users(users)

def check_subscription(bot, user_id):
    # Check subscription for only the required channel (gouglenetwork)
    channel = REQUIRED_CHANNELS[0]  # Get the first (and only) channel in the list
    try:
        member = bot.get_chat_member(f"@{channel}", user_id)
        # Check if the user is a member, admin, or owner
        if member.status not in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]:
            return False  # User is not subscribed
    except:
        return False  # Channel not found or error
    return True  # User is subscribed

def format_time(seconds):
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{int(hours)} H. {int(mins)} M."
    return f"{int(mins)} M. {int(secs)} S."

def update_total_payout(token_type, amount):
    if os.path.exists(PAYOUTS_FILE):
        with open(PAYOUTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"ptrst": 0, "ton": 0.0}

    if token_type == "ptrst":
        data["ptrst"] += int(amount)
    elif token_type == "ton":
        data["ton"] += float(amount)

    with open(PAYOUTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_total_payouts():
    if os.path.exists(PAYOUTS_FILE):
        with open(PAYOUTS_FILE, "r") as f:
            return json.load(f)
    return {"ptrst": 0, "ton": 0.0}

def get_datetime():
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

# --- Transaction log utility ---
def add_tx(user_id, tx_type, amount, desc):
    users = load_users()
    str_uid = str(user_id)
    if str_uid not in users:
        users[str_uid] = create_user(user_id, "")
    user = users[str_uid]
    if "txs" not in user:
        user["txs"] = []
    user["txs"].append({
        "date": get_datetime(),
        "type": tx_type,
        "amount": amount,
        "desc": desc
    })
    save_users(users)
