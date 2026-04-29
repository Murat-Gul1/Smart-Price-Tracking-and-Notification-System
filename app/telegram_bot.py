"""
Telegram Bot Modülü
~~~~~~~~~~~~~~~~~~~~
Telegram üzerinden ürün takip komutları ve fiyat alarm bildirimleri.
"""

import asyncio
import logging
from typing import Optional

from telegram import Update, Bot
from telegram.error import Conflict
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HEADLESS_BROWSER
from app.logic import get_tracker
from app.scraper import ScraperError
from utils.security import validate_url

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
        logger.warning(
            "Telegram bildirimi atlandi: token_set=%s chat_id_set=%s",
            bool(TELEGRAM_BOT_TOKEN),
            bool(TELEGRAM_CHAT_ID),
        )
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
            except Exception as e:
                # Görsel gönderilemezse metin olarak gönder
                logger.warning("Telegram gorsel gonderimi basarisiz, metin deneniyor: %s", e)

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
        logger.exception(f"Telegram gonderim hatasi: {e}")
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
        "/chatid — Bildirim chat ID'sini göster\n"
        "/yardim — Bu mesajı göster\n\n"
        "🌐 Desteklenen siteler: Trendyol, Amazon.com.tr, Hepsiburada"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/yardim komutu."""
    await cmd_start(update, context)


async def cmd_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/chatid komutu — Bildirim için kullanılacak sohbet ID'sini gösterir."""
    chat = update.effective_chat
    if not chat:
        await update.message.reply_text("Chat ID okunamadı.")
        return

    await update.message.reply_text(
        "Bu sohbetin chat ID değeri:\n"
        f"`{chat.id}`\n\n"
        "Bunu .env içindeki TELEGRAM_CHAT_ID alanına yaz.",
        parse_mode="Markdown",
    )


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
        from app.services import add_tracked_product

        info = await add_tracked_product(
            url,
            target_price=target_price,
            headless=HEADLESS_BROWSER,
        )
        product_id = info["product_id"]
        result = info["scrape_result"]

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

    from app.services import acknowledge_alert, check_all_tracked_products

    alerts = await check_all_tracked_products(headless=HEADLESS_BROWSER)
    alerts_found = 0
    for alert in alerts:
        alerts_found += 1
        await update.message.reply_text(alert["message"])
        acknowledge_alert(alert)

    await update.message.reply_text(
        f"✅ Kontrol tamamlandı.\n"
        f"📊 {len(products)} ürün kontrol edildi.\n"
        f"🔔 {alerts_found} alarm tespit edildi."
    )


# ══════════════════════════════════════════════════════════
#  Bot Başlatma
# ══════════════════════════════════════════════════════════
async def telegram_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Telegram polling/handler errors with actionable details."""
    error = context.error
    if isinstance(error, Conflict):
        logger.error(
            "Telegram polling conflict: ayni bot tokeni icin baska bir getUpdates/polling "
            "istegi calisiyor. Acik python main.py sureclerini ve getUpdates sekmelerini kapat."
        )
        return

    if error:
        logger.error(
            "Telegram handler hatasi: %s",
            error,
            exc_info=(type(error), error, error.__traceback__),
        )
    else:
        logger.error("Telegram handler hatasi: bilinmeyen hata. update=%r", update)


def create_telegram_app():
    """Telegram bot uygulamasını oluşturur (başlatmadan)."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN tanımlı değil. Telegram bot devre dışı.")
        return None

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_error_handler(telegram_error_handler)

    # Komut handler'ları
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("yardim", cmd_help))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("chatid", cmd_chat_id))
    app.add_handler(CommandHandler("ekle", cmd_add))
    app.add_handler(CommandHandler("liste", cmd_list))
    app.add_handler(CommandHandler("sil", cmd_remove))
    app.add_handler(CommandHandler("kontrol", cmd_check))

    logger.info("🤖 Telegram bot oluşturuldu.")
    return app
