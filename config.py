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
DATABASE_PATH = os.getenv("DATABASE_PATH", "auto_split.db")

# Pro tier: set PRO_LICENSE_KEY to any non-empty string to enable Pro features
IS_PRO = bool(os.getenv("PRO_LICENSE_KEY"))
