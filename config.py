"""
Merkezi konfigürasyon modülü.
Tüm ayarlar .env dosyasından okunur, yoksa varsayılan değerler kullanılır.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Gmail SMTP ────────────────────────────────────────────
GMAIL_ADDRESS: str = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
NOTIFICATION_EMAIL: str = os.getenv("NOTIFICATION_EMAIL", "")

# ── Scraper ───────────────────────────────────────────────
SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "true").lower() == "true"

# ── Flask ─────────────────────────────────────────────────
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# ── Veri Dosyaları ────────────────────────────────────────
DATA_DIR: Path = BASE_DIR / "data"
PRODUCTS_FILE: Path = DATA_DIR / "products.json"
PRICE_HISTORY_FILE: Path = DATA_DIR / "price_history.json"
