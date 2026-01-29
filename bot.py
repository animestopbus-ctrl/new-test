import asyncio
import datetime
import sys
import os
from datetime import timezone, timedelta
import uvloop
import re
from pytube import YouTube

from pyrogram import Client, filters, enums, __version__ as pyrogram_version
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, InputMediaDocument

from config import API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL
from database.db import db
from logger import LOGGER

try:
    from keep_alive import keep_alive
except ImportError:
    keep_alive = None

logger = LOGGER(__name__)

IST = timezone(timedelta(hours=5, minutes=30))

LOGO = r"""


  ██████╗  ██╗  ██╗  █████╗  ███╗   ██╗ ██████╗   █████╗  ██╗      
  ██╔══██╗ ██║  ██║ ██╔══██╗ ████╗  ██║ ██╔══██╗ ██╔══██╗ ██║      
  ██║  ██║ ███████║ ███████║ ██╔██╗ ██║ ██████╔╝ ███████║ ██║      
  ██║  ██║ ██╔══██║ ██╔══██║ ██║╚██╗██║ ██╔═══╝  ██╔══██║ ██║      
  ██████╔╝ ██║  ██║ ██║  ██║ ██║ ╚████║ ██║      ██║  ██║ ███████
"""

uvloop.install()  # Speedup

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Rexbots_Login_Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="."),  # Load from current dir
            workers=20,  # Increased for performance
            sleep_threshold=10,
            max_concurrent_transmissions=20,  # Faster uploads
            ipv6=False,
            in_memory=False
        )

    async def start(self):
        await super().start()
        logger.info(LOGO)
        bot = await self.get_me()
        now = datetime.datetime.now(IST)
        start_text = (
            f"<b><i>#BotStarted 🤖</i></b>\n\n"
            f"<b>Bot:</b> @{bot.username}\n"
            f"<b>Username:</b> {bot.first_name}\n"
            f"<b>User ID:</b> <code>{bot.id}</code>\n\n"
            f"<b>Pyrogram:</b> <code>{pyrogram_version}</code>\n\n"
            f"<b>📅 Date:</b> <code>{now.strftime('%d %B %Y')}</code>\n"
            f"<b>🕒 Time:</b> <code>{now.strftime('%I:%M %p')} IST</code>\n\n"
            f"<b>Developed by @RexBots_Official</b>"
        )
        try:
            await self.send_message(LOG_CHANNEL, start_text, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send to log channel: {e}. Logging to console.")

        # Set command menu
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help"),
            BotCommand("settings", "Customize settings"),
            BotCommand("login", "Login session"),
            BotCommand("logout", "Logout session"),
            BotCommand("myplan", "Check plan"),
            BotCommand("premium", "Premium info"),
            BotCommand("save", "Save content (send link)"),
            BotCommand("batch", "Batch save (e.g., link/100-110)"),
            BotCommand("cmd", "Refresh command menu"),
            BotCommand("set_caption", "Set caption"),
            BotCommand("del_caption", "Delete caption"),
            BotCommand("set_thumb", "Set thumbnail"),
            BotCommand("del_thumb", "Delete thumbnail"),
            BotCommand("set_del_word", "Set delete words"),
            BotCommand("rem_del_word", "Remove delete words"),
            BotCommand("set_repl_word", "Set replace words"),
            BotCommand("rem_repl_word", "Remove replace words"),
            BotCommand("setchat", "Set dump chat")
        ]
        await self.set_bot_commands(commands)

    async def stop(self):
        bot = await self.get_me()
        now = datetime.datetime.now(IST)
        stop_text = (
            f"<b><i>#BotStopped 🛑</i></b>\n\n"
            f"<b>Bot:</b> @{bot.username}\n"
            f"<b>Username:</b> {bot.first_name}\n"
            f"<b>User ID:</b> <code>{bot.id}</code>\n\n"
            f"<b>📅 Date:</b> <code>{now.strftime('%d %B %Y')}</code>\n"
            f"<b>🕒 Time:</b> <code>{now.strftime('%I:%M %p')} IST</code>\n\n"
            f"<b>Developed by @RexBots_Official</b>"
        )
        try:
            await self.send_message(LOG_CHANNEL, stop_text, parse_mode=enums.ParseMode.HTML)
        except:
            pass
        await super().stop()
        logger.info("Bot stopped cleanly")

BotInstance = Bot()

BATCH_STATE = {}

async def progress_callback(current, total, message, text):
    percent = current * 100 / total
    bar = '█' * int(percent / 10) + '-' * (10 - int(percent / 10))
    await message.edit_text(f"{text}\n[{bar}] {percent:.1f}%")

@BotInstance.on_message(filters.private & filters.command("cmd"))
async def refresh_commands(client: Client, message: Message):
    await client.start()  # Re-run set_commands
    await message.reply("✅ Command menu refreshed! Check bottom menu.")

