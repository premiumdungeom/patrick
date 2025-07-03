import json, os, time
from datetime import datetime
from telegram import ChatMember
from threading import Lock
from functools import wraps
from config import REQUIRED_CHANNELS
from config import REFERRAL_REWARDS, PTRST_COOLDOWN, TON_COOLDOWN

USERS_FILE = "users.json"
PAYOUTS_FILE = "payouts.json"
balance_locks = {}

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

def save_users(users, retries=3):
    for attempt in range(retries):
        try:
            with open(USERS_FILE, "w") as f:
                json.dump(users, f, indent=2)
            return
        except IOError as e:
            if attempt == retries - 1:
                raise
            time.sleep(0.1)

def get_user(user_id):
    users = load_users()
    # Ensure consistent string IDs and initialize all fields
    return users.get(str(user_id), {
        "id": user_id,
        "username": "",
        "referrer": None,
        "referrals_lvl1": [],
        "referrals_lvl2": [],
        "referral_timestamps": [],  # NEW FIELD
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

    # Initialize new user with all required fields
    users[str_uid] = {
        "id": user_id,
        "username": username,
        "referrer": str(referrer_id) if referrer_id else None,  # Ensure string
        "referrals_lvl1": [],
        "referrals_lvl2": [],
        "referral_timestamps": [],  # NEW FIELD
        "balance_ptrst": 0,
        "balance_ton": 0.0,
        "wallet": None,
        "last_ptrst_claim": 0,
        "last_ton_claim": 0,
        "last_active": time.time(),
        "verified": False,
        "txs": []
    }

    # Reward referrer (with type consistency)
    if referrer_id:
        str_ref_id = str(referrer_id)
        if str_ref_id in users:
            users[str_ref_id]["referrals_lvl1"].append(str_uid)
            users[str_ref_id]["balance_ptrst"] += REFERRAL_REWARDS["level_1"]
            
            # Add timestamp for the new referral
            users[str_ref_id]["referral_timestamps"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "referral_id": str_uid
            })

            # Handle level 2 referral
            lvl2_ref = users[str_ref_id].get("referrer")
            if lvl2_ref and lvl2_ref in users:
                users[lvl2_ref]["referrals_lvl2"].append(str_uid)
                users[lvl2_ref]["balance_ptrst"] += REFERRAL_REWARDS["level_2"]

    save_users(users)
    return users[str_uid]

def migrate_existing_users():
    """One-time migration for existing users"""
    users = load_users()
    for user_id, data in users.items():
        # Initialize referral_timestamps if missing
        if "referral_timestamps" not in data:
            data["referral_timestamps"] = []
            
        # Convert any integer IDs to strings
        if isinstance(data.get("referrer"), int):
            data["referrer"] = str(data["referrer"])
            
        # Convert referral lists
        data["referrals_lvl1"] = [str(x) for x in data.get("referrals_lvl1", [])]
        data["referrals_lvl2"] = [str(x) for x in data.get("referrals_lvl2", [])]
    
    save_users(users)
    print(f"Migrated {len(users)} user records")

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

def check_sybil_attempt(user_id, ip_address):
    """Detect potential multi-account abuse"""
    user = get_user(user_id)
    
    # Check if IP was used recently
    if ip_address in user.get("ip_addresses", []):
        return True
        
    # Track new IP
    user.setdefault("ip_addresses", []).append(ip_address)
    save_user(user_id, user)
    return False

def validate_referral_chain(user_id, referrer_id):
    """Prevent circular referrals"""
    visited = set()
    current = referrer_id
    
    while current:
        if current == user_id:
            return False  # Circular reference
        if current in visited:
            return False  # Loop detected
        visited.add(current)
        current = get_user(current).get("referrer")
        
    return True

def get_balance_lock(user_id):
    if user_id not in balance_locks:
        balance_locks[user_id] = Lock()
    return balance_locks[user_id]

def update_balance(user_id, token, amount):
    """Thread-safe balance update with overflow check"""
    with get_balance_lock(user_id):
        user = get_user(user_id)
        current = user.get(f"balance_{token}", 0)
        
        # Prevent negative balances
        if amount < 0 and abs(amount) > current:
            raise ValueError(f"Insufficient {token} balance")
            
        user[f"balance_{token}"] = current + amount
        save_user(user_id, user)

def deduct_balance(user_id, token, amount):
    """Deduction with verification"""
    update_balance(user_id, token, -amount)

def rate_limit(key, calls=3, period=10):
    """Decorator to limit function calls"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = args[1].effective_user.id  # Update/CallbackContext
            cache_key = f"{key}_{user_id}"
            
            now = time.time()
            timestamps = getattr(wrapped, '_timestamps', {})

            # Clean old entries
            timestamps[cache_key] = [t for t in timestamps.get(cache_key, []) 
                                  if now - t < period]
            
            if len(timestamps.get(cache_key, [])) >= calls:
                raise Exception(f"Rate limited: {calls} calls per {period}s")
                
            timestamps.setdefault(cache_key, []).append(now)
            wrapped._timestamps = timestamps
            return f(*args, **kwargs)
        return wrapped
    return decorator

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
