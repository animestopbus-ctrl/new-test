from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db

@Client.on_message(filters.command("set_thumb") & filters.private)
async def set_custom_thumbnail(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    if not message.reply_to_message or not message.reply_to_message.photo:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
        return await message.reply_text(
            "<b>🖼 Set Custom Thumbnail</b>\n\n"
            "<i>Reply to any photo with /set_thumb to use it as your default thumbnail.</i>\n\n"
            "<b>Usage:</b> Reply to a photo → <code>/set_thumb</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    file_id = message.reply_to_message.photo.file_id
    await db.set_thumbnail(user_id, file_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ View Thumb", callback_data="view_thumb_btn"), InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    await message.reply_photo(
        photo=file_id,
        caption=(
            "<b>✅ Custom Thumbnail Set Successfully! 🎉</b>\n\n"
            "<i>This thumbnail will be used for all your future uploads.</i>\n"
            "<i>Use /view_thumb to preview • /del_thumb to remove</i>"
        ),
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

@Client.on_message(filters.command(["view_thumb", "see_thumb"]) & filters.private)
async def view_custom_thumbnail(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    thumb_id = await db.get_thumbnail(user_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🗑 Delete", callback_data="del_thumb_btn"), InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    if thumb_id:
        try:
            await message.reply_photo(
                photo=thumb_id,
                caption=(
                    "<b>🖼 Your Current Custom Thumbnail</b>\n\n"
                    "<i>This is applied to all uploads.</i>\n"
                    "<i>To delete, use /del_thumb</i>"
                ),
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons
            )
        except Exception as e:
            await message.reply_text(f"<b>❌ Error loading thumbnail:</b> {e}\n<i>Please set a new one.</i>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text(
            "<b>❌ No Custom Thumbnail Found</b>\n\n"
            "<i>Reply to a photo with /set_thumb to add one.</i>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

@Client.on_message(filters.command(["del_thumb", "delete_thumb"]) & filters.private)
async def delete_custom_thumbnail(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    thumb_id = await db.get_thumbnail(user_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    if not thumb_id:
        return await message.reply_text(
            "<b>ℹ️ You don't have a custom thumbnail set.</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    await db.del_thumbnail(user_id)

    await message.reply_text(
        "<b>🗑 Custom Thumbnail Deleted Successfully! ✅</b>\n\n"
        "<i>Your uploads will now use the default video/file thumbnail.</i>",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

@Client.on_message(filters.command("thumb_mode") & filters.private)
async def thumbnail_status(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    thumb_id = await db.get_thumbnail(user_id)

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🖼 Set Thumb", callback_data="set_thumb_btn"), InlineKeyboardButton("🔙 Back", callback_data="settings_back_btn")]])
    if thumb_id:
        status = "<b>🟢 Custom Thumbnail Active ✅</b>"
        extra = "<i>Use /view_thumb to preview</i>"
    else:
        status = "<b>🔴 No Custom Thumbnail ❌</b>"
        extra = "<i>Use /set_thumb (reply to photo) to enable</i>"

    await message.reply_text(
        f"<b>🖼 Thumbnail Status</b>\n\n"
        f"{status}\n"
        f"{extra}",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex("^(view_thumb_btn|del_thumb_btn|set_thumb_btn)$"))
async def thumb_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data == "view_thumb_btn":
        await view_custom_thumbnail(client, callback_query.message)
    elif data == "del_thumb_btn":
        await delete_custom_thumbnail(client, callback_query.message)
    elif data == "set_thumb_btn":
        await callback_query.answer("Reply to a photo with /set_thumb")
    await callback_query.answer()