@BotInstance.on_message(filters.private & (filters.command(["save", "batch"]) | filters.regex(r"https?://(t.me|youtube.com|youtu.be)")))
async def save_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if await db.is_banned(user_id):
        return await message.reply("<b>❌ You are banned.</b>")

    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    if await db.check_limit(user_id):
        return await message.reply("<b>❌ Daily limit reached. Upgrade to premium.</b>")

    session = await db.get_session(user_id)
    if not session and "t.me" in message.text:
        return await message.reply("<b>⚠️ Please /login for restricted content.</b>")

    link = message.text.strip()
    is_premium = await db.check_premium(user_id)
    max_concurrent = float('inf') if is_premium else 5

    progress_msg = await message.reply("<b>🔄 Processing...</b>")
    BATCH_STATE[user_id] = {"status": "running", "progress_msg": progress_msg, "current": 0, "total": 1}

    try:
        if "youtube.com" in link or "youtu.be" in link:
            # YouTube downloader
            yt = YouTube(link)
            stream = yt.streams.get_highest_resolution()
            file_path = await asyncio.to_thread(stream.download)
            caption = await db.get_caption(user_id) or yt.title
            thumb = await db.get_thumbnail(user_id)
            del_words = await db.get_delete_words(user_id)
            repl_words = await db.get_replace_words(user_id)
            for word in del_words:
                caption = caption.replace(word, "")
            for target, repl in repl_words.items():
                caption = caption.replace(target, repl)
            dump_chat = await db.get_dump_chat(user_id)
            await client.send_video(
                dump_chat or user_id,
                video=file_path,
                caption=caption,
                thumb=thumb,
                progress=progress_callback,
                progress_args=(progress_msg, "Uploading YouTube video...")
            )
            os.remove(file_path)
        else:
            # Telegram link
            match = re.match(r"https://t.me/(?P<chat>[\w+]+)/?(?P<start>\d+)?-?(?P<end>\d+)?", link)
            if not match:
                raise ValueError("Invalid link")
            chat = match.group("chat")
            start = int(match.group("start") or 1)
            end = int(match.group("end") or start)
            total = end - start + 1
            if total > max_concurrent and not is_premium:
                raise ValueError("Batch too large for free users")
            BATCH_STATE[user_id]["total"] = total
            user_client = Client(f"user_{user_id}", session_string=session) if session else client
            await user_client.start()
            tasks = []
            for msg_id in range(start, end + 1):
                if BATCH_STATE[user_id]["status"] != "running":
                    break
                tg_msg = await user_client.get_messages(chat, msg_id)
                if not tg_msg:
                    continue
                caption = tg_msg.caption or ""
                filename = tg_msg.document.file_name if tg_msg.document else ""
                del_words = await db.get_delete_words(user_id)
                repl_words = await db.get_replace_words(user_id)
                for word in del_words:
                    caption = caption.replace(word, "")
                    filename = filename.replace(word, "")
                for target, repl in repl_words.items():
                    caption = caption.replace(target, repl)
                    filename = filename.replace(target, repl)
                custom_caption = await db.get_caption(user_id)
                if custom_caption:
                    caption = custom_caption.format(filename=filename, size=tg_msg.document.file_size if tg_msg.document else 0)
                thumb = await db.get_thumbnail(user_id)
                dump_chat = await db.get_dump_chat(user_id)
                if tg_msg.document and tg_msg.document.file_size > 2000000000:  # Large file stream link
                    link_msg = await tg_msg.copy(dump_chat or user_id, as_copy=True)
                    await message.reply(f"Stream link: {link_msg.link}")
                else:
                    tasks.append(asyncio.create_task(tg_msg.copy(dump_chat or user_id, caption=caption, thumb=thumb)))
                BATCH_STATE[user_id]["current"] += 1
                current = BATCH_STATE[user_id]["current"]
                total = BATCH_STATE[user_id]["total"]
                await progress_msg.edit(f"<b>📥 Saving: {current}/{total}</b>")
                await db.add_traffic(user_id)
            await asyncio.gather(*tasks)
            await user_client.stop()
        await progress_msg.edit("<b>✅ Save complete! 🎉</b>")
    except Exception as e:
        await progress_msg.edit(f"<b>❌ Error: {e}</b>")
    finally:
        if user_id in BATCH_STATE:
            del BATCH_STATE[user_id]

@BotInstance.on_message(filters.private & filters.command("cancel"))
async def cancel_batch(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in BATCH_STATE and BATCH_STATE[user_id]["status"] == "running":
        BATCH_STATE[user_id]["status"] = "cancelled"
        await BATCH_STATE[user_id]["progress_msg"].edit("<b>❌ Batch cancelled. ✅</b>")

@BotInstance.on_message(filters.private & filters.incoming, group=-1)
async def new_user_log(bot: Client, message: Message):
    user = message.from_user
    if not user:
        return

    if await db.is_user_exist(user.id):
        return

    await db.add_user(user.id, user.first_name)

    now = datetime.datetime.now(IST)
    username_text = f"@{user.username}" if user.username else "<i>None</i>"

    new_user_text = (
        f"<b><i>#NewUser 👤 Joined the Bot</i></b>\n\n"
        f"<b>Bot:</b> @{bot.me.username}\n\n"
        f"<b>User:</b> {user.mention(style='html')}\n"
        f"<b>Username:</b> {username_text}\n"
        f"<b>User ID:</b> <code>{user.id}</code>\n\n"
        f"<b>📅 Date:</b> <code>{now.strftime('%d %B %Y')}</code>\n"
        f"<b>🕒 Time:</b> <code>{now.strftime('%I:%M %p')} IST</code>\n\n"
        f"<b>Developed by @RexBots_Official</b>"
    )

    try:
        await bot.send_message(
            LOG_CHANNEL,
            new_user_text,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f"New user logged: {user.id} - {user.first_name}")
    except Exception as e:
        logger.error(f"Failed to log new user {user.id}: {e}")

if __name__ == "__main__":
    if keep_alive:
        keep_alive()
    BotInstance.run()
