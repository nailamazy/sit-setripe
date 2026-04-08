import time

# Per-user rate limiting: {user_id: [timestamp1, timestamp2, ...]}
_user_rate_limits = {}

# Max cards per minute per user
MAX_CARDS_PER_MINUTE = 50

# Max cards per single command
MAX_CARDS_PER_COMMAND = 50


def check_rate_limit(user_id: int) -> bool:
    """Check if user is within rate limit.
    Returns True if allowed, False if rate-limited."""
    now = time.time()

    if user_id not in _user_rate_limits:
        _user_rate_limits[user_id] = []

    # Remove entries older than 60 seconds
    _user_rate_limits[user_id] = [t for t in _user_rate_limits[user_id] if now - t < 60]

    if len(_user_rate_limits[user_id]) >= MAX_CARDS_PER_MINUTE:
        return False

    _user_rate_limits[user_id].append(now)
    return True


def get_remaining_quota(user_id: int) -> int:
    """Get how many cards a user can still charge this minute."""
    now = time.time()

    if user_id not in _user_rate_limits:
        return MAX_CARDS_PER_MINUTE

    # Clean old entries
    _user_rate_limits[user_id] = [t for t in _user_rate_limits[user_id] if now - t < 60]

    return max(0, MAX_CARDS_PER_MINUTE - len(_user_rate_limits[user_id]))


def get_cooldown_seconds(user_id: int) -> int:
    """Get seconds until the user can charge again (0 if not limited)."""
    now = time.time()

    if user_id not in _user_rate_limits:
        return 0

    _user_rate_limits[user_id] = [t for t in _user_rate_limits[user_id] if now - t < 60]

    if len(_user_rate_limits[user_id]) < MAX_CARDS_PER_MINUTE:
        return 0

    # Earliest entry that still counts
    oldest = min(_user_rate_limits[user_id])
    return max(0, int(60 - (now - oldest)) + 1)
