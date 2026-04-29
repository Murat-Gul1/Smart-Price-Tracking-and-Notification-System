"""
Zamanlayici Modulu - APScheduler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Periyodik fiyat kontrolu yapar (varsayilan: 6 saatte bir).
Scraper'i cagirir, fiyatlari gunceller, alarm tetikler.
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import HEADLESS_BROWSER, SCRAPE_INTERVAL_HOURS

logger = logging.getLogger(__name__)

# Global scheduler
_scheduler: BackgroundScheduler | None = None


async def _check_all_prices() -> list[dict]:
    """
    Tum takip edilen urunlerin fiyatlarini kontrol eder.
    Alarm olusanlari dondurur.
    """
    from app.services import check_all_tracked_products

    return await check_all_tracked_products(headless=HEADLESS_BROWSER)


def _run_price_check() -> None:
    """Senkron wrapper - APScheduler'dan cagrilir."""
    from app.email_service import send_price_alert_email
    from app.services import acknowledge_alert
    from app.telegram_bot import send_telegram_alert

    loop = asyncio.new_event_loop()
    try:
        alerts = loop.run_until_complete(_check_all_prices())

        for alert in alerts:
            email_sent = False
            telegram_sent = False

            try:
                email_sent = send_price_alert_email(alert)
            except Exception as e:
                logger.error(f"E-posta gonderme hatasi: {e}")

            try:
                telegram_sent = loop.run_until_complete(send_telegram_alert(alert))
            except Exception as e:
                logger.error(f"Telegram gonderme hatasi: {e}")

            if email_sent or telegram_sent:
                acknowledge_alert(alert)
            else:
                logger.warning(
                    "[scheduler] Alarm gonderilemedi; cooldown kaydi yazilmadi. "
                    "product_id=%s kind=%s",
                    alert.get("product_id"),
                    alert.get("kind"),
                )
    finally:
        loop.close()


def start_scheduler() -> BackgroundScheduler:
    """
    Zamanlayiciyi baslatir.
    Her SCRAPE_INTERVAL_HOURS saatte bir tum urunleri kontrol eder.
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.warning("Zamanlayici zaten calisiyor.")
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_price_check,
        trigger=IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS),
        id="price_check_job",
        name=f"Fiyat Kontrolu (her {SCRAPE_INTERVAL_HOURS} saat)",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        f"Zamanlayici baslatildi: her {SCRAPE_INTERVAL_HOURS} saatte bir kontrol yapilacak."
    )
    return _scheduler


def stop_scheduler() -> None:
    """Zamanlayiciyi durdurur."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Zamanlayici durduruldu.")


def trigger_manual_check() -> list[dict]:
    """Manuel fiyat kontrolu tetikler (web arayuzunden kullanilir)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_check_all_prices())
    finally:
        loop.close()
