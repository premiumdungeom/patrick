# config.py
import pytz
from datetime import datetime

# Admin user IDs
ADMINS = [5650788149, 548105255]

TOKEN = "8042213784:AAEnFnkHGue3pdIAjTfWll-WqWvLHWLpF0w"

# Define only the required channel
REQUIRED_CHANNELS = ["ptrst_official"]

CHANNEL_USERNAME = "@ptrst_official"

WEBHOOK_URL = "https://patrickeded.onrender.com"

# Cooldowns (in seconds)
PTRST_COOLDOWN = 30 * 60       # 30 minutes cooldown for $PTRST bonus
TON_COOLDOWN = 8 * 60 * 60     # 8 hours cooldown for TON bonus

# Emojis for interface
EMOJIS = {
    "start": "⚠️",
    "new_task": "🆕",
    "account": "💰",
    "ptrst": "👑",
    "friends": "👫",
    "bonus": "🎁",
    "ton": "⛏️",
    "about": "🛠️",
    "admin_panel": "💘",
    "pending_withdraw": "😇",
    "total_user": "🚀",
    "total_payout": "💱",
    "broadcast": "👗",
    "set_new_task": "🍍",
    "task_history": "📝"
}

# Referral reward amounts
REFERRAL_REWARDS = {
    "level_1": 150,  # $PTRST reward for level 1 referral
    "level_2": 75    # $PTRST reward for level 2 referral
}

# Withdrawal settings
MIN_WITHDRAWAL_PTRST = 2000      # Minimum $PTRST withdrawal
MIN_WITHDRAWAL_TON = 0.2         # Minimum TON withdrawal

UTC = pytz.UTC
RUSH_START_DATE = datetime(2025, 7, 3, tzinfo=UTC)
WITHDRAWAL_START_DATE = datetime(2025, 8, 1, tzinfo=UTC)

MAX_DAILY_CLAIMS = 48
MAX_REWARD_PTRST = 1000

USER_LOCK_TIMEOUT = 30
