"""
Telegram Bot Modülü
~~~~~~~~~~~~~~~~~~~~
Telegram üzerinden ürün takip komutları ve fiyat alarm bildirimleri.
"""

import asyncio
import logging
from typing import Optional

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HEADLESS_BROWSER
from app.logic import get_tracker
from app.scraper import scrape_product_url, ScraperError
from utils.security import validate_url, generate_product_id

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
#  Telegram Alarm Gönderimi (Scheduler'dan çağrılır)
# ══════════════════════════════════════════════════════════
async def send_telegram_alert(alert: dict) -> bool:
    """
    Fiyat alarmını Telegram'a gönderir.
    scheduler.py tarafından çağrılır.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram ayarları eksik. Bildirim gönderilmedi.")
        return False

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        message = alert.get("message", "Fiyat değişikliği tespit edildi.")
        url = alert.get("url", "")
        image_url = alert.get("image_url", "")

        # Görsel varsa, görsel ile birlikte gönder
        if image_url:
            full_caption = f"{message}\n\n🔗 {url}"
            try:
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=image_url,
                    caption=full_caption[:1024],
                    parse_mode=None,
                )
                logger.info(f"📱 Telegram bildirimi gönderildi (görsel ile).")
                return True
            except Exception:
                # Görsel gönderilemezse metin olarak gönder
                pass

        # Metin olarak gönder
        full_message = f"{message}\n\n🔗 {url}"
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=full_message,
            parse_mode=None,
        )
        logger.info(f"📱 Telegram bildirimi gönderildi.")
        return True

    except Exception as e:
        logger.error(f"Telegram gönderim hatası: {e}")
        return False


# ══════════════════════════════════════════════════════════
#  Telegram Bot Komutları
# ══════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutu — Hoş geldin mesajı."""
    welcome = (
        "🛒 *Smart Price Tracker Bot*\n\n"
        "Merhaba! E-ticaret fiyat takip botuna hoş geldin.\n\n"
        "📋 *Komutlar:*\n"
        "/ekle `<url>` — Ürün takibe al\n"
        "/ekle `<url>` `<hedef_fiyat>` — Hedef fiyatla takibe al\n"
        "/liste — Takip listesini göster\n"
        "/sil `<no>` — Ürünü takipten çıkar\n"
        "/kontrol — Manuel fiyat kontrolü\n"
        "/yardim — Bu mesajı göster\n\n"
        "🌐 Desteklenen siteler: Trendyol, Amazon.com.tr"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yardim komutu."""
    await cmd_start(update, context)


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ekle <url> [hedef_fiyat] — Ürün takibe al."""
    if not context.args:
        await update.message.reply_text("❌ Kullanım: /ekle <ürün_url> [hedef_fiyat]")
        return

    url = context.args[0]
    target_price = None

    # Hedef fiyat verilmişse
    if len(context.args) > 1:
        try:
            target_price = float(context.args[1].replace(",", "."))
        except ValueError:
            await update.message.reply_text("❌ Geçersiz hedef fiyat.")
            return

    # URL doğrula
    is_valid, error = validate_url(url)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return

    await update.message.reply_text("⏳ Ürün bilgileri alınıyor...")

    try:
        # Fiyat bilgisi çek
        result = await scrape_product_url(url, headless=HEADLESS_BROWSER)

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

        price_text = f"{result.get('price', 'N/A')} {result.get('currency', 'TRY')}"
        target_text = f"\n🎯 Hedef: {target_price} {result.get('currency', 'TRY')}" if target_price else ""

        reply = (
            f"✅ Ürün takibe alındı!\n\n"
            f"📦 {result.get('title', 'N/A')}\n"
            f"💰 Fiyat: {price_text}\n"
            f"🏪 Platform: {result.get('platform', '').capitalize()}"
            f"{target_text}"
        )

        # Görsel varsa gönder
        image_url = result.get("image_url")
        if image_url:
            try:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=reply,
                )
                return
            except Exception:
                pass

        await update.message.reply_text(reply)

    except ScraperError as e:
        await update.message.reply_text(f"❌ Ürün bilgileri alınamadı:\n{e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Beklenmeyen hata: {e}")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/liste — Takip listesini göster."""
    tracker = get_tracker()
    products = tracker.get_all_products()

    if not products:
        await update.message.reply_text("📋 Takip listeniz boş.\n/ekle komutuyla ürün ekleyebilirsiniz.")
        return

    lines = ["📋 *Takip Listeniz:*\n"]
    for i, (pid, p) in enumerate(products.items(), 1):
        title = (p.get("title", "N/A"))[:40]
        price = p.get("current_price", "N/A")
        currency = p.get("currency", "TRY")
        platform = p.get("platform", "").capitalize()
        target = p.get("target_price")
        stock = "✅" if p.get("in_stock", True) else "❌"

        line = f"{i}. {stock} *{title}*\n   💰 {price} {currency} | {platform}"
        if target:
            line += f"\n   🎯 Hedef: {target} {currency}"
        lines.append(line)

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sil <numara> — Ürünü takipten çıkar."""
    if not context.args:
        await update.message.reply_text("❌ Kullanım: /sil <sıra_numarası>")
        return

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("❌ Geçersiz numara.")
        return

    tracker = get_tracker()
    products = tracker.get_all_products()
    product_ids = list(products.keys())

    if index < 0 or index >= len(product_ids):
        await update.message.reply_text(f"❌ Geçersiz numara. 1-{len(product_ids)} arası bir değer girin.")
        return

    pid = product_ids[index]
    title = products[pid].get("title", "Ürün")
    tracker.remove_product(pid)

    await update.message.reply_text(f"🗑️ Takipten çıkarıldı: {title}")


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/kontrol — Manuel fiyat kontrolü."""
    tracker = get_tracker()
    products = tracker.get_all_products()

    if not products:
        await update.message.reply_text("📋 Takip listeniz boş.")
        return

    await update.message.reply_text(f"🔍 {len(products)} ürün kontrol ediliyor...")

    alerts_found = 0
    for pid, product in products.items():
        url = product.get("url")
        if not url:
            continue

        try:
            result = await scrape_product_url(url, headless=HEADLESS_BROWSER)
            alert = tracker.update_price(
                product_id=pid,
                new_price=result.get("price"),
                in_stock=result.get("in_stock", True),
                title=result.get("title", ""),
                image_url=result.get("image_url", ""),
            )
            if alert:
                alerts_found += 1
                await update.message.reply_text(alert["message"])

        except Exception as e:
            logger.error(f"Manuel kontrol hatası ({pid}): {e}")

    await update.message.reply_text(
        f"✅ Kontrol tamamlandı.\n"
        f"📊 {len(products)} ürün kontrol edildi.\n"
        f"🔔 {alerts_found} alarm tespit edildi."
    )


# ══════════════════════════════════════════════════════════
#  Bot Başlatma
# ══════════════════════════════════════════════════════════
def create_telegram_app():
    """Telegram bot uygulamasını oluşturur (başlatmadan)."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN tanımlı değil. Telegram bot devre dışı.")
        return None

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Komut handler'ları
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("yardim", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ekle", cmd_add))
    app.add_handler(CommandHandler("liste", cmd_list))
    app.add_handler(CommandHandler("sil", cmd_remove))
    app.add_handler(CommandHandler("kontrol", cmd_check))

    logger.info("🤖 Telegram bot oluşturuldu.")
    return app
