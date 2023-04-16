from decouple import config

API_KEY_VARS = {
    "prod": "BOT_API_KEY",
    "dev": "DEV_BOT_API_KEY",
}
ENV_VAR = "ENV_NAME"


def get_bot_token() -> str:
    environment = config(ENV_VAR, default="prod")
    if environment not in API_KEY_VARS:
        raise ValueError(f"Invalid environment defined by {ENV_VAR}: {environment}")

    if token := config(API_KEY_VARS[environment], default=None):
        return token
    raise ValueError(f"API key not found for environment {environment}")
