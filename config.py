import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


TELEGRAM_TOKEN = _require("TELEGRAM_TOKEN")
GEMINI_API_KEY = _require("GEMINI_API_KEY")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
DATABASE_PATH = os.getenv("DATABASE_PATH", "auto_split.db")
