import logging

from decouple import config
from telegram import Bot
from telegram.ext import Application, CommandHandler

from bot.commands.help import help_commnad_handler
from bot.commands.sumarize import summarize_conversation_handler
from bot.logs import logging
import toml

BOT_TOKEN = config("BOT_API_KEY", default=None)
access = toml.load("bot/config/access.toml")


def main():
    bot = Bot(token=BOT_TOKEN)
    app = Application.builder().bot(bot).concurrent_updates(True).build()

    # add logs
    app.add_handler(help_commnad_handler)
    app.add_handler(summarize_conversation_handler)

    logging.info("Bot started, press Ctrl+C to stop it")
    app.run_polling()


if __name__ == "__main__":
    main()
