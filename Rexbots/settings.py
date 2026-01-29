import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from strings import COMMANDS_TXT

@Client.on_message(filters.command("settings") & filters.private)
async def settings_menu(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    is_premium = await db.check_premium(user_id)
    premium_badge = "💎 Premium" if is_premium else "👤 Free"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
        [
            InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
            InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
        ],
        [InlineKeyboardButton("🔤 Words", callback_data="words_btn")],
        [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
    ])

    text = (
        f"<b>⚙️ Settings Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Account:</b> {premium_badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Customize your experience below. 🚀</i>"
    )

    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("commands") & filters.private)
async def direct_commands(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]
    ])

    await message.reply_text(
        COMMANDS_TXT,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex("^(cmd_list_btn|user_stats_btn|dump_chat_btn|thumb_btn|caption_btn|words_btn|settings_back_btn|close_btn)$"))
async def settings_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message

    back_close = [[InlineKeyboardButton("⬅️ Back", callback_data="settings_back_btn"), InlineKeyboardButton("❌ Close", callback_data="close_btn")]]

    if data == "cmd_list_btn":
        await callback_query.edit_message_text(COMMANDS_TXT, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "dump_chat_btn":
        dump_chat = await db.get_dump_chat(user_id)
        text = (
            f"<b>🗑 Dump Chat Settings</b>\n\n"
            f"<b>Current:</b> <code>{dump_chat if dump_chat else 'None'}</code>\n\n"
            "<i>Use /setchat <chat_id> to set • /setchat clear to remove</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "thumb_btn":
        thumb_id = await db.get_thumbnail(user_id)
        text = (
            f"<b>🖼 Thumbnail Settings</b>\n\n"
            f"<b>Status:</b> {'Active ✅' if thumb_id else 'Inactive ❌'}\n\n"
            "<i>Use /set_thumb (reply) • /view_thumb • /del_thumb • /thumb_mode</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "caption_btn":
        caption = await db.get_caption(user_id)
        text = (
            f"<b>📝 Caption Settings</b>\n\n"
            f"<b>Current:</b> <code>{caption if caption else 'Default'}</code>\n\n"
            "<i>Use /set_caption <text> • /see_caption • /del_caption</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "words_btn":
        del_words = await db.get_delete_words(user_id)
        repl_words = await db.get_replace_words(user_id)
        text = (
            f"<b>🔤 Words Settings</b>\n\n"
            f"<b>Delete Words:</b> {', '.join(del_words) if del_words else 'None'}\n"
            f"<b>Replace Words:</b> {', '.join([f'{k}->{v}' for k,v in repl_words.items()]) if repl_words else 'None'}\n\n"
            "<i>Use /set_del_word • /rem_del_word • /set_repl_word • /rem_repl_word</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "user_stats_btn":
        is_premium = await db.check_premium(user_id)
        user_data = await db.col.find_one({'id': int(user_id)})
        
        if is_premium:
            limit_text = "♾️ Unlimited"
            usage_text = "Ignored (Premium) 💎"
        else:
            daily_limit = 10
            used = user_data.get('daily_usage', 0)
            limit_text = f"{daily_limit} / 24h"
            usage_text = f"{used} / {daily_limit}"

        text = (
            f"<b>📊 My Usage Statistics</b>\n\n"
            f"<b>Plan:</b> {'💎 Premium' if is_premium else '👤 Free'}\n"
            f"<b>Daily Limit:</b> <code>{limit_text}</code>\n"
            f"<b>Today's Usage:</b> <code>{usage_text}</code>\n"
            f"<b>Total Saves:</b> <code>{user_data.get('total_saves', 0)}</code>\n\n"
            f"<i>Upgrade for unlimited! 💎</i>"
        )
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(back_close), parse_mode=enums.ParseMode.HTML)

    elif data == "settings_back_btn":
        is_premium = await db.check_premium(user_id)
        premium_badge = "💎 Premium" if is_premium else "👤 Free"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Chat", callback_data="dump_chat_btn")],
            [
                InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
                InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
            ],
            [InlineKeyboardButton("🔤 Words", callback_data="words_btn")],
            [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
        ])
        
        text = (
            f"<b>⚙️ Settings Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Account:</b> {premium_badge}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Select option to customize. 🚀</i>"
        )
        
        await callback_query.edit_message_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

    elif data == "close_btn":
        await callback_query.message.delete()

    await callback_query.answer()
