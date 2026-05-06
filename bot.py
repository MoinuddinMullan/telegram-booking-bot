# # bot.py
# import logging
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import (
#     Application, CommandHandler, CallbackQueryHandler,
#     MessageHandler, filters, ContextTypes, ConversationHandler
# )
# from database import Database
# from config import AVAILABLE_DATES, DOCUMENTS_LIST, UPLOAD_LINK, FEEDBACK_LINK
# import os
# from dotenv import load_dotenv

# load_dotenv()
# BOT_TOKEN = os.getenv("BOT_TOKEN")

# db = Database()

# # Conversation states
# DATE_SELECTION, WAITING_UPLOAD, WAITING_FEEDBACK = range(3)

# logging.basicConfig(level=logging.INFO)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Welcome message + show date buttons"""
#     keyboard = [
#         [InlineKeyboardButton(date, callback_data=date)]
#         for date in AVAILABLE_DATES
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
    
#     await update.message.reply_text(
#         "👋 Welcome to our service!\n\nPlease select an appointment date:",
#         reply_markup=reply_markup
#     )
#     return DATE_SELECTION

# async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """User tapped a date button"""
#     query = update.callback_query
#     await query.answer()
    
#     selected_date = query.data
#     user = query.from_user
    
#     # Check if date is available
#     if db.is_date_available(selected_date):
#         # Save booking
#         db.create_booking(user.id, user.username, user.full_name, selected_date)
        
#         await query.edit_message_text(
#             f"✅ Your booking for *{selected_date}* is confirmed!\n\n"
#             f"Please prepare the following documents:\n{DOCUMENTS_LIST}\n\n"
#             f"📎 Upload your documents here:\n{UPLOAD_LINK}",
#             parse_mode="Markdown"
#         )
        
#         await query.message.reply_text(
#             "Once you have uploaded your documents, send me a message saying 'done' "
#             "or send the files directly here."
#         )
#         return WAITING_UPLOAD
#     else:
#         # Date not available — show buttons again
#         keyboard = [
#             [InlineKeyboardButton(date, callback_data=date)]
#             for date in AVAILABLE_DATES if date != selected_date
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
        
#         await query.edit_message_text(
#             f"❌ Sorry, *{selected_date}* is no longer available.\n\nPlease choose another date:",
#             reply_markup=reply_markup,
#             parse_mode="Markdown"
#         )
#         return DATE_SELECTION

# async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """User sent a file or said 'done'"""
#     user = update.effective_user
    
#     if update.message.document:
#         file_id = update.message.document.file_id
#         db.save_upload(user.id, file_id)
    
#     # Send feedback form
#     await update.message.reply_text(
#         f"✅ Documents received! Thank you.\n\n"
#         f"We'd love your feedback:\n{FEEDBACK_LINK}"
#     )
#     return WAITING_FEEDBACK

# async def handle_feedback_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """User confirmed feedback submitted"""
#     await update.message.reply_text(
#         "🙏 Thank you for choosing us! We look forward to seeing you.\n\n"
#         "If you need anything, just send /start to begin again."
#     )
#     return ConversationHandler.END

# def main():
#     app = Application.builder().token(BOT_TOKEN).build()
    
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={
#             DATE_SELECTION: [CallbackQueryHandler(handle_date_selection)],
#             WAITING_UPLOAD: [
#                 MessageHandler(filters.Document.ALL, handle_upload),
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, handle_upload),
#             ],
#             WAITING_FEEDBACK: [
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback_done)
#             ],
#         },
#         fallbacks=[CommandHandler("start", start)],
#     )
    
#     app.add_handler(conv_handler)
#     app.run_polling()

# if __name__ == "__main__":
#     main()
from datetime import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from config import AVAILABLE_DATES, DOCUMENTS_LIST, FEEDBACK_QUESTION
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

db = Database()

DATE_SELECTION, WAITING_UPLOAD, WAITING_FEEDBACK, WAITING_COMMENT = range(4)

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(date, callback_data=date)]
        for date in AVAILABLE_DATES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome to our service!\n\nPlease select an appointment date:",
        reply_markup=reply_markup
    )
    return DATE_SELECTION


async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_date = query.data
    user = query.from_user

    if db.is_date_available(selected_date):
        db.create_booking(user.id, user.username, user.full_name, selected_date)

        # ✅ TRACK SESSION START
        context.user_data["session_start"] = datetime.utcnow()

        await query.edit_message_text(
            f"✅ Your booking for *{selected_date}* is confirmed!\n\n"
            f"Please prepare the following documents:\n{DOCUMENTS_LIST}",
            parse_mode="Markdown"
        )

        await query.message.reply_text(
            "📎 Please send your documents *directly in this chat* as file attachments.\n\n"
            "You can send multiple files one by one.\n"
            "When you are done sending all files, type *done*.",
            parse_mode="Markdown"
        )
        return WAITING_UPLOAD

    else:
        keyboard = [
            [InlineKeyboardButton(date, callback_data=date)]
            for date in AVAILABLE_DATES if date != selected_date
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"❌ Sorry, *{selected_date}* is no longer available.\n\nPlease choose another date:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return DATE_SELECTION


async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        db.save_upload(user.id, file_id, file_name)

        await update.message.reply_text(
            f"✅ *{file_name}* received!\n\n"
            "Send the next file, or type *done* if finished.",
            parse_mode="Markdown"
        )
        return WAITING_UPLOAD

    elif update.message.text and update.message.text.strip().lower() == "done":
        # ✅ USE SESSION-BASED UPLOAD CHECK
        session_start = context.user_data.get("session_start", datetime.utcnow())
        uploads = db.get_session_uploads(user.id, session_start)

        if not uploads:
            await update.message.reply_text(
                "⚠️ No documents received yet.\n\nPlease upload files first, then type *done*.",
                parse_mode="Markdown"
            )
            return WAITING_UPLOAD

        await update.message.reply_text(
            f"✅ All documents received! ({len(uploads)} file(s))\n\n{FEEDBACK_QUESTION}"
        )
        return WAITING_FEEDBACK

    else:
        await update.message.reply_text(
            "📎 Please send files as attachments.\nType *done* when finished.",
            parse_mode="Markdown"
        )
        return WAITING_UPLOAD


async def handle_feedback_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rating = update.message.text.strip()

    if rating not in ["1", "2", "3", "4", "5"]:
        await update.message.reply_text(
            "⚠️ Please enter a number between *1 and 5*.",
            parse_mode="Markdown"
        )
        return WAITING_FEEDBACK

    context.user_data["feedback_rating"] = rating

    await update.message.reply_text(
        f"⭐ You rated us *{rating}/5*\n\n"
        "Want to add a comment?\nType your message or *skip*.",
        parse_mode="Markdown"
    )
    return WAITING_COMMENT


async def handle_feedback_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    rating = context.user_data.get("feedback_rating", "N/A")

    # ✅ FIXED SKIP WORDS
    skip_words = ["skip", "finish", "done", "no", "nothing", "nope"]
    comment = "" if text.lower() in skip_words else text

    db.save_feedback(user.id, rating, comment)

    await update.message.reply_text(
        "🙏 Thank you for your feedback!\n\nSend /start anytime to book again."
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DATE_SELECTION: [CallbackQueryHandler(handle_date_selection)],
            WAITING_UPLOAD: [
                MessageHandler(filters.Document.ALL, handle_upload),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_upload),
            ],
            WAITING_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback_rating)
            ],
            WAITING_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback_comment)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()