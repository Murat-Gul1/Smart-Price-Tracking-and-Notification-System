"""
Merkezi konfigurasyon modulu.
Tum ayarlar .env dosyasindan okunur, yoksa varsayilan degerler kullanilir.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _clean_env(name: str, default: str = "") -> str:
    """Ornek placeholder degerleri gercek ayar gibi kullanma."""
    value = os.getenv(name, default).strip()
    placeholders = {
        "your_telegram_bot_token_here",
        "your_chat_id_here",
        "your_email@gmail.com",
        "your_app_password_here",
        "recipient@example.com",
    }
    if value in placeholders:
        return ""
    return value


# Telegram
TELEGRAM_BOT_TOKEN: str = _clean_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = _clean_env("TELEGRAM_CHAT_ID")

# Gmail SMTP
GMAIL_ADDRESS: str = _clean_env("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD: str = _clean_env("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL: str = _clean_env("NOTIFICATION_EMAIL")

# Scraper
SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"

# Flask
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Veri dosyalari
DATA_DIR: Path = BASE_DIR / "data"
PRODUCTS_FILE: Path = DATA_DIR / "products.json"
PRICE_HISTORY_FILE: Path = DATA_DIR / "price_history.json"
