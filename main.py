"""
Smart Price Tracking and Notification System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ana giriş noktası.
Flask web arayüzünü, zamanlayıcıyı ve opsiyonel olarak Telegram bot'unu başlatır.
"""

import logging
import sys
import threading

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)-20s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("price_tracker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def main():
    """Uygulamayı başlatır."""
    from config import FLASK_PORT, FLASK_DEBUG, TELEGRAM_BOT_TOKEN
    from app.web import create_app
    from app.scheduler import start_scheduler

    logger.info("=" * 60)
    logger.info("🛒 Smart Price Tracker başlatılıyor...")
    logger.info("=" * 60)

    # 1. Data dizinini oluştur
    from config import DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Flask uygulamasını oluştur
    app = create_app()
    logger.info(f"🌐 Flask web arayüzü hazır → http://localhost:{FLASK_PORT}")

    # 3. Zamanlayıcıyı başlat
    start_scheduler()

    # 4. Telegram bot'unu başlat (opsiyonel, ayrı thread'de)
    if TELEGRAM_BOT_TOKEN:
        try:
            from app.telegram_bot import create_telegram_app

            telegram_app = create_telegram_app()
            if telegram_app:
                def run_telegram():
                    try:
                        telegram_app.run_polling(drop_pending_updates=True)
                    except Exception as e:
                        logger.error(f"Telegram bot hatası: {e}")

                telegram_thread = threading.Thread(target=run_telegram, daemon=True)
                telegram_thread.start()
                logger.info("🤖 Telegram bot başlatıldı (arka planda).")
        except Exception as e:
            logger.warning(f"Telegram bot başlatılamadı: {e}")
    else:
        logger.info("ℹ️ TELEGRAM_BOT_TOKEN tanımlı değil. Telegram bot devre dışı.")

    # 5. Flask'ı başlat
    logger.info(f"🚀 Sunucu başlıyor: http://localhost:{FLASK_PORT}")
    app.run(
        host="0.0.0.0",
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False,  # Scheduler çakışmasını önle
    )


if __name__ == "__main__":
    main()
