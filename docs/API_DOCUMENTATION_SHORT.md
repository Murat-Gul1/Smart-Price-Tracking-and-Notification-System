# Kısa API Dokümantasyonu

## 1. Kısa Proje Özeti

Smart Price Tracking and Notification System / Akıllı Fiyat Takip ve Bildirim Sistemi, e-ticaret sitelerindeki ürün fiyatlarını takip etmek, hedef fiyat belirlemek, fiyat geçmişini saklamak ve fiyat düşünce kullanıcıya bildirim göndermek için geliştirilmiş bir Python projesidir.

Kullanılan temel teknolojiler:

- Flask: Web arayüzü ve endpointler.
- Playwright + playwright-stealth: Trendyol, Amazon.com.tr ve Hepsiburada ürün bilgilerinin çekilmesi.
- APScheduler: Belirli aralıklarla otomatik fiyat kontrolü.
- python-telegram-bot: Telegram bot komutları ve Telegram bildirimi.
- Gmail SMTP: E-posta bildirimi.
- JSON dosyaları: Ürün ve fiyat geçmişi saklama.

Projede web arayüzü vardır. Kullanıcı ürün ekleyebilir, listeleyebilir, silebilir, hedef fiyat güncelleyebilir, manuel fiyat kontrolü yapabilir ve ürün karşılaştırma ekranını kullanabilir.

Telegram bot vardır. Bot ile ürün ekleme, listeleme, silme, manuel kontrol ve chat ID görüntüleme yapılabilir.

Email bildirimi vardır. Fiyat alarmı oluştuğunda Gmail SMTP ayarları yapılmışsa e-posta gönderilir.

Scheduler vardır. Uygulama başlarken arka plan zamanlayıcısı başlatılır ve ürünler `SCRAPE_INTERVAL_HOURS` değerine göre periyodik kontrol edilir. Varsayılan değer 6 saattir.

## 2. Çalıştırma ve Ortam Bilgisi

Local çalıştırma komutu:

```powershell
python main.py
```

Local base URL:

```text
http://localhost:5000
```

Port `.env` içindeki `FLASK_PORT` ile değiştirilebilir. Varsayılan port `5000` değeridir.

Gerekli veya opsiyonel `.env` değişkenleri:

| Değişken | Açıklama |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram botunu çalıştırmak için kullanılır. Boşsa bot devre dışı kalır. |
| `TELEGRAM_CHAT_ID` | Scheduler bildirimlerinin gönderileceği Telegram sohbet ID'si. |
| `GMAIL_ADDRESS` | E-posta gönderen Gmail adresi. |
| `GMAIL_APP_PASSWORD` | Gmail uygulama şifresi. |
| `NOTIFICATION_EMAIL` | Bildirim e-postasının gönderileceği alıcı adres. |
| `SCRAPE_INTERVAL_HOURS` | Otomatik fiyat kontrol aralığı. Varsayılan: `6`. |
| `HEADLESS_BROWSER` | Browser'ın arka planda çalışıp çalışmayacağı. Varsayılan: `true`. |
| `FLASK_SECRET_KEY` | Flask session/flash mesajları için gizli anahtar. |
| `FLASK_PORT` | Flask web portu. Varsayılan: `5000`. |
| `FLASK_DEBUG` | Flask debug modu. |

Gerçek token, şifre veya kişisel `.env` değerleri dokümana yazılmamalıdır.

## 3. Web Endpoint Özeti

| Method | Endpoint | Açıklama | Parametreler |
|---|---|---|---|
| `GET` | `/` | Ana takip panelini gösterir. | Yok |
| `POST` | `/add` | Formdan gelen URL ile ürünü takibe alır. | Form: `url`, opsiyonel `target_price` |
| `POST` | `/remove/<product_id>` | Ürünü takip listesinden siler. | Path: `product_id` |
| `POST` | `/target/<product_id>` | Ürün hedef fiyatını günceller. | Path: `product_id`, Form: `target_price` |
| `POST` | `/check` | Manuel fiyat kontrolü başlatır. | Yok |
| `GET` | `/api/history/<product_id>` | Ürünün fiyat geçmişini ve istatistiklerini JSON döndürür. | Path: `product_id` |
| `GET` | `/compare` | Ürün karşılaştırma sayfasını gösterir. | Yok |
| `POST` | `/compare/search` | Ürün adını Trendyol, Amazon.com.tr ve Hepsiburada'da arar. | JSON: `query` |
| `POST` | `/compare/add` | Karşılaştırma sonucundaki ürünü takip listesine ekler. | JSON: `id` veya `product_id`, `url`, `title`, `platform`, `image_url`, `price`, opsiyonel `target_price` |

## 4. Telegram Bot Komutları

| Komut | Kullanım | Açıklama |
|---|---|---|
| `/start` | `/start` | Hoş geldin mesajı ve komut listesini gönderir. |
| `/yardim` | `/yardim` | Yardım mesajını gösterir. |
| `/help` | `/help` | Yardım mesajını gösterir. |
| `/chatid` | `/chatid` | Mevcut Telegram sohbet ID'sini gösterir. |
| `/ekle` | `/ekle <url> [hedef_fiyat]` | Ürün URL'sini doğrular, ürünü scrape eder ve takip listesine ekler. |
| `/liste` | `/liste` | Takip edilen ürünleri listeler. |
| `/sil` | `/sil <sıra_numarası>` | Listedeki sıra numarasına göre ürünü takipten çıkarır. |
| `/kontrol` | `/kontrol` | Takip edilen tüm ürünler için manuel fiyat kontrolü yapar. |

