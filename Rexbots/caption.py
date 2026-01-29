from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db

@Client.on_message(filters.command("set_caption") & filters.private)
async def set_caption(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    if len(message.command) < 2:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
        return await message.reply_text(
            "<b>⚠️ Usage Error</b>\n\n"
            "Provide caption text after command.\n\n"
            "<b>Format:</b> <code>/set_caption Your Caption</code>\n\n"
            "<b>Placeholders:</b>\n"
            "• {filename} : Name\n"
            "• {size} : Size\n\n"
            "<i>Example: /set_caption File: {filename} | Size: {size}</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    caption = message.text.split(" ", 1)[1].strip()
    await db.set_caption(user_id, caption)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("👀 Preview", callback_data="see_caption_btn"), InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    await message.reply_text(
        "<b>✅ Custom Caption Saved! 🎉</b>\n\n"
        f"<b>Preview:</b>\n<code>{caption}</code>\n\n"
        "<i>Applied to future saves.</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

@Client.on_message(filters.command("see_caption") & filters.private)
async def see_caption(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    caption = await db.get_caption(user_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete", callback_data="del_caption_btn"), InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    if caption:
        await message.reply_text(
            "<b>📝 Your Custom Caption</b>\n\n"
            f"<code>{caption}</code>\n\n"
            "<i>To delete, use /del_caption</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            "<b>❌ No Caption Set</b>\n\n"
            "Using default.\n"
            "<i>Use /set_caption to customize.</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

@Client.on_message(filters.command("del_caption") & filters.private)
async def del_caption(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    caption = await db.get_caption(user_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    if not caption:
        return await message.reply_text(
            "<b>⚠️ No Caption Found</b>\n\n"
            "No custom caption set.",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    await db.del_caption(user_id)

    await message.reply_text(
        "<b>🗑 Custom Caption Removed ✅</b>\n\n"
        "<i>Using default now.</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex("^(see_caption_btn|del_caption_btn)$"))
async def caption_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "see_caption_btn":
        await see_caption(client, callback_query.message)
    elif data == "del_caption_btn":
        await del_caption(client, callback_query.message)
    await callback_query.answer()
