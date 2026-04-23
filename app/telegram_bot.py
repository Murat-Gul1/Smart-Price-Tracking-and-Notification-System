import os
import requests
import logging
from dotenv import load_dotenv

# Çevresel değişkenleri yükle
load_dotenv()

# Logger ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_telegram_notification(chat_id: str, product_name: str, product_url: str, current_price: float, target_price: float, image_url: str = None) -> bool:
    """
    Fiyat düşüşü gerçekleştiğinde kullanıcıya Telegram üzerinden bildirim gönderir.
    Eğer image_url verilmişse resimli mesaj (sendPhoto), verilmemişse düz mesaj (sendMessage) atar.
    
    Args:
        chat_id (str): Kullanıcının Telegram Chat ID'si.
        product_name (str): Ürünün adı veya başlığı.
        product_url (str): Ürünün linki.
        current_price (float): Ürünün güncel fiyatı.
        target_price (float): Kullanıcının beklediği hedef fiyat.
        image_url (str, optional): Ürünün görsel linki.
        
    Returns:
        bool: Mesaj başarıyla gönderildiyse True, aksi halde False.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("HATA: TELEGRAM_BOT_TOKEN çevresel değişkeni bulunamadı!")
        return False
        
    # Telegram API Base URL
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    # Gönderilecek Mesaj Metni (Markdown formatında)
    message_text = (
        f"🎉 *Müjde! Fiyat Düştü*\n\n"
        f"📦 *Ürün:* {product_name}\n"
        f"🎯 *Hedef Fiyat:* {target_price} TL\n"
        f"💰 *Güncel Fiyat:* {current_price} TL\n\n"
        f"🔗 [Ürüne Gitmek İçin Tıklayın]({product_url})"
    )

    try:
        if image_url:
            # Resim varsa sendPhoto endpoint'ini kullan
            api_url = f"{base_url}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "photo": image_url,
                "caption": message_text,
                "parse_mode": "Markdown"
            }
        else:
            # Resim yoksa sendMessage endpoint'ini kullan
            api_url = f"{base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }

        # Telegram sunucularına POST isteği atıyoruz
        response = requests.post(api_url, data=payload)
        response_data = response.json()

        if response_data.get("ok"):
            logger.info(f"Telegram bildirimi başarıyla gönderildi -> Chat ID: {chat_id}")
            return True
        else:
            logger.error(f"Telegram API Hatası: {response_data.get('description')}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"HATA: Telegram sunucusuna bağlanırken hata oluştu: {str(e)}")
        return False

# Test için (sadece bu dosya çalıştırıldığında çalışır)
if __name__ == "__main__":
    # Test etmek için .env dosyanızı doldurup burayı aktif edebilirsiniz
    # Chat ID'nizi Telegram'da @userinfobot veya benzeri botlardan öğrenebilirsiniz.
    # send_telegram_notification(
    #     chat_id="123456789", 
    #     product_name="Test Ürünü", 
    #     product_url="https://example.com/urun", 
    #     current_price=120.50, 
    #     target_price=150.00, 
    #     image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
    # )
    pass
