from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

from config import OWNER_ID
from utils.constants import CMD_NAME
from utils.access import check_access

router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>@sambat1234</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return

    welcome = (
        "<blockquote><code>𝗢𝗿𝗮𝗻𝗴_𝗟𝗲𝗺𝗮𝗵 ⚡</code></blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗵𝗲𝗰𝗸𝗼𝘂𝘁 𝗖𝗵𝗮𝗿𝗴𝗲𝗿\n"
        f"    • <code>/{CMD_NAME} url cc|mm|yy|cvv</code> - Charge Card\n"
        f"    • <code>/{CMD_NAME} url bin</code> - Generate & Charge from BIN</blockquote>\n\n"
        "<blockquote>「❃」 𝗣𝗿𝗼𝘅𝘆 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀\n"
        "    • <code>/addproxy proxy</code> - Add proxy\n"
        "    • <code>/removeproxy proxy</code> - Remove proxy\n"
        "    • <code>/removeproxy all</code> - Remove all proxies\n"
        "    • <code>/proxy check</code> - Check proxy status</blockquote>\n\n"
        "<blockquote>「❃」 𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀\n"
        "    • <code>/purge</code> - Delete all messages\n"
        "    • <code>/lock</code> - Lock group chat\n"
        "    • <code>/unlock</code> - Unlock group chat\n"
        "    • <code>/stopbot</code> - Stop the bot\n"
        "    • <code>/startbot</code> - Activate the bot\n"
        "    • <code>/globalproxy add proxy</code> - Add global proxy\n"
        "    • <code>/globalproxy remove proxy</code> - Remove global proxy</blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 : <code>@Oranglemah97</code></blockquote>"
    )
    await msg.answer(welcome, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def help_handler(msg: Message):
    if not check_access(msg):
        await msg.answer(
            "<blockquote><code>𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱 ❌</code></blockquote>\n\n"
            "<blockquote>「❃」 𝗝𝗼𝗶𝗻 𝘁𝗼 𝘂𝘀𝗲 : <code>@sambat1234</code></blockquote>",
            parse_mode=ParseMode.HTML
        )
        return

    help_text = (
        "<blockquote><code>𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 📋</code></blockquote>\n\n"
        "<blockquote>「❃」 <code>/start</code> - Show welcome message\n"
        "「❃」 <code>/help</code> - Show this help\n"
        f"「❃」 <code>/{CMD_NAME} url</code> - Parse checkout info\n"
        f"「❃」 <code>/{CMD_NAME} url cards</code> - Charge cards</blockquote>\n\n"
        "<blockquote>「❃」 𝗣𝗿𝗼𝘅𝘆 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀\n"
        "「❃」 <code>/addproxy proxy</code> - Add proxy\n"
        "「❃」 <code>/removeproxy proxy</code> - Remove proxy\n"
        "「❃」 <code>/removeproxy all</code> - Remove all proxies\n"
        "「❃」 <code>/proxy check</code> - Check proxy status</blockquote>\n\n"
        "<blockquote>「❃」 𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 (𝗢𝘄𝗻𝗲𝗿 𝗢𝗻𝗹𝘆)\n"
        "「❃」 <code>/purge</code> - Delete all group messages\n"
        "「❃」 <code>/lock</code> - Lock group chat\n"
        "「❃」 <code>/unlock</code> - Unlock group chat\n"
        "「❃」 <code>/stopbot</code> - Stop the bot\n"
        "「❃」 <code>/startbot</code> - Activate the bot\n"
        "「❃」 <code>/globalproxy add proxy</code> - Add global proxy\n"
        "「❃」 <code>/globalproxy remove proxy</code> - Remove global proxy</blockquote>\n\n"
        "<blockquote>「❃」 𝗖𝗮𝗿𝗱 𝗙𝗼𝗿𝗺𝗮𝘁 : <code>cc|mm|yy|cvv</code>\n"
        "「❃」 𝗘𝘅𝗮𝗺𝗽𝗹𝗲 : <code>4242424242424242|12|25|123</code></blockquote>"
    )
    await msg.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(Command("myid"))
async def myid_handler(msg: Message):
    from config import ALLOWED_GROUP
    await msg.answer(
        f"<blockquote><code>𝗜𝗗 𝗜𝗻𝗳𝗼 🔍</code></blockquote>\n\n"
        f"<blockquote>「❃」 𝗖𝗵𝗮𝘁 𝗜𝗗 : <code>{msg.chat.id}</code>\n"
        f"「❃」 𝗖𝗵𝗮𝘁 𝗧𝘆𝗽𝗲 : <code>{msg.chat.type}</code>\n"
        f"「❃」 𝗨𝘀𝗲𝗿 𝗜𝗗 : <code>{msg.from_user.id}</code>\n"
        f"「❃」 𝗔𝗹𝗹𝗼𝘄𝗲𝗱 : <code>{ALLOWED_GROUP}</code></blockquote>",
        parse_mode=ParseMode.HTML
    )
