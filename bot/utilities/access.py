from dataclasses import dataclass
from bot.utilities.logging import get_logger
import toml

logger = get_logger(__name__)

ACCESS_FILE = "bot/config/access.toml"


@dataclass
class AccessManager:
    admins: list[str]
    whitelisted_users: list[str]

    def from_toml(toml_file: str = ACCESS_FILE) -> "AccessManager":
        return AccessManager(**toml.load(toml_file))

    def is_admin(self, user_id: str) -> bool:
        return str(user_id) in self.admins

    def is_whitelisted(self, user_id: str) -> bool:
        return str(user_id) in self.whitelisted_users

    def is_allowed(self, user_id: str) -> bool:
        return self.is_admin(user_id) or self.is_whitelisted(user_id)

    def add_admin(self, user_id: str) -> None:
        if not self.is_admin(user_id):
            self.admins.append(str(user_id))
        logger.info(f"Added user {user_id} as admin")

    def add_whitelisted_user(self, user_id: str) -> None:
        if not self.is_whitelisted(user_id):
            self.whitelisted_users.append(str(user_id))
        logger.info(f"Added user {user_id} to whitelist")

    def remove_admin(self, user_id: str) -> None:
        if self.is_admin(user_id):
            self.admins.remove(str(user_id))
        logger.info(f"Removed user {user_id} as admin")

    def remove_whitelisted_user(self, user_id: str) -> None:
        if self.is_whitelisted(user_id):
            self.whitelisted_users.remove(str(user_id))
        logger.info(f"Removed user {user_id} from whitelist")

    def to_toml(self, toml_file: str = ACCESS_FILE) -> None:
        toml.dump(
            {
                "admins": self.admins,
                "whitelisted_users": self.whitelisted_users,
            },
            open(toml_file, "w"),
        )
