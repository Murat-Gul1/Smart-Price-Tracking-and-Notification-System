"""
Flask Web Arayüzü
~~~~~~~~~~~~~~~~~~
Ürün ekleme/silme, fiyat geçmişi ve takip listesi yönetimi.
"""

import asyncio
import logging

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from config import FLASK_SECRET_KEY, HEADLESS_BROWSER
from app.logic import get_tracker
from app.scraper import scrape_product_url, ScraperError
from utils.security import validate_url, generate_product_id

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Flask uygulamasını oluşturur ve döndürür."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.secret_key = FLASK_SECRET_KEY

    # ── Ana Sayfa ─────────────────────────────────────

    @app.route("/")
    def index():
        """Ana sayfa — takip listesi."""
        tracker = get_tracker()
        products = tracker.get_all_products()

        # Her ürün için istatistikleri hesapla
        products_with_stats = {}
        for pid, product in products.items():
            stats = tracker.get_price_stats(pid)
            products_with_stats[pid] = {**product, "stats": stats}

        return render_template(
            "index.html",
            products=products_with_stats,
            product_count=tracker.get_product_count(),
        )

    # ── Ürün Ekleme ───────────────────────────────────

    @app.route("/add", methods=["POST"])
    def add_product():
        """Yeni ürün takibe alır."""
        url = request.form.get("url", "").strip()
        target_price_str = request.form.get("target_price", "").strip()

        # URL doğrulama
        is_valid, error = validate_url(url)
        if not is_valid:
            flash(f"❌ {error}", "error")
            return redirect(url_for("index"))

        # Hedef fiyat (opsiyonel)
        target_price = None
        if target_price_str:
            try:
                target_price = float(target_price_str.replace(",", "."))
            except ValueError:
                flash("❌ Geçersiz hedef fiyat.", "error")
                return redirect(url_for("index"))

        # Scraping
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                scrape_product_url(url, headless=HEADLESS_BROWSER)
            )
            loop.close()

            # Takip listesine ekle
            tracker = get_tracker()
            product_id = generate_product_id(url)
            tracker.add_product(
                product_id=product_id,
                url=url,
                title=result.get("title", ""),
                platform=result.get("platform", ""),
                image_url=result.get("image_url", ""),
                target_price=target_price,
                current_price=result.get("price"),
                currency=result.get("currency", "TRY"),
            )

            title = result.get("title", "Ürün")[:60]
            flash(f"✅ Takibe alındı: {title}", "success")

        except ScraperError as e:
            flash(f"❌ Ürün bilgileri alınamadı: {e}", "error")
        except Exception as e:
            flash(f"❌ Beklenmeyen hata: {e}", "error")

        return redirect(url_for("index"))

    # ── Ürün Silme ────────────────────────────────────

    @app.route("/remove/<product_id>", methods=["POST"])
    def remove_product(product_id):
        """Ürünü takipten çıkarır."""
        tracker = get_tracker()
        product = tracker.get_product(product_id)

        if product:
            title = product.get("title", "Ürün")[:60]
            tracker.remove_product(product_id)
            flash(f"🗑️ Takipten çıkarıldı: {title}", "success")
        else:
            flash("❌ Ürün bulunamadı.", "error")

        return redirect(url_for("index"))

    # ── Hedef Fiyat Güncelleme ────────────────────────

    @app.route("/target/<product_id>", methods=["POST"])
    def update_target(product_id):
        """Hedef fiyatı günceller."""
        tracker = get_tracker()
        target_str = request.form.get("target_price", "").strip()

        if not target_str:
            flash("❌ Hedef fiyat boş olamaz.", "error")
            return redirect(url_for("index"))

        try:
            target = float(target_str.replace(",", "."))
            if tracker.set_target_price(product_id, target):
                flash(f"🎯 Hedef fiyat güncellendi: {target} TL", "success")
            else:
                flash("❌ Ürün bulunamadı.", "error")
        except ValueError:
            flash("❌ Geçersiz fiyat.", "error")

        return redirect(url_for("index"))

    # ── Manuel Kontrol ────────────────────────────────

    @app.route("/check", methods=["POST"])
    def manual_check():
        """Manuel fiyat kontrolü tetikler."""
        try:
            from app.scheduler import trigger_manual_check
            alerts = trigger_manual_check()

            if alerts:
                flash(f"🔔 {len(alerts)} fiyat alarmı tespit edildi!", "success")
            else:
                flash("✅ Kontrol tamamlandı. Fiyat değişikliği yok.", "info")
        except Exception as e:
            flash(f"❌ Kontrol hatası: {e}", "error")

        return redirect(url_for("index"))

    # ── API: Fiyat Geçmişi ────────────────────────────

    @app.route("/api/history/<product_id>")
    def api_price_history(product_id):
        """Ürün fiyat geçmişini JSON olarak döndürür."""
        tracker = get_tracker()
        history = tracker.get_price_history(product_id)
        stats = tracker.get_price_stats(product_id)
        return jsonify({"history": history, "stats": stats})

    return app
