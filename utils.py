# utils.py

import json, os, time
from datetime import datetime
from config import REFERRAL_REWARDS, PTRST_COOLDOWN, TON_COOLDOWN

USERS_FILE = "users.json"
PAYOUTS_FILE = "payouts.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id), None)

def save_user(user_id, user_data):
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

def create_user(user_id, username, referrer_id=None):
    users = load_users()
    if str(user_id) in users:
        return users[str(user_id)]

    users[str(user_id)] = {
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
        "last_active": time.time()
    }

    # reward the referrer
    if referrer_id and str(referrer_id) in users:
        users[str(referrer_id)]["referrals_lvl1"].append(str(user_id))
        users[str(referrer_id)]["balance_ptrst"] += REFERRAL_REWARDS["level_1"]

        lvl2 = users[str(referrer_id)].get("referrer")
        if lvl2 and lvl2 in users:
            users[lvl2]["referrals_lvl2"].append(str(user_id))
            users[lvl2]["balance_ptrst"] += REFERRAL_REWARDS["level_2"]

    save_users(users)
    return users[str(user_id)]

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