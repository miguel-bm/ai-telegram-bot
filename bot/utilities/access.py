from dataclasses import dataclass
from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext

import toml

from bot.utilities.logging import get_logger

logger = get_logger(__name__)

ACCESS_FILE = "bot/config/access.toml"


@dataclass
class AccessManager:
    admins: list[str]
    whitelist: list[str]

    def from_toml(toml_file: str = ACCESS_FILE) -> "AccessManager":
        return AccessManager(**toml.load(toml_file))

    def is_admin(self, user_id: str) -> bool:
        return str(user_id) in self.admins

    def is_whitelisted(self, user_id: str) -> bool:
        return str(user_id) in self.whitelist

    def is_allowed(self, user_id: str) -> bool:
        return self.is_admin(user_id) or self.is_whitelisted(user_id)

    def add_admin(self, user_id: str) -> None:
        if not self.is_admin(user_id):
            self.admins.append(str(user_id))
        logger.info(f"Added user {user_id} as admin")

    def add_whitelisted_user(self, user_id: str) -> None:
        if not self.is_whitelisted(user_id):
            self.whitelist.append(str(user_id))
        logger.info(f"Added user {user_id} to whitelist")

    def remove_admin(self, user_id: str) -> None:
        if self.is_admin(user_id):
            self.admins.remove(str(user_id))
        logger.info(f"Removed user {user_id} as admin")

    def remove_whitelisted_user(self, user_id: str) -> None:
        if self.is_whitelisted(user_id):
            self.whitelist.remove(str(user_id))
        logger.info(f"Removed user {user_id} from whitelist")

    def to_toml(self, toml_file: str = ACCESS_FILE) -> None:
        toml.dump(
            {
                "admins": self.admins,
                "whitelist": self.whitelist,
            },
            open(toml_file, "w"),
        )


def restricted(access_manager: AccessManager, only_admin: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
            username = str(update.effective_user.username)
            if only_admin:
                has_access = access_manager.is_admin(username)
            else:
                has_access = access_manager.is_allowed(username)
            if not has_access:
                logger.info(f"Unauthorized access denied for {username}.")
                await update.message.reply_text(
                    "You are not authorized to use this functionality."
                )
                return
            return await func(update, context, *args, **kwargs)

        return wrapped

    return decorator
