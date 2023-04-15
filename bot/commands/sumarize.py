from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters

from bot.logs import logging
from bot.utilities.url_validator import is_valid_url
from bot.utilities.pdf_reader import extract_text_from_pdf
from bot.utilities.summary_generator import generate_summary
import asyncio

TIMEOUT_SECONDS = 120

TEXT_TO_SUMMARIZE = 0


async def sumarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Takes in a text, URL, or file and returns a summary of the text."""
    logging.info(
        f"User {update.effective_user.username} with id {update.effective_user.id} requested a summary"
    )

    await update.message.reply_text("Please send me a text, URL, or file to summarize.")
    return TEXT_TO_SUMMARIZE


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Cancelling...")
    return ConversationHandler.END


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancels and ends the conversation."""
    return ConversationHandler.END


async def timeout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancels and ends the conversation."""
    logging.info(
        f"Summarize conversation with {update.effective_user.username} timed out, cancelling"
    )
    await update.message.reply_text("Summarize conversation timed out, cancelling")
    return ConversationHandler.END


async def summary_generator(text: str) -> str:
    """Generates a summary of the text"""
    return generate_summary(text)


async def summary_text_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles text responses"""
    text_from_user = update.message.text

    # If the user sends a URL, download the text from the URL
    if is_valid_url(text_from_user):
        url = text_from_user
        logging.info(f"Downloading text from {url}")
        # Send reply saying we're downloading the text
        await update.message.reply_text(f"Downloading text from {text_from_user}...")
        # After a few seconds, reply that this is not implemented yet
        await asyncio.sleep(2)
        await update.message.reply_text("This is not implemented yet, sorry!")
        return ConversationHandler.END

    summary_promise = summary_generator(text_from_user)
    await update.message.reply_text(f"Generating summary...")
    summary = await summary_promise
    await update.message.reply_text(summary)
    return ConversationHandler.END


async def summary_pdf_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles text responses"""
    try:
        document = update.message.document
        logging.info(f"Getting text from PDF")
        await update.message.reply_text(f"Downloading PDF...")
        file = await document.get_file()
        file_path = await file.download_to_drive("temp.pdf")
        text_from_file = extract_text_from_pdf(file_path)
        # delete file
        file_path.unlink()
    except:
        logging.info(f"Error getting text from PDF")
        await update.message.reply_text("Error downloading PDF, it might be too large!")
        return ConversationHandler.END

    summary_promise = summary_generator(text_from_file)
    await update.message.reply_text(f"Generating summary...")
    logging.info(f"Generating summary")
    summary = await summary_promise
    await update.message.reply_text(summary)
    return ConversationHandler.END


summarize_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("summarize", sumarize_command)],
    states={
        TEXT_TO_SUMMARIZE: [
            MessageHandler(filters.TEXT, summary_text_handler),
            MessageHandler(filters.Document.PDF, summary_pdf_handler),
        ],
        ConversationHandler.TIMEOUT: [
            MessageHandler(filters.TEXT | filters.COMMAND, timeout_callback)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
    conversation_timeout=TIMEOUT_SECONDS,
    name="summarize_conversation_handler",
)
