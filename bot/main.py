from telegram import Bot
from telegram.ext import Application

from bot.commands.help import help_commnad_handler
from bot.commands.sumarize import summarize_conversation_handler
from bot.utilities.logging import get_logger
from bot.utilities.token import get_bot_token
from bot.utilities.access import AccessManager


logger = get_logger(__name__)

bot_token = get_bot_token()
access_manager = AccessManager.from_toml()


def main():
    # Create the bot and pass it to the app
    bot = Bot(token=bot_token)
    app = Application.builder().bot(bot).concurrent_updates(True).build()

    # Add handlers to the app
    app.add_handler(help_commnad_handler)
    app.add_handler(summarize_conversation_handler)

    # Start the bot
    logger.info("Bot started, press Ctrl+C to stop it")
    app.run_polling()


if __name__ == "__main__":
    main()
