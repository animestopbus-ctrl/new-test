from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database.db import db
from config import ADMINS
from datetime import date, datetime, timedelta
from logger import LOGGER

logger = LOGGER(__name__)

@Client.on_message(filters.command("myplan") & filters.private)
async def my_plan(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    user_data = await db.col.find_one({'id': user_id})
    
    is_premium = user_data.get('is_premium', False)
    expiry = user_data.get('premium_expiry')
    daily_usage = user_data.get('daily_usage', 0)
    total_saves = user_data.get('total_saves', 0)

    if is_premium:
        if expiry:
            try:
                exp_date = datetime.fromisoformat(str(expiry))
                days_left = (exp_date - datetime.now()).days
                expiry_text = f"<code>{expiry}</code> ({days_left} days left)"
            except:
                expiry_text = "<code>Active</code>"
        else:
            expiry_text = "<code>Permanent ♾️</code>"

        plan_text = (
            f"<b>👑 Premium Status: Active ✅</b>\n\n"
            f"<b>📅 Expiry:</b> {expiry_text}\n\n"
            f"<b>♾️ Daily Tokens:</b> Unlimited\n"
            f"<b>♾️ Batch Limit:</b> Unlimited\n"
            f"<b>📊 Total Lifetime Saves:</b> <code>{total_saves}</code>\n"
            f"<b>🚀 Extra: Large files, YouTube integration</b>"
        )
    else:
        plan_text = (
            f"<b>👤 Free Plan Status</b>\n\n"
            f"<b>📅 Expiry:</b> N/A\n\n"
            f"<b>🔒 Daily Tokens:</b> <code>{daily_usage}/10</code>\n"
            f"<b>📦 Batch Limit:</b> 5 Files\n"
            f"<b>📊 Total Lifetime Saves:</b> <code>{total_saves}</code>\n\n"
            f"<i>Upgrade to premium for unlimited access! 💎</i>"
        )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Upgrade Now", callback_data="premium_plans_btn")],
        [InlineKeyboardButton("🔙 Back", callback_data="myplan_back_btn")]
    ])
    await message.reply_text(plan_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("premium") & filters.private)
async def premium_plans(client: Client, message: Message):
    text = (
        "<b>💎 Premium Plans</b>\n\n"
        "<b>Benefits:</b>\n"
        "• ♾️ Unlimited daily saves\n"
        "• ♾️ Unlimited batch size\n"
        "• Large file streaming\n"
        "• YouTube/FB/Insta downloader\n"
        "• Priority support\n\n"
        "<i>Contact admin to purchase.</i>"
    )
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to My Plan", callback_data="myplan_back_btn")]])
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("add_premium") & filters.user(ADMINS) & filters.private)
async def add_premium_admin(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "<b>⚠️ Usage:</b> <code>/add_premium &lt;user_id&gt; &lt;days&gt;</code>\n\n"
            "<i>Use 0 for permanent premium.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    try:
        user_id = int(message.command[1])
        days = int(message.command[2])

        if days == 0:
            expiry_date = None
            duration_text = "Permanent ♾️"
        else:
            expiry_date = (datetime.now() + timedelta(days=days)).isoformat()
            duration_text = f"{days} days (until {expiry_date})"

        await db.add_premium(user_id, expiry_date)

        await message.reply_text(
            f"<b>✅ Premium Added Successfully</b>\n\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n"
            f"<b>Duration:</b> {duration_text}",
            parse_mode=enums.ParseMode.HTML
        )

    except ValueError:
        await message.reply_text("❌ <b>Error:</b> User ID and Days must be numbers.", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> {e}", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("remove_premium") & filters.user(ADMINS) & filters.private)
async def remove_premium_admin(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>⚠️ Usage:</b> <code>/remove_premium &lt;user_id&gt;</code>",
            parse_mode=enums.ParseMode.HTML
        )
    try:
        user_id = int(message.command[1])
        await db.remove_premium(user_id)
        await message.reply_text(f"✅ Premium removed from <code>{user_id}</code>.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_callback_query(filters.regex("^premium_plans_btn$"))
async def premium_plans_callback(client: Client, callback_query: CallbackQuery):
    text = (
        "<b>💎 Premium Plans</b>\n\n"
        "<b>Benefits:</b>\n"
        "• ♾️ Unlimited daily saves\n"
        "• ♾️ Unlimited batch size\n"
        "• Large file streaming\n"
        "• YouTube/FB/Insta downloader\n"
        "• Priority support\n\n"
        "<i>Contact admin to purchase.</i>"
    )
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to My Plan", callback_data="myplan_back_btn")]])
    await callback_query.edit_message_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("^myplan_back_btn$"))
async def myplan_back_callback(client: Client, callback_query: CallbackQuery):
    await my_plan(client, callback_query.message)
