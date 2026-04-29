"""
Smart Price Tracking and Notification System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ana giris noktasi.
Flask web arayuzunu, zamanlayiciyi ve opsiyonel olarak Telegram botunu baslatir.
"""

import atexit
import asyncio
import logging
import os
import sys
import threading

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows-specific guard.
    msvcrt = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("price_tracker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

_single_instance_lock = None


def _acquire_single_instance_lock(lock_path):
    """Prevent a second local app instance from starting Telegram polling."""
    global _single_instance_lock

    if msvcrt is None:
        logger.warning("Tek instance kilidi bu platformda desteklenmiyor.")
        return True

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_file = open(lock_path, "r+b")
    except FileNotFoundError:
        lock_file = open(lock_path, "w+b")

    try:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write(b"\0")
            lock_file.flush()

        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return False

    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(str(os.getpid()).encode("ascii"))
    lock_file.flush()
    _single_instance_lock = lock_file

    def release_lock():
        global _single_instance_lock
        if _single_instance_lock is None:
            return
        try:
            _single_instance_lock.seek(0)
            msvcrt.locking(_single_instance_lock.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            _single_instance_lock.close()
        except OSError:
            pass
        _single_instance_lock = None

    atexit.register(release_lock)
    return True


def main():
    """Uygulamayi baslatir."""
    from config import DATA_DIR, FLASK_DEBUG, FLASK_PORT, TELEGRAM_BOT_TOKEN
    from app.scheduler import start_scheduler
    from app.web import create_app

    logger.info("=" * 60)
    logger.info("Smart Price Tracker baslatiliyor...")
    logger.info("=" * 60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = DATA_DIR / "price_tracker.lock"
    if not _acquire_single_instance_lock(lock_path):
        logger.error(
            "Baska bir Smart Price Tracker instance calisiyor. "
            "Telegram polling conflict yasamamak icin bu instance baslatilmadi."
        )
        return
    logger.info(f"Tek instance kilidi alindi (pid={os.getpid()}).")

    app = create_app()
    logger.info(f"Flask web arayuzu hazir -> http://localhost:{FLASK_PORT}")

    start_scheduler()

    if TELEGRAM_BOT_TOKEN:
        try:
            from app.telegram_bot import create_telegram_app

            telegram_app = create_telegram_app()
            if telegram_app:

                def run_telegram():
                    try:
                        asyncio.set_event_loop(asyncio.new_event_loop())
                        logger.info(
                            "Telegram polling baslatiliyor "
                            f"(pid={os.getpid()}, thread={threading.current_thread().name})."
                        )
                        telegram_app.run_polling(
                            drop_pending_updates=True,
                            stop_signals=None,
                        )
                    except Exception as e:
                        logger.exception(f"Telegram bot hatasi: {e}")

                telegram_thread = threading.Thread(
                    target=run_telegram,
                    name="telegram-polling",
                    daemon=True,
                )
                telegram_thread.start()
                logger.info("Telegram bot baslatildi (arka planda).")
        except Exception as e:
            logger.exception(f"Telegram bot baslatilamadi: {e}")
    else:
        logger.info("TELEGRAM_BOT_TOKEN tanimli degil. Telegram bot devre disi.")

    logger.info(f"Sunucu basliyor: http://localhost:{FLASK_PORT}")
    app.run(
        host="0.0.0.0",
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
