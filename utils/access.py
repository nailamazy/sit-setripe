from aiogram.types import Message

from config import ALLOWED_GROUP, OWNER_ID


def check_access(msg: Message) -> bool:
    """Check if user has access to use the bot.
    Single definition used by all command handlers."""
    from commands.admin import is_bot_paused
    if is_bot_paused():
        return False
    if msg.chat.id == ALLOWED_GROUP:
        return True
    if msg.chat.type == "private" and msg.from_user.id == OWNER_ID:
        return True
    return False
