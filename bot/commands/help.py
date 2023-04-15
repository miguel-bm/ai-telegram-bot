from pathlib import Path

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.logs import logging

# Load the help text from bot/assets/help_text.md

HELP_TEXT_FILENAME = Path("bot/config/help_text.md")
with open(HELP_TEXT_FILENAME, "r") as f:
    help_text = f.read()


async def help_commnad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logging.info(
        f"User {update.effective_user.username} with id {update.effective_user.id} requested help"
    )
    await update.message.reply_markdown(help_text)


help_commnad_handler = CommandHandler("help", help_commnad)
