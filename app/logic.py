"""
İş Mantığı Modülü — PriceTracker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ürün takip listesi yönetimi, fiyat geçmişi ve alarm sistemi.
Veriler JSON dosyasında saklanır.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import DATA_DIR, PRODUCTS_FILE, PRICE_HISTORY_FILE

logger = logging.getLogger(__name__)


def _ensure_data_dir() -> None:
    """data/ dizinini oluşturur (yoksa)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict | list:
    """JSON dosyasını okur, yoksa varsayılan döndürür."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"JSON okuma hatası ({path}): {e}")
    return {} if "products" in str(path) else {}


def _save_json(path: Path, data) -> None:
    """JSON dosyasına yazar."""
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════
#  PriceTracker
# ══════════════════════════════════════════════════════════
class PriceTracker:
    """
    Ürün takip ve fiyat karşılaştırma motoru.

    Veri yapısı (products.json):
    {
        "product_id": {
            "url": str,
            "title": str,
            "platform": str,
            "image_url": str,
            "target_price": float | None,
            "current_price": float | None,
            "currency": str,
            "added_at": str (ISO),
            "last_checked": str (ISO) | None,
            "in_stock": bool
        }
    }

    Fiyat geçmişi (price_history.json):
    {
        "product_id": [
            {"price": float, "timestamp": str (ISO), "in_stock": bool},
            ...
        ]
    }
    """

    def __init__(self):
        _ensure_data_dir()
        self._products: dict = _load_json(PRODUCTS_FILE)
        self._history: dict = _load_json(PRICE_HISTORY_FILE)

    # ── Ürün Yönetimi ────────────────────────────────────

    def add_product(
        self,
        product_id: str,
        url: str,
        title: str = "",
        platform: str = "",
        image_url: str = "",
        target_price: Optional[float] = None,
        current_price: Optional[float] = None,
        currency: str = "TRY",
    ) -> dict:
        """
        Yeni ürün takip listesine ekler.
        Eğer zaten varsa, günceller.
        """
        now = datetime.now(timezone.utc).isoformat()

        if product_id in self._products:
            # Mevcut ürünü güncelle
            self._products[product_id].update({
                "title": title or self._products[product_id].get("title", ""),
                "image_url": image_url or self._products[product_id].get("image_url", ""),
                "current_price": current_price,
                "last_checked": now,
            })
            if target_price is not None:
                self._products[product_id]["target_price"] = target_price
            logger.info(f"Ürün güncellendi: {product_id}")
        else:
            # Yeni ürün ekle
            self._products[product_id] = {
                "url": url,
                "title": title,
                "platform": platform,
                "image_url": image_url,
                "target_price": target_price,
                "current_price": current_price,
                "currency": currency,
                "added_at": now,
                "last_checked": now if current_price else None,
                "in_stock": True,
            }
            self._history[product_id] = []
            logger.info(f"Yeni ürün eklendi: {product_id} — {title}")

        # İlk fiyat kaydını ekle
        if current_price is not None:
            self._add_price_record(product_id, current_price, True)

        self._save()
        return self._products[product_id]

    def remove_product(self, product_id: str) -> bool:
        """Ürünü takip listesinden siler."""
        if product_id in self._products:
            del self._products[product_id]
            self._history.pop(product_id, None)
            self._save()
            logger.info(f"Ürün silindi: {product_id}")
            return True
        return False

    def get_product(self, product_id: str) -> Optional[dict]:
        """Ürün bilgilerini döndürür."""
        return self._products.get(product_id)

    def get_all_products(self) -> dict:
        """Tüm takip edilen ürünleri döndürür."""
        return self._products.copy()

    def get_product_count(self) -> int:
        """Takip edilen ürün sayısını döndürür."""
        return len(self._products)

    # ── Fiyat Güncelleme ─────────────────────────────────

    def update_price(
        self,
        product_id: str,
        new_price: Optional[float],
        in_stock: bool = True,
        title: str = "",
        image_url: str = "",
    ) -> Optional[dict]:
        """
        Ürün fiyatını günceller ve alarm kontrolü yapar.

        Returns:
            dict: Alarm bilgisi (fiyat düştüyse), yoksa None
        """
        product = self._products.get(product_id)
        if not product:
            logger.warning(f"Ürün bulunamadı: {product_id}")
            return None

        old_price = product.get("current_price")
        now = datetime.now(timezone.utc).isoformat()

        # Ürün bilgilerini güncelle
        product["current_price"] = new_price
        product["last_checked"] = now
        product["in_stock"] = in_stock
        if title:
            product["title"] = title
        if image_url:
            product["image_url"] = image_url

        # Fiyat geçmişine kaydet
        if new_price is not None:
            self._add_price_record(product_id, new_price, in_stock)

        self._save()

        # Alarm kontrolü
        alert = self._check_alert(product_id, old_price, new_price)
        return alert

    def set_target_price(self, product_id: str, target_price: float) -> bool:
        """Ürünün hedef fiyatını günceller."""
        if product_id in self._products:
            self._products[product_id]["target_price"] = target_price
            self._save()
            return True
        return False

    # ── Fiyat Geçmişi ────────────────────────────────────

    def get_price_history(self, product_id: str) -> list[dict]:
        """Ürünün fiyat geçmişini döndürür."""
        return self._history.get(product_id, [])

    def get_price_stats(self, product_id: str) -> dict:
        """Fiyat istatistiklerini döndürür (min, max, ortalama)."""
        history = self.get_price_history(product_id)
        if not history:
            return {"min": None, "max": None, "avg": None, "count": 0}

        prices = [h["price"] for h in history if h.get("price") is not None]
        if not prices:
            return {"min": None, "max": None, "avg": None, "count": 0}

        return {
            "min": min(prices),
            "max": max(prices),
            "avg": round(sum(prices) / len(prices), 2),
            "count": len(prices),
        }

    # ── Alarm Kontrolü ───────────────────────────────────

    def _check_alert(
        self,
        product_id: str,
        old_price: Optional[float],
        new_price: Optional[float],
    ) -> Optional[dict]:
        """
        Fiyat alarmı kontrolü yapar.
        Şartlar:
         1. Hedef fiyatın altına düşmüşse
         2. Fiyat bir öncekine göre düşmüşse
        """
        product = self._products.get(product_id)
        if not product or new_price is None:
            return None

        target = product.get("target_price")
        alert_data = None

        # Hedef fiyat alarmı
        if target is not None and new_price <= target:
            alert_data = {
                "type": "target_reached",
                "product_id": product_id,
                "title": product.get("title", ""),
                "url": product.get("url", ""),
                "image_url": product.get("image_url", ""),
                "old_price": old_price,
                "new_price": new_price,
                "target_price": target,
                "currency": product.get("currency", "TRY"),
                "platform": product.get("platform", ""),
                "message": (
                    f"🎯 Hedef fiyata ulaşıldı!\n"
                    f"📦 {product.get('title', '')}\n"
                    f"💰 Fiyat: {new_price} {product.get('currency', 'TRY')}\n"
                    f"🎯 Hedef: {target} {product.get('currency', 'TRY')}"
                ),
            }
            logger.info(f"🎯 HEDEF ALARM: {product_id} → {new_price} ≤ {target}")

        # Fiyat düşüş alarmı
        elif old_price is not None and new_price < old_price:
            drop_pct = round((1 - new_price / old_price) * 100, 1)
            alert_data = {
                "type": "price_drop",
                "product_id": product_id,
                "title": product.get("title", ""),
                "url": product.get("url", ""),
                "image_url": product.get("image_url", ""),
                "old_price": old_price,
                "new_price": new_price,
                "drop_percentage": drop_pct,
                "currency": product.get("currency", "TRY"),
                "platform": product.get("platform", ""),
                "message": (
                    f"📉 Fiyat düştü! (%{drop_pct})\n"
                    f"📦 {product.get('title', '')}\n"
                    f"💰 {old_price} → {new_price} {product.get('currency', 'TRY')}"
                ),
            }
            logger.info(f"📉 FİYAT DÜŞÜŞ: {product_id} → {old_price} → {new_price} (-%{drop_pct})")

        return alert_data

    # ── Dahili Yardımcılar ────────────────────────────────

    def _add_price_record(self, product_id: str, price: float, in_stock: bool) -> None:
        """Fiyat geçmişine yeni kayıt ekler."""
        if product_id not in self._history:
            self._history[product_id] = []

        self._history[product_id].append({
            "price": price,
            "in_stock": in_stock,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _save(self) -> None:
        """Verileri diske yazar."""
        _save_json(PRODUCTS_FILE, self._products)
        _save_json(PRICE_HISTORY_FILE, self._history)


# ── Singleton erişim ──────────────────────────────────────
_tracker_instance: Optional[PriceTracker] = None


def get_tracker() -> PriceTracker:
    """PriceTracker singleton'ını döndürür."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PriceTracker()
    return _tracker_instance
