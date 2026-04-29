"""
Shared service layer for product tracking workflows.

Flask routes, Telegram commands, and the scheduler call this module so the
scrape -> normalize -> persist/update flow stays consistent across entrypoints.
"""

import logging

from app.logic import get_tracker
from app.scraper import ScraperError, scrape_product_url
from utils.security import generate_product_id, validate_url

logger = logging.getLogger(__name__)


def normalize_scrape_result(raw: dict | None, url: str) -> dict:
    """Normalize scraper output to the shared downstream contract."""
    raw = raw or {}
    return {
        "title": raw.get("title"),
        "price": raw.get("price"),
        "currency": raw.get("currency", "TRY"),
        "url": raw.get("url", url),
        "platform": raw.get("platform"),
        "image_url": raw.get("image_url"),
        "in_stock": raw.get("in_stock"),
        "rating": raw.get("rating"),
        "error": raw.get("error"),
    }


async def add_tracked_product(
    url: str,
    target_price: float | None = None,
    headless: bool = True,
) -> dict:
    """
    Scrape a product URL and add/update it in the tracking list.

    Raises:
        ValueError: URL validation failed.
        ScraperError: Product details could not be scraped.
    """
    is_valid, error = validate_url(url)
    if not is_valid:
        raise ValueError(error)

    raw = await scrape_product_url(url, headless=headless)
    result = normalize_scrape_result(raw, url)

    tracker = get_tracker()
    product_id = generate_product_id(url)
    tracker.add_product(
        product_id=product_id,
        url=url,
        title=result.get("title") or "",
        platform=result.get("platform") or "",
        image_url=result.get("image_url") or "",
        target_price=target_price,
        current_price=result.get("price"),
        currency=result.get("currency") or "TRY",
    )

    return {
        "product_id": product_id,
        "scrape_result": result,
        "tracker_record": tracker.get_product(product_id),
    }


async def check_all_tracked_products(headless: bool = True) -> list[dict]:
    """
    Re-scrape every tracked product and update stored prices.

    Returns the same raw alert dictionaries that PriceTracker.update_price()
    already produced before this service layer existed.
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
            raw = await scrape_product_url(url, headless=headless)
            result = normalize_scrape_result(raw, url)

            alert = tracker.update_price(
                product_id=product_id,
                new_price=result.get("price"),
                in_stock=result.get("in_stock") if result.get("in_stock") is not None else True,
                title=result.get("title") or "",
                image_url=result.get("image_url") or "",
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


def remove_tracked_product(product_id: str) -> bool:
    """Remove a tracked product."""
    tracker = get_tracker()
    return tracker.remove_product(product_id)


def list_tracked_products() -> dict:
    """Return all tracked products."""
    return get_tracker().get_all_products()


def acknowledge_alert(alert: dict) -> bool:
    """Record cooldown only after an alert was actually shown or sent."""
    if not isinstance(alert, dict):
        return False

    product_id = alert.get("product_id")
    kind = alert.get("kind")
    if not product_id or not kind:
        return False

    return get_tracker().mark_alert_sent(product_id, kind)


def acknowledge_alerts(alerts: list[dict]) -> int:
    """Record delivery for every alert that was successfully surfaced."""
    delivered = 0
    for alert in alerts:
        if acknowledge_alert(alert):
            delivered += 1
    return delivered