## 5. Temel Servis Fonksiyonları

| Dosya | Fonksiyon | Görevi |
|---|---|---|
| `app/web.py` | `create_app()` | Flask uygulamasını ve route'ları oluşturur. |
| `app/services.py` | `add_tracked_product()` | URL doğrular, ürünü scrape eder ve takip listesine ekler. |
| `app/services.py` | `check_all_tracked_products()` | Tüm takip edilen ürünleri tekrar kontrol eder ve alarm listesi döndürür. |
| `app/services.py` | `acknowledge_alert()` / `acknowledge_alerts()` | Gösterilen veya gönderilen alarmlar için cooldown kaydı yazar. |
| `app/logic.py` | `PriceTracker.add_product()` | Ürün kaydını ekler veya günceller. |
| `app/logic.py` | `PriceTracker.remove_product()` | Ürünü ve fiyat geçmişini siler. |
| `app/logic.py` | `PriceTracker.update_price()` | Güncel fiyatı kaydeder ve alarm kontrolü yapar. |
| `app/logic.py` | `PriceTracker.set_target_price()` | Ürün hedef fiyatını günceller. |
| `app/scraper.py` | `scrape_product_url()` | Tek ürün URL'sinden ürün bilgisi çeker. |
| `app/scraper.py` | `get_scraper()` | URL domainine göre doğru scraper sınıfını seçer. |
| `app/search_engine.py` | `SearchEngine.search_all()` | Üç platformda eş zamanlı ürün araması yapar. |
| `app/telegram_bot.py` | `create_telegram_app()` | Telegram bot uygulamasını ve komut handler'larını oluşturur. |
| `app/telegram_bot.py` | `send_telegram_alert()` | Fiyat alarmını Telegram'a gönderir. |
| `app/email_service.py` | `send_price_alert_email()` | Fiyat alarmını Gmail SMTP ile e-posta olarak gönderir. |
| `app/scheduler.py` | `start_scheduler()` | Periyodik fiyat kontrol job'unu başlatır. |
| `app/scheduler.py` | `trigger_manual_check()` | Web arayüzünden manuel fiyat kontrolü çalıştırır. |
| `utils/security.py` | `validate_url()` | URL'nin geçerli ve desteklenen platforma ait olduğunu kontrol eder. |
| `utils/security.py` | `generate_product_id()` | URL'den benzersiz ürün ID'si üretir. |

## 6. Fiyat Kontrol ve Bildirim Akışı

- Kullanıcı web arayüzünden veya Telegram `/ekle` komutuyla ürün ekler.
- Sistem ürün URL'sini doğrular.
- `scrape_product_url()` ile ürün adı, fiyat, görsel, platform ve stok bilgisi çekilir.
- Ürün bilgisi `PriceTracker` ile JSON dosyasına kaydedilir.
- Kullanıcı hedef fiyat girmişse ürün kaydına `target_price` olarak eklenir.
- Manuel kontrol veya scheduler çalıştığında takipteki ürünler tekrar scrape edilir.
- Yeni fiyat eski fiyat ve hedef fiyatla karşılaştırılır.
- Fiyat hedefe ulaşırsa veya önceki fiyattan düşükse alarm oluşur.
- Scheduler alarm oluşursa e-posta ve Telegram bildirimi göndermeye çalışır.
- Web manuel kontrolde alarm sonucu flash mesajı olarak kullanıcıya gösterilir.
- Telegram `/kontrol` komutunda alarm mesajları aynı Telegram konuşmasına gönderilir.

## 7. Veri Saklama

Veri saklama JSON dosyalarıyla yapılır:

| Dosya | Açıklama |
|---|---|
| `data/products.json` | Takip edilen ürünlerin aktif kayıtlarını tutar. |
| `data/price_history.json` | Ürünlerin geçmiş fiyat kayıtlarını tutar. |

Ürün kaydında genellikle şu alanlar bulunur:

```json
{
  "url": "https://...",
  "title": "Ürün adı",
  "platform": "trendyol",
  "image_url": "https://...",
  "target_price": 1000.0,
  "current_price": 1299.99,
  "currency": "TRY",
  "added_at": "2026-04-28T12:00:00+00:00",
  "last_checked": "2026-04-28T12:00:00+00:00",
  "in_stock": true
}
```

Fiyat geçmişi kaydında genellikle `price`, `in_stock` ve `timestamp` alanları bulunur.

## 8. Kısa Sınırlamalar / Belirsiz Noktalar

- Proje tam REST API olarak değil, ağırlıklı olarak Flask HTML form tabanlı web uygulaması olarak tasarlanmıştır.
- JSON endpointleri sınırlıdır: fiyat geçmişi ve karşılaştırma ekranı için kullanılır.
- Veri saklama JSON dosyalarıyla yapıldığı için yüksek eş zamanlı kullanım veya çok kullanıcılı üretim ortamı için uygun olmayabilir.
- Scraper'lar e-ticaret sitelerinin HTML/API yapısına bağlıdır; siteler değişirse scraping başarısız olabilir.
- Telegram ve e-posta bildirimleri `.env` ayarları yapılmamışsa sessizce devre dışı kalabilir veya gönderim başarısız dönebilir.
- Scheduler varsayılan olarak 6 saatte bir çalışır; uygulama başlar başlamaz otomatik ilk kontrolü yapmaz.
