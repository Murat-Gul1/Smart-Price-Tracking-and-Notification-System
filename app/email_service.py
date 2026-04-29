"""
E-posta Bildirim Servisi — Gmail SMTP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fiyat düşüş ve hedef fiyat alarmlarını Gmail üzerinden gönderir.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)


def _build_alert_html(alert: dict) -> str:
    """Alarm bilgisinden HTML e-posta içeriği oluşturur."""
    alert_type = alert.get("type", "price_drop")
    title = alert.get("title", "Ürün")
    url = alert.get("url", "#")
    image_url = alert.get("image_url", "")
    old_price = alert.get("old_price", "N/A")
    new_price = alert.get("new_price", "N/A")
    currency = alert.get("currency", "TRY")
    platform = alert.get("platform", "").capitalize()

    if alert_type == "target_reached":
        header_color = "#10b981"
        header_text = "🎯 Hedef Fiyata Ulaşıldı!"
        target_price = alert.get("target_price", "N/A")
        price_info = f"""
            <p style="font-size:16px;">Hedef Fiyat: <strong>{target_price} {currency}</strong></p>
            <p style="font-size:20px; color:#10b981;">Güncel Fiyat: <strong>{new_price} {currency}</strong></p>
        """
    else:
        header_color = "#f59e0b"
        drop_pct = alert.get("drop_percentage", 0)
        header_text = f"📉 Fiyat Düştü! (%{drop_pct})"
        price_info = f"""
            <p style="font-size:16px; text-decoration:line-through; color:#888;">{old_price} {currency}</p>
            <p style="font-size:20px; color:#ef4444; font-weight:bold;">{new_price} {currency}</p>
        """

    image_section = ""
    if image_url:
        image_section = f"""
            <div style="text-align:center; margin:15px 0;">
                <img src="{image_url}" alt="{title}" style="max-width:250px; border-radius:8px; border:1px solid #e2e8f0;">
            </div>
        """

    return f"""
    <html>
    <body style="font-family:'Segoe UI',Arial,sans-serif; background:#f8fafc; margin:0; padding:20px;">
        <div style="max-width:500px; margin:auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
            <div style="background:{header_color}; padding:20px; text-align:center;">
                <h1 style="color:white; margin:0; font-size:22px;">{header_text}</h1>
            </div>
            <div style="padding:20px;">
                <h2 style="font-size:16px; color:#334155; margin:0 0 10px;">{title}</h2>
                <p style="color:#64748b; font-size:13px; margin:0 0 15px;">Platform: {platform}</p>
                {image_section}
                <div style="background:#f1f5f9; padding:15px; border-radius:8px; text-align:center;">
                    {price_info}
                </div>
                <div style="text-align:center; margin-top:20px;">
                    <a href="{url}" style="display:inline-block; background:{header_color}; color:white; padding:12px 30px; border-radius:8px; text-decoration:none; font-weight:bold;">
                        Ürünü Görüntüle
                    </a>
                </div>
            </div>
            <div style="background:#f1f5f9; padding:12px; text-align:center;">
                <p style="color:#94a3b8; font-size:11px; margin:0;">Smart Price Tracker — Otomatik Fiyat Takip</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_price_alert_email(alert: dict) -> bool:
    """
    Fiyat alarmını Gmail SMTP üzerinden e-posta olarak gönderir.

    Args:
        alert: Alarm bilgileri dict'i (logic.py'den gelir)

    Returns:
        bool: Gönderim başarılı mı
    """
    missing = []
    if not GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS")
    if not GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")
    if not NOTIFICATION_EMAIL:
        missing.append("NOTIFICATION_EMAIL")

    if missing:
        logger.info(
            f"[email] E-posta bildirimi atlandı: yapılandırma eksik "
            f"(eksik alanlar: {', '.join(missing)})"
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"💰 Fiyat Alarmı: {alert.get('title', 'Ürün')[:50]}"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = NOTIFICATION_EMAIL

        # Düz metin (fallback)
        text_content = alert.get("message", "Fiyat değişikliği tespit edildi.")
        msg.attach(MIMEText(text_content, "plain", "utf-8"))

        # HTML içerik
        html_content = _build_alert_html(alert)
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # Gmail SMTP ile gönder
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        logger.info(f"[email] E-posta gönderildi: {NOTIFICATION_EMAIL}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            f"[email] Gmail kimlik doğrulama başarısız. "
            f"App password doğru mu? GMAIL_ADDRESS: {GMAIL_ADDRESS}. Detay: {e}"
        )
        return False
    except smtplib.SMTPException as e:
        logger.error(f"[email] SMTP hatası: {e}")
        return False
    except Exception as e:
        logger.error(f"[email] Beklenmeyen e-posta hatası: {e}")
        return False
