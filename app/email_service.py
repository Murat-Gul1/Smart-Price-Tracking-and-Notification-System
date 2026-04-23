import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Çevresel değişkenleri yükle
load_dotenv()

# Logger ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Çevresel değişkenlerden SMTP ayarlarını alıyoruz
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))  # SSL için 465, TLS için 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_price_drop_email(recipient_email: str, product_name: str, product_url: str, current_price: float, target_price: float) -> bool:
    """
    Fiyat düşüşü gerçekleştiğinde kullanıcıya bildirim e-postası gönderir.
    
    Args:
        recipient_email (str): Alıcının e-posta adresi.
        product_name (str): Ürünün adı veya başlığı.
        product_url (str): Ürünün linki.
        current_price (float): Ürünün güncel fiyatı.
        target_price (float): Kullanıcının beklediği hedef fiyat.
        
    Returns:
        bool: E-posta başarıyla gönderildiyse True, aksi halde False.
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.error("HATA: SENDER_EMAIL veya SENDER_PASSWORD çevresel değişkenleri ayarlanmamış!")
        return False

    # E-posta içeriğini oluştur
    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"🎉 Fiyat Düştü! Beklediğiniz ürün hedef fiyata ulaştı: {product_name}"
    msg['From'] = f"Akıllı Fiyat Takip <{SENDER_EMAIL}>"
    msg['To'] = recipient_email

    # HTML formatında e-posta gövdesi
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
          <h2 style="color: #4ade80;">Müjde! Fiyat Düştü 🎉</h2>
          <p>Merhaba,</p>
          <p>Takip ettiğiniz ürünün fiyatı beklediğiniz seviyenin altına düştü!</p>
          
          <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Ürün:</strong> {product_name}</p>
            <p><strong>Hedeflediğiniz Fiyat:</strong> {target_price} TL/USD</p>
            <p><strong>Güncel Fiyat:</strong> <span style="color: #4ade80; font-size: 1.2em; font-weight: bold;">{current_price} TL/USD</span></p>
          </div>
          
          <a href="{product_url}" style="display: inline-block; padding: 12px 24px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Ürüne Git</a>
          
          <p style="margin-top: 30px; font-size: 0.9em; color: #888;">Bu e-posta Akıllı Fiyat Takip asistanınız tarafından otomatik gönderilmiştir.</p>
        </div>
      </body>
    </html>
    """

    # İçeriği mesaja ekle
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # SMTP_PORT 465 ise SSL kullan
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
        # Değilse TLS kullan (Örn: 587)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                
        logger.info(f"Fiyat düşüş e-postası başarıyla gönderildi -> {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("HATA: E-posta kimlik doğrulaması başarısız! Lütfen Gmail Uygulama Şifrenizi (App Password) kontrol edin.")
        return False
    except Exception as e:
        logger.error(f"HATA: E-posta gönderilirken bir hata oluştu: {str(e)}")
        return False

# Test için (sadece bu dosya çalıştırıldığında çalışır)
if __name__ == "__main__":
    # Test etmek için .env dosyanızı doldurup burayı aktif edebilirsiniz
    # send_price_drop_email("alici@example.com", "Test Ürünü", "https://example.com/urun", 120.50, 150.00)
    pass
