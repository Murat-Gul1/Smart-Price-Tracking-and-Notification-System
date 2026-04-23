"""
Zamanlayıcı Modülü — APScheduler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Periyodik fiyat kontrolü yapar (varsayılan: 6 saatte bir).
Scraper'ı çağırır, fiyatları günceller, alarm tetikler.
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import SCRAPE_INTERVAL_HOURS, HEADLESS_BROWSER
from app.logic import get_tracker
from app.scraper import scrape_product_url, ScraperError

logger = logging.getLogger(__name__)

# Global scheduler
_scheduler: BackgroundScheduler | None = None


async def _check_all_prices() -> list[dict]:
    """
    Tüm takip edilen ürünlerin fiyatlarını kontrol eder.
    Alarm oluşanları döndürür.
    """
    tracker = get_tracker()
    products = tracker.get_all_products()

    if not products:
        logger.info("Takip listesi boş. Kontrol atlandı.")
        return []

    logger.info(f"🔍 {len(products)} ürün kontrol ediliyor...")
    alerts = []

    for product_id, product in products.items():
        url = product.get("url")
        if not url:
            continue

        try:
            result = await scrape_product_url(url, headless=HEADLESS_BROWSER)

            alert = tracker.update_price(
                product_id=product_id,
                new_price=result.get("price"),
                in_stock=result.get("in_stock", True),
                title=result.get("title", ""),
                image_url=result.get("image_url", ""),
            )

            if alert:
                alerts.append(alert)

        except ScraperError as e:
            logger.error(f"Scraping hatası ({product_id}): {e}")
        except Exception as e:
            logger.error(f"Beklenmeyen hata ({product_id}): {e}")

    logger.info(
        f"✅ Kontrol tamamlandı. "
        f"{len(products)} ürün kontrol edildi, "
        f"{len(alerts)} alarm tetiklendi."
    )
    return alerts


def _run_price_check() -> None:
    """Senkron wrapper — APScheduler'dan çağrılır."""
    from app.email_service import send_price_alert_email
    from app.telegram_bot import send_telegram_alert

    loop = asyncio.new_event_loop()
    try:
        alerts = loop.run_until_complete(_check_all_prices())

        # Alarmları bildir
        for alert in alerts:
            # E-posta bildirimi
            try:
                send_price_alert_email(alert)
            except Exception as e:
                logger.error(f"E-posta gönderme hatası: {e}")

            # Telegram bildirimi
            try:
                loop.run_until_complete(send_telegram_alert(alert))
            except Exception as e:
                logger.error(f"Telegram gönderme hatası: {e}")

    finally:
        loop.close()


def start_scheduler() -> BackgroundScheduler:
    """
    Zamanlayıcıyı başlatır.
    Her SCRAPE_INTERVAL_HOURS saatte bir tüm ürünleri kontrol eder.
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        logger.warning("Zamanlayıcı zaten çalışıyor.")
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_price_check,
        trigger=IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS),
        id="price_check_job",
        name=f"Fiyat Kontrolü (her {SCRAPE_INTERVAL_HOURS} saat)",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(f"⏰ Zamanlayıcı başlatıldı: her {SCRAPE_INTERVAL_HOURS} saatte bir kontrol yapılacak.")
    return _scheduler


def stop_scheduler() -> None:
    """Zamanlayıcıyı durdurur."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("⏹️ Zamanlayıcı durduruldu.")


def trigger_manual_check() -> list[dict]:
    """Manuel fiyat kontrolü tetikler (web arayüzünden kullanılır)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_check_all_prices())
    finally:
        loop.close()
