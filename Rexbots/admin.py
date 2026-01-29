# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import ADMINS, DB_URI

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/ban user_id`")
    try:
        user_id = int(message.command[1])
        await db.ban_user(user_id)
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done", callback_data="admin_done")]])
        await message.reply_text(f"**User {user_id} Banned Successfully 🚫**", reply_markup=buttons)
    except:
        await message.reply_text("Error banning user.")

@Client.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/unban user_id`")
    try:
        user_id = int(message.command[1])
        await db.unban_user(user_id)
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done", callback_data="admin_done")]])
        await message.reply_text(f"**User {user_id} Unbanned Successfully ✅**", reply_markup=buttons)
    except:
        await message.reply_text("Error unbanning user.")

@Client.on_message(filters.command("set_dump") & filters.user(ADMINS))
async def set_dump(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("**Usage:** `/set_dump user_id chat_id`")
    try:
        user_id = int(message.command[1])
        chat_id = int(message.command[2])
        await db.set_dump_chat(user_id, chat_id)
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done", callback_data="admin_done")]])
        await message.reply_text(f"**Dump chat set for user {user_id}.**", reply_markup=buttons)
    except:
        await message.reply_text("Error setting dump chat.")

@Client.on_message(filters.command("dblink") & filters.user(ADMINS))
async def dblink(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Done", callback_data="admin_done")]])
    await message.reply_text(f"**DB URI:** `{DB_URI}`", reply_markup=buttons)

@Client.on_message(filters.command(["add_unsubscribe", "del_unsubscribe"]) & filters.user(ADMINS))
async def manage_force_subscribe(client: Client, message: Message):
    await message.reply_text("Force Subscribe management feature is coming soon.")

@Client.on_callback_query(filters.regex("admin_done"))
async def admin_done(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Action completed!")
