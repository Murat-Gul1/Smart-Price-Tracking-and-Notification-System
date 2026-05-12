# Smart Price Tracking and Notification System - API ve Sistem Dokümantasyonu

Bu doküman, repository içindeki mevcut kod incelenerek hazırlanmıştır. Yeni endpoint, yeni özellik veya kodda bulunmayan API eklenmemiştir. Kapsam; Flask route'ları, HTML form action'ları, JSON endpointleri, servis fonksiyonları, Telegram bot komutları, e-posta bildirimi ve scheduler akışlarıdır.

## 1. Proje API / Sistem Genel Özeti

Smart Price Tracking and Notification System, Trendyol, Amazon.com.tr ve Hepsiburada ürünlerinin fiyatlarını takip eden, fiyat geçmişini saklayan, hedef fiyat veya fiyat düşüşü olduğunda bildirim gönderen bir Python uygulamasıdır.

Kullanıcı web arayüzünden şu işlemleri yapabilir:

- Ürün URL'si ile yeni ürün takibe almak.
- Takibe alınan ürünleri listelemek.
- Ürünü takip listesinden çıkarmak.
- Ürün için hedef fiyat belirlemek veya güncellemek.
- Manuel fiyat kontrolü başlatmak.
- Ürün fiyat geçmişini JSON olarak görüntülemek.
- Karşılaştırma sayfasında ürün adını Trendyol, Amazon.com.tr ve Hepsiburada'da aratmak.
- Karşılaştırma sonucundaki ürünü takip listesine eklemek.

Backend teknolojisi Flask'tır. Uygulama giriş noktası [main.py](../main.py), Flask uygulama fabrikası ise [app/web.py](../app/web.py) içindeki `create_app()` fonksiyonudur.

Projede web arayüzü vardır:

- Ana takip paneli: [app/templates/index.html](../app/templates/index.html)
- Fiyat karşılaştırma ekranı: [app/templates/compare.html](../app/templates/compare.html)
- Ortak stil dosyası: [app/static/style.css](../app/static/style.css)

Projede Telegram bot vardır. Bot komutları ve Telegram alarm gönderimi [app/telegram_bot.py](../app/telegram_bot.py) içindedir.

Projede Gmail SMTP tabanlı e-posta bildirimi vardır. Bildirim servisi [app/email_service.py](../app/email_service.py) içindedir.

Projede APScheduler tabanlı arka plan fiyat kontrol sistemi vardır. Scheduler akışı [app/scheduler.py](../app/scheduler.py) içindedir.

Ana dosya sorumlulukları:

| Dosya | Görev |
| --- | --- |
| [main.py](../main.py) | Uygulamayı başlatır, tek instance kilidi alır, Flask, scheduler ve varsa Telegram botu çalıştırır. |
| [config.py](../config.py) | `.env` ayarlarını okur; port, scheduler aralığı, Telegram, Gmail ve scraper ayarlarını merkezileştirir. |
| [app/web.py](../app/web.py) | Flask web route'larını ve JSON endpointlerini tanımlar. |
| [app/services.py](../app/services.py) | Web, Telegram ve scheduler tarafından kullanılan ortak ürün takip servislerini sağlar. |
| [app/logic.py](../app/logic.py) | `PriceTracker` sınıfı ile ürün, fiyat geçmişi ve alarm iş kurallarını yönetir. |
| [app/scraper.py](../app/scraper.py) | Playwright + stealth tabanlı scraper sınıflarını içerir. |
| [app/search_engine.py](../app/search_engine.py) | Karşılaştırma ekranı için platformlarda arama yapar. |
| [app/telegram_bot.py](../app/telegram_bot.py) | Telegram komutları ve Telegram alarm bildirimi. |
| [app/email_service.py](../app/email_service.py) | Gmail SMTP ile fiyat alarm e-postası gönderimi. |
| [app/scheduler.py](../app/scheduler.py) | Periyodik ve manuel fiyat kontrol akışı. |
| [utils/security.py](../utils/security.py) | URL doğrulama, platform tespiti, URL temizleme, ürün ID üretimi. |
| [utils/stealth_compat.py](../utils/stealth_compat.py) | `playwright-stealth` JS script'lerini Playwright sayfasına uygular. |

## 2. Base URL ve Çalıştırma Mantığı

Varsayılan local geliştirme adresi:

```text
http://localhost:5000
```

Port [config.py](../config.py) içinde `FLASK_PORT` değişkeninden okunur. `.env` dosyasında `FLASK_PORT` verilmezse varsayılan değer `5000` kullanılır. [main.py](../main.py) Flask'ı şu ayarlarla başlatır:

```python
app.run(host="0.0.0.0", port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False)
```

Projede genel bir API prefix yoktur. Sadece fiyat geçmişi endpointi `/api/history/<product_id>` yolu altında yer alır. Karşılaştırma ekranının JSON endpointleri `/compare/search` ve `/compare/add` olarak tanımlanmıştır.

Web form endpointleri:

- `POST /add`
- `POST /remove/<product_id>`
- `POST /target/<product_id>`
- `POST /check`

JSON dönen endpointler:

- `GET /api/history/<product_id>`
- `POST /compare/search`
- `POST /compare/add`

HTML sayfa endpointleri:

- `GET /`
- `GET /compare`

Bu proje klasik anlamda tam REST API olarak tasarlanmamıştır. Ana ürün yönetimi HTML form tabanlıdır; karşılaştırma ekranında JavaScript `fetch()` ile çağrılan JSON endpointleri de vardır.

## 3. Web Endpointleri / Route Dokümantasyonu

### Ana Sayfa

- Method: `GET`
- URL: `/`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `index`
- Kullanıcı arayüzünde ne işe yarar: Takip edilen ürünleri, fiyat istatistiklerini ve ürün ekleme formunu gösterir.
- Request parametreleri: Yok.
- Form alanları veya JSON body: Yok.
- Örnek request:

```http
GET / HTTP/1.1
Host: localhost:5000
```

- Örnek response veya yönlendirme: `index.html` render edilir. Template'e `products` ve `product_count` gönderilir.
- Olası hata durumları: Route içinde özel hata dönüşü yoktur. Veri dosyası bozuksa [app/logic.py](../app/logic.py) JSON okuma hatasını loglar ve boş yapı dönebilir.
- Bağlı olduğu servis/fonksiyonlar: `get_tracker()`, `PriceTracker.get_all_products()`, `PriceTracker.get_price_stats()`, `PriceTracker.get_product_count()`.

### Ürün Ekleme

- Method: `POST`
- URL: `/add`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `add_product`
- Kullanıcı arayüzünde ne işe yarar: Ana sayfadaki formdan ürün URL'sini ve opsiyonel hedef fiyatı alıp ürünü takip listesine ekler.
- Request parametreleri: Query parametresi yoktur.
- Form alanları:
  - `url`: Zorunlu ürün URL'si.
  - `target_price`: Opsiyonel hedef fiyat. Virgül veya nokta ondalık ayırıcı olarak kabul edilir.
- JSON body: Yok.
- Örnek request:

```http
POST /add HTTP/1.1
Host: localhost:5000
Content-Type: application/x-www-form-urlencoded

url=https%3A%2F%2Fwww.trendyol.com%2Fornek%2Furun-p-123&target_price=1000
```

- Örnek response veya yönlendirme: Başarılı veya hatalı flash mesajı yazılır ve `/` adresine redirect edilir.
- Olası hata durumları:
  - URL boşsa veya `http://` / `https://` ile başlamıyorsa hata mesajı.
  - Domain desteklenmiyorsa hata mesajı.
  - Hedef fiyat parse edilemiyorsa hata mesajı.
  - Scraper ürün bilgilerini alamazsa `ScraperError` yakalanır.
  - Beklenmeyen hatalar flash mesajı olarak gösterilir.
- Bağlı olduğu servis/fonksiyonlar: `validate_url()`, `add_tracked_product()`, `scrape_product_url()`, `PriceTracker.add_product()`.

### Ürün Silme

- Method: `POST`
- URL: `/remove/<product_id>`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `remove_product`
- Kullanıcı arayüzünde ne işe yarar: Takip listesindeki ürünü siler. Ana sayfada ürün kartındaki "Çıkar" formu bu endpointi çağırır.
- Request parametreleri:
  - `product_id`: URL path parametresi. Ürün ID'sidir.
- Form alanları veya JSON body: Yok.
- Örnek request:

```http
POST /remove/abc123def456 HTTP/1.1
Host: localhost:5000
```

- Örnek response veya yönlendirme: Ürün varsa silinir, flash mesajı yazılır ve `/` adresine redirect edilir.
- Olası hata durumları: Ürün bulunamazsa "Ürün bulunamadı" flash mesajı.
- Bağlı olduğu servis/fonksiyonlar: `get_tracker()`, `PriceTracker.get_product()`, `PriceTracker.remove_product()`.

### Hedef Fiyat Güncelleme

- Method: `POST`
- URL: `/target/<product_id>`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `update_target`
- Kullanıcı arayüzünde ne işe yarar: Mevcut ürünün hedef fiyatını günceller.
- Request parametreleri:
  - `product_id`: URL path parametresi.
- Form alanları:
  - `target_price`: Zorunlu hedef fiyat.
- JSON body: Yok.
- Örnek request:

```http
POST /target/abc123def456 HTTP/1.1
Host: localhost:5000
Content-Type: application/x-www-form-urlencoded

target_price=899.90
```

- Örnek response veya yönlendirme: Başarı/hata flash mesajı yazılır ve `/` adresine redirect edilir.
- Olası hata durumları:
  - `target_price` boşsa hata.
  - Sayıya çevrilemiyorsa hata.
  - `product_id` bulunamazsa hata.
- Bağlı olduğu servis/fonksiyonlar: `PriceTracker.set_target_price()`.

### Manuel Fiyat Kontrolü

- Method: `POST`
- URL: `/check`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `manual_check`
- Kullanıcı arayüzünde ne işe yarar: Ana sayfadaki "Manuel Kontrol" butonu ile takipteki ürünlerin fiyatını hemen kontrol eder.
- Request parametreleri: Yok.
- Form alanları veya JSON body: Yok.
- Örnek request:

```http
POST /check HTTP/1.1
Host: localhost:5000
```

- Örnek response veya yönlendirme: Kontrol sonucu flash mesajı yazılır ve `/` adresine redirect edilir.
- Olası hata durumları: Kontrol sırasında hata oluşursa flash mesajı olarak gösterilir.
- Bağlı olduğu servis/fonksiyonlar: `trigger_manual_check()`, `_check_all_prices()`, `check_all_tracked_products()`, `acknowledge_alerts()`.
- Önemli not: Web üzerinden manuel kontrolde alarm bulunursa `acknowledge_alerts()` çağrılır. Bu, alarmın kullanıcıya arayüzde gösterildiğini kabul edip cooldown kaydını yazar. Scheduler ise cooldown kaydını yalnızca e-posta veya Telegram bildirimi başarıyla gönderilirse yazar.

### Fiyat Geçmişi API

- Method: `GET`
- URL: `/api/history/<product_id>`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `api_price_history`
- Kullanıcı arayüzünde ne işe yarar: Ürünün fiyat geçmişini ve istatistiklerini JSON olarak döndürür. Mevcut template içinde doğrudan çağıran bir JavaScript kodu görünmemektedir, ancak route aktiftir.
- Request parametreleri:
  - `product_id`: URL path parametresi.
- Form alanları veya JSON body: Yok.
- Örnek request:

```http
GET /api/history/abc123def456 HTTP/1.1
Host: localhost:5000
```

- Örnek response:

```json
{
  "history": [
    {
      "price": 1299.99,
      "in_stock": true,
      "timestamp": "2026-04-28T12:00:00+00:00"
    }
  ],
  "stats": {
    "min": 1299.99,
    "max": 1299.99,
    "avg": 1299.99,
    "count": 1
  }
}
```

- Olası hata durumları: Ürün yoksa özel HTTP hata kodu dönmez; `history` boş liste, `stats` boş istatistik yapısı olabilir.
- Bağlı olduğu servis/fonksiyonlar: `PriceTracker.get_price_history()`, `PriceTracker.get_price_stats()`.

### Karşılaştırma Sayfası

- Method: `GET`
- URL: `/compare`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `compare`
- Kullanıcı arayüzünde ne işe yarar: Trendyol, Amazon.com.tr ve Hepsiburada arama sonuçlarını karşılaştıran HTML sayfasını gösterir.
- Request parametreleri: Yok.
- Form alanları veya JSON body: Yok.
- Örnek request:

```http
GET /compare HTTP/1.1
Host: localhost:5000
```

- Örnek response veya yönlendirme: `compare.html` render edilir.
- Olası hata durumları: Route içinde özel hata dönüşü yoktur.
- Bağlı olduğu servis/fonksiyonlar: Template tarafında JavaScript ile `/compare/search` ve `/compare/add` çağrılır.

### Karşılaştırma Arama

- Method: `POST`
- URL: `/compare/search`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `compare_search`
- Kullanıcı arayüzünde ne işe yarar: Karşılaştırma ekranında girilen ürün adını üç platformda arar ve JSON sonuç döndürür.
- Request parametreleri: Yok.
- JSON body:
  - `query`: Zorunlu arama metni. Boş veya sadece whitespace olamaz.
- Örnek request:

```http
POST /compare/search HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "query": "iPhone 15"
}
```

- Örnek response:

```json
{
  "results": {
    "trendyol": [
      {
        "id": "abc123def456",
        "title": "Ürün adı",
        "price": 42999.0,
        "currency": "TRY",
        "url": "https://www.trendyol.com/...",
        "image_url": "https://...",
        "platform": "trendyol",
        "in_stock": true
      }
    ],
    "amazon": [],
    "hepsiburada": []
  },
  "lowest_price_id": "abc123def456",
  "query": "iPhone 15",
  "searched_at": "2026-05-12T05:00:00+00:00"
}
```

- Olası hata durumları:
  - Geçersiz sorgu: `400` ve `{"error": "..."}`
  - Arama sırasında beklenmeyen hata: `500` ve `{"error": "..."}`
  - Tek platform hatası: `SearchEngine.search_all()` içinde ilgili platform sonucu `{"error": "...", "results": []}` olabilir; diğer platformlar etkilenmez.
- Bağlı olduğu servis/fonksiyonlar: `validate_search_query()`, `SearchEngine.search_all()`, `SearchEngine.search_platform()`, platform scraper'larının `search_products()` fonksiyonları.

### Karşılaştırmadan Ürün Ekleme

- Method: `POST`
- URL: `/compare/add`
- Dosya: [app/web.py](../app/web.py)
- Fonksiyon adı: `compare_add`
- Kullanıcı arayüzünde ne işe yarar: Karşılaştırma sonuç kartındaki "Takibe Al" butonu ile ürünün takip listesine eklenmesini sağlar.
- Request parametreleri: Yok.
- JSON body:
  - `product_id` veya `id`: Opsiyonel. Yoksa `url` üzerinden `generate_product_id()` ile üretilir.
  - `url`: Zorunlu ürün URL'si.
  - `title`: Ürün başlığı.
  - `platform`: Platform adı.
  - `image_url`: Ürün görseli.
  - `price`: Güncel fiyat.
  - `target_price`: Opsiyonel hedef fiyat.
- Örnek request:

```http
POST /compare/add HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "id": "abc123def456",
  "title": "Ürün adı",
  "url": "https://www.amazon.com.tr/...",
  "price": 1299.99,
  "currency": "TRY",
  "platform": "amazon",
  "image_url": "https://...",
  "target_price": 1000
}
```

- Örnek response:

```json
{
  "success": true,
  "message": "Ürün takibe alındı: Ürün adı"
}
```

- Olası hata durumları:
  - JSON body yoksa `400`.
  - `product_id`/`id` ve `url` birlikte üretilemeyecek durumdaysa `400`.
  - Kaydetme sırasında hata oluşursa `500`.
- Bağlı olduğu servis/fonksiyonlar: `generate_product_id()`, `get_tracker()`, `PriceTracker.add_product()`.
- Önemli not: Bu endpoint, `/add` gibi canlı scrape yapmaz. Karşılaştırma arama sonucunda gelen başlık/fiyat/görsel bilgilerini doğrudan takip kaydına yazar.

## 4. Ürün Takip Akışı

### Web üzerinden ürün ekleme

1. Kullanıcı ana sayfadaki formdan `url` ve opsiyonel `target_price` gönderir.
2. `POST /add` içinde `validate_url()` ile URL doğrulanır.
3. `add_tracked_product()` çağrılır.
4. `scrape_product_url()` URL'ye uygun scraper'ı seçer ve ürün bilgilerini çeker.
5. `generate_product_id(url)` ile URL'den 12 karakterlik ürün ID'si üretilir.
6. `PriceTracker.add_product()` ürün kaydını `data/products.json` içine yazar.
7. Fiyat varsa `data/price_history.json` içine ilk fiyat kaydı eklenir.
8. Kullanıcı ana sayfaya yönlendirilir.

### Telegram üzerinden ürün ekleme

1. Kullanıcı `/ekle <url> [hedef_fiyat]` komutunu gönderir.
2. Komut `cmd_add()` tarafından işlenir.
3. URL doğrulanır, hedef fiyat parse edilir.
4. `add_tracked_product()` aynı web akışındaki ortak servis olarak kullanılır.
5. Başarı durumunda kullanıcıya metin veya ürün görseliyle yanıt gönderilir.

### Hedef fiyat

Hedef fiyat şu yerlerden girilebilir:

- Ana sayfadaki ürün ekleme formu: `target_price`
- Ana sayfadaki hedef fiyat güncelleme formu: `POST /target/<product_id>`
- Telegram komutu: `/ekle <url> [hedef_fiyat]`
- Karşılaştırma modalı: `/compare/add` JSON body içindeki `target_price`

Hedef fiyat `products.json` içinde ürün kaydının `target_price` alanında tutulur.

### Veri saklama

Aktif takip listesi:

```text
data/products.json
```

Fiyat geçmişi:

```text
data/price_history.json
```

Proje SQLite, CSV veya uzak veritabanı kullanmaz. Veri saklama JSON dosyaları ile yapılır.

### Fiyat çekme

Fiyat çekme [app/scraper.py](../app/scraper.py) içindeki Playwright tabanlı scraper'lar ile yapılır. Desteklenen platformlar:

- `trendyol`
- `amazon`
- `hepsiburada`

URL'nin hangi platforma ait olduğu [utils/security.py](../utils/security.py) içindeki `detect_platform()` ile belirlenir.

### Alarm üretme

`PriceTracker.update_price()` yeni fiyatı kaydeder ve `_check_alert()` ile alarm kontrolü yapar. Alarm iki durumda üretilir:

- `target_reached`: Yeni fiyat hedef fiyata eşit veya hedef fiyatın altındaysa.
- `price_drop`: Yeni fiyat önceki fiyattan düşükse.

Alarm yapısında ürün ID'si, başlık, URL, eski fiyat, yeni fiyat, hedef fiyat, platform, para birimi ve kullanıcıya gösterilecek mesaj bulunur.

### Manuel kontrol ve otomatik kontrol farkı

Manuel kontrol:

- Web: `POST /check` -> `trigger_manual_check()`
- Telegram: `/kontrol` -> `check_all_tracked_products()`
- Kullanıcı isteğiyle hemen çalışır.

Otomatik kontrol:

- `start_scheduler()` ile APScheduler job'u başlatılır.
- Varsayılan olarak her `SCRAPE_INTERVAL_HOURS` saatte bir çalışır.
- Varsayılan değer `.env.example` ve [config.py](../config.py) içinde `6` saattir.
- Scheduler alarm bulursa e-posta ve Telegram bildirimi göndermeye çalışır.

## 5. Scraper API / Fonksiyon Dokümantasyonu

Scraper katmanı [app/scraper.py](../app/scraper.py) içindedir. HTTP istekleri doğrudan `requests` ile yapılmaz; Playwright browser otomasyonu kullanılır. Trendyol için bazı durumlarda Playwright browser context'i üzerinden dahili API çağrısı yapılır.

Desteklenen siteler:

- Trendyol: `trendyol.com`, `www.trendyol.com`
- Amazon Türkiye: `amazon.com.tr`, `www.amazon.com.tr`
- Hepsiburada: `hepsiburada.com`, `www.hepsiburada.com`

### Ortak anti-ban / anti-bot ayarları

`StealthScraper.launch()` şu önlemleri kullanır:

- Rastgele `User-Agent` havuzu.
- Chromium launch argümanları: `--disable-blink-features=AutomationControlled`, `--no-sandbox`, `--disable-infobars` vb.
- Locale: `tr-TR`
- Timezone: `Europe/Istanbul`
- Ek HTTP header'ları: `Accept-Language`, `Accept-Encoding`, `Accept`, `Sec-Fetch-*`, `Upgrade-Insecure-Requests`
- `playwright-stealth` script'leri.
- `navigator.webdriver`, `window.chrome`, permissions, plugins ve languages gibi alanları taklit eden init script.
- İnsan davranışına yakın rastgele bekleme: `_human_delay()`
- Sayfa kaydırma: `_scroll_page()`

[utils/security.py](../utils/security.py) içinde `RateLimiter` ve `scraper_rate_limiter` tanımlıdır; ancak mevcut scraper akışında bu global limiter çağrılmamaktadır. Scraper tarafındaki fiili bekleme, `_human_delay()` ve toplu scraping'deki `delay_between` ile yapılır.

### `_parse_price_value(value)`

- Parametreler: `value`
- Dönen değer: `float | None`
- Kullanıldığı yerler: Platform fiyat parser'ları, JSON-LD parser, rating parse işlemlerinde.
- Hata davranışı: Parse edilemeyen, boş veya makul aralık dışında kalan değerlerde `None` döner.
- Açıklama: `1.299,99 TL`, `1299,99`, `1.299` gibi Türkçe fiyat formatlarını float değere çevirir.

### `_parse_schema_product(page)`

- Parametreler: `page`
- Dönen değer: `dict | None`
- Kullanıldığı yerler: Trendyol ve Hepsiburada detay sayfası parsing fallback akışları.
- Hata davranışı: JSON-LD okunamaz veya parse edilemezse `None` döner.
- Açıklama: Sayfadaki `script[type="application/ld+json"]` bloklarından Schema.org `Product` verisi arar.

### `StealthScraper`

Soyut temel scraper sınıfıdır. Platform scraper'ları bu sınıftan türetilir.

Önemli fonksiyonlar:

| Fonksiyon | Parametreler | Dönen değer | Açıklama |
| --- | --- | --- | --- |
| `launch()` | Yok | `None` | Playwright Chromium browser ve context başlatır. |
| `_create_stealth_page()` | Yok | `Page` | Stealth script uygulanmış yeni sayfa oluşturur. |
| `close()` | Yok | `None` | Browser/context/playwright kaynaklarını kapatır. |
| `_human_delay(min_sec, max_sec)` | Minimum ve maksimum saniye | `None` | Rastgele bekler. |
| `_scroll_page(page)` | Playwright page | `None` | Sayfayı birkaç kez kaydırır. |
| `scrape_product(url)` | Ürün URL'si | `dict` | URL'ye gider, platform `parse_product()` fonksiyonunu çağırır ve ortak meta alanları ekler. |
| `parse_product(page)` | Playwright page | `dict` | Abstract method. Her platform kendisi uygular. |

`scrape_product()` hata alırsa `ScraperError` fırlatır.

### `TrendyolScraper`

- Platform adı: `trendyol`
- Desteklediği detay URL'leri: `trendyol.com` domaini ve `-p-<id>` formatındaki ürün URL'leri.

Önemli fonksiyonlar:

| Fonksiyon | Parametreler | Dönen değer | Hata davranışı |
| --- | --- | --- | --- |
| `_extract_content_id(url)` | URL | `str | None` | URL içinde `-p-123` formatı yoksa `None`. |
| `parse_product(page)` | Playwright page | `dict` | API/fragment/JSON-LD başarısızsa fallback parse sonucu döner. |
| `_fetch_from_api(page, content_id)` | Page, content ID | `dict | None` | Fragment veya API başarısızsa `None`. |
| `_parse_fragment_data(fragment_data, content_id)` | Fragment dict, content ID | `dict | None` | Uygun ürün verisi yoksa `None`. |
| `_parse_api_response(result)` | Trendyol API result objesi | `dict | None` | Eksik alanlarda varsayılan/None alanlar. |
| `_fallback_parse(page)` | Page | `dict` | Başlık bulunamazsa `"Başlık bulunamadı"`, fiyat bulunamazsa `None`. |
| `search_products(page, query)` | Page, arama sorgusu | `list[dict]` | Cloudflare veya parse hatalarında boş liste dönebilir. |

Trendyol ürün bilgisi çıkarma sırası:

1. URL'den content ID çıkarılır.
2. Sayfadaki micro-frontend fragment verisi okunmaya çalışılır.
3. Browser context üzerinden Trendyol dahili API endpointleri denenir.
4. JSON-LD Product verisi denenir.
5. Page title, meta description ve `og:image` üzerinden fallback yapılır.

### `AmazonScraper`

- Platform adı: `amazon`
- Desteklediği domain: `amazon.com.tr`

Önemli fonksiyonlar:

| Fonksiyon | Parametreler | Dönen değer | Hata davranışı |
| --- | --- | --- | --- |
| `parse_product(page)` | Page | `dict` | CAPTCHA varsa reload dener; alan bulunamazsa `None` veya varsayılan değerler döner. |
| `_check_captcha(page)` | Page | `bool` | Kontrol sırasında hata olursa `False`. |
| `_extract_price(page)` | Page | `float | None` | Fiyat bulunamazsa `None`. |
| `_get_image_url(page)` | Page | `str | None` | Görsel bulunamazsa `None`. |
| `_check_stock(page)` | Page | `bool` | Sepete ekle veya availability metnine göre karar verir. |
| `_get_text(page, selector)` | Page, CSS selector | `str | None` | Selector bulunamazsa `None`. |
| `search_products(page, query)` | Page, arama sorgusu | `list[dict]` | CAPTCHA veya parse hatalarında boş/eksik sonuç dönebilir. |
| `_parse_price_text(text)` | Fiyat metni | `float | None` | Parse edilemezse `None`. |
| `_parse_rating(text)` | Rating metni | `float | None` | Parse edilemezse `None`. |

Amazon fiyat çekme sırası:

1. Deal/our price/offscreen fiyat blokları.
2. `a-price-whole` ve `a-price-fraction` alanlarını birleştirme.
3. Bulunamazsa `None`.

### `HepsiburadaScraper`

- Platform adı: `hepsiburada`
- Desteklediği domain: `hepsiburada.com`

Önemli fonksiyonlar:

| Fonksiyon | Parametreler | Dönen değer | Hata davranışı |
| --- | --- | --- | --- |
| `parse_product(page)` | Page | `dict` | CAPTCHA/güvenlik algılanırsa `error: "security"` içeren boş sonuç döner. |
| `search_products(page, query)` | Page, arama sorgusu | `list[dict]` | Güvenlik sayfası veya parse hatasında boş liste dönebilir. |
| `_check_captcha(page)` | Page | `bool` | Hata olursa `False`. |
| `_extract_price(page)` | Page | `float | None` | Fiyat bulunamazsa `None`. |
| `_get_image_url(page)` | Page | `str | None` | Görsel bulunamazsa `None`. |
| `_check_stock(page)` | Page | `bool` | Sepete ekle butonu varsa `True`, yoksa `False`. |
| `_get_text(page, selector)` | Page, çoklu CSS selector | `str | None` | Selector bulunamazsa `None`. |
| `_parse_price_text(text)` | Fiyat metni | `float | None` | Parse edilemezse `None`. |

Hepsiburada detay parsing önce CAPTCHA/güvenlik kontrolü yapar, sonra JSON-LD Product verisini dener, sonra CSS selector'larla başlık/fiyat/görsel/stok alanlarını çıkarır.

### `get_scraper(url, headless=True)`

- Parametreler:
  - `url`: Ürün URL'si.
  - `headless`: Browser'ın görünmeden çalışıp çalışmayacağı.
- Dönen değer: `StealthScraper` alt sınıfı.
- Kullanıldığı yerler: `scrape_product_url()`.
- Hata davranışı: Platform desteklenmiyorsa `ValueError` fırlatır.

### `scrape_product_url(url, headless=True)`

- Parametreler:
  - `url`: Ürün URL'si.
  - `headless`: Browser modu.
- Dönen değer: Ürün bilgisi dict'i.
- Kullanıldığı yerler: `add_tracked_product()`, `check_all_tracked_products()`.
- Hata davranışı: Scraper hatası varsa `ScraperError` yukarı taşınabilir.
- Özel davranış: Headless sonuç yetersizse ve platform `trendyol` veya `hepsiburada` ise headed/offscreen retry denenir.

### `scrape_multiple_urls(urls, headless=True, delay_between=(3.0, 7.0))`

- Parametreler:
  - `urls`: Ürün URL listesi.
  - `headless`: Browser modu.
  - `delay_between`: Aynı platformdaki istekler arası rastgele bekleme aralığı.
- Dönen değer: Sonuç dict listesi.
- Kullanıldığı yerler: Mevcut web route'larında doğrudan kullanılmıyor; scraper yardımcı fonksiyonudur.
- Hata davranışı: Desteklenmeyen platform veya scrape hatasında ilgili URL için hata içeren dict ekler.

## 6. Logic / İş Kuralları

İş kuralları [app/logic.py](../app/logic.py) içindeki `PriceTracker` sınıfında ve [app/services.py](../app/services.py) servis katmanında toplanmıştır.

### `PriceTracker.add_product(...)`

- Parametreler: `product_id`, `url`, `title`, `platform`, `image_url`, `target_price`, `current_price`, `currency`
- Dönen değer: Eklenen veya güncellenen ürün dict'i.
- Görevi: Ürünü takip listesine ekler. Aynı `product_id` zaten varsa başlık/görsel/güncel fiyat gibi alanları günceller.
- Fiyat geçmişi: `current_price` varsa `_add_price_record()` ile fiyat geçmişine kayıt ekler.
- Duplicate URL kontrolü: Ayrı bir "duplicate URL" listesi yoktur; aynı URL aynı `generate_product_id()` değerini ürettiği için aynı kayıt güncellenir.

### `PriceTracker.remove_product(product_id)`

- Parametreler: `product_id`
- Dönen değer: `bool`
- Görevi: Ürünü `products.json` içinden siler, aynı ürünün fiyat geçmişini de `price_history.json` içinden kaldırır.

### `PriceTracker.get_product(product_id)`

- Parametreler: `product_id`
- Dönen değer: `dict | None`
- Görevi: Tek ürün kaydını döndürür.

### `PriceTracker.get_all_products()`

- Parametreler: Yok.
- Dönen değer: Ürün dict kopyası.
- Görevi: Tüm takip listesini döndürür.

### `PriceTracker.get_product_count()`

- Parametreler: Yok.
- Dönen değer: `int`
- Görevi: Takip edilen ürün sayısını döndürür.

### `PriceTracker.update_price(...)`

- Parametreler: `product_id`, `new_price`, `in_stock`, `title`, `image_url`
- Dönen değer: Alarm dict'i veya `None`.
- Görevi: Ürünün güncel fiyatını, son kontrol zamanını, stok bilgisini ve varsa başlık/görselini günceller. Fiyat varsa geçmişe kayıt ekler. Sonra `_check_alert()` çağırır.
- Hata davranışı: Ürün bulunamazsa log yazar ve `None` döner.

### `PriceTracker.set_target_price(product_id, target_price)`

- Parametreler: `product_id`, `target_price`
- Dönen değer: `bool`
- Görevi: Ürün hedef fiyatını günceller.
- Hata davranışı: Ürün yoksa `False` döner.

### `PriceTracker.mark_alert_sent(product_id, kind)`

- Parametreler: `product_id`, `kind`
- Dönen değer: `bool`
- Görevi: Alarmın gerçekten kullanıcıya gösterildiğini/gönderildiğini kaydeder. `last_alert_at` ve `last_alert_kind` alanlarını yazar.

### `PriceTracker.get_price_history(product_id)`

- Parametreler: `product_id`
- Dönen değer: `list[dict]`
- Görevi: Ürün fiyat geçmişini döndürür.

### `PriceTracker.get_price_stats(product_id)`

- Parametreler: `product_id`
- Dönen değer: `{"min": ..., "max": ..., "avg": ..., "count": ...}`
- Görevi: Fiyat geçmişinden minimum, maksimum, ortalama ve kayıt sayısı üretir.

### `PriceTracker._check_alert(product_id, old_price, new_price)`

- Parametreler: `product_id`, `old_price`, `new_price`
- Dönen değer: Alarm dict'i veya `None`.
- Görevi: Hedef fiyat ve fiyat düşüşü alarmını üretir.
- Cooldown davranışı: Aynı alarm türü için son 6 saat içinde `mark_alert_sent()` ile kayıt yazıldıysa alarm bastırılır. Süre `SUPPRESS_WINDOW_HOURS = 6`.

### `PriceTracker._is_suppressed(product, kind)`

- Parametreler: Ürün dict'i, alarm türü (`target` veya `drop`)
- Dönen değer: `bool`
- Görevi: Aynı alarm türünün 6 saatlik bastırma penceresinde olup olmadığını kontrol eder.

### `normalize_scrape_result(raw, url)`

- Dosya: [app/services.py](../app/services.py)
- Parametreler: Scraper sonucu ve kaynak URL.
- Dönen değer: Ortak alanlara normalize edilmiş dict.
- Görevi: Scraper çıktısını `title`, `price`, `currency`, `url`, `platform`, `image_url`, `in_stock`, `rating`, `error` alanlarıyla standart hale getirir.

### `add_tracked_product(url, target_price=None, headless=True)`

- Dosya: [app/services.py](../app/services.py)
- Parametreler: Ürün URL'si, opsiyonel hedef fiyat, browser modu.
- Dönen değer:

```json
{
  "product_id": "...",
  "scrape_result": {},
  "tracker_record": {}
}
```

- Görevi: URL doğrular, ürünü scrape eder, ürünü takip listesine ekler/günceller.
- Hata davranışı: Geçersiz URL için `ValueError`, scrape hatası için `ScraperError`.

### `check_all_tracked_products(headless=True)`

- Dosya: [app/services.py](../app/services.py)
- Parametreler: Browser modu.
- Dönen değer: Alarm dict listesi.
- Görevi: Tüm takip edilen ürünleri tekrar scrape eder, fiyatları günceller, oluşan alarmları döndürür.
- Hata davranışı: Tek ürün hatası loglanır; diğer ürünlerin kontrolüne devam edilir.

### `remove_tracked_product(product_id)` ve `list_tracked_products()`

- Dosya: [app/services.py](../app/services.py)
- Görevi: `PriceTracker` üstünden silme ve listeleme için basit servis fonksiyonlarıdır.
- Not: Mevcut Flask route'ları bu iki fonksiyonu doğrudan kullanmıyor; route içinde `PriceTracker` çağrısı vardır.

### `acknowledge_alert(alert)` ve `acknowledge_alerts(alerts)`

- Dosya: [app/services.py](../app/services.py)
- Görevi: Alarm kullanıcıya ulaştıktan sonra cooldown kaydı yazar.
- Kullanıldığı yerler: Web manuel kontrol, Telegram manuel kontrol, scheduler bildirim gönderimi sonrası.

### URL doğrulama iş kuralları

[utils/security.py](../utils/security.py) içindeki `validate_url()` şu kontrolleri yapar:

- URL boş olamaz.
- URL string olmalıdır.
- `http://` veya `https://` ile başlamalıdır.
- Geçerli domain içermelidir.
- Domain desteklenen domain listesinde olmalıdır.

Desteklenen domain eşleşmeleri:

```python
{
  "trendyol.com": "trendyol",
  "www.trendyol.com": "trendyol",
  "amazon.com.tr": "amazon",
  "www.amazon.com.tr": "amazon",
  "hepsiburada.com": "hepsiburada",
  "www.hepsiburada.com": "hepsiburada"
}
```

## 7. Telegram Bot Komutları

Telegram bot kodu [app/telegram_bot.py](../app/telegram_bot.py) içindedir. Bot uygulaması `create_telegram_app()` ile oluşturulur. [main.py](../main.py), `TELEGRAM_BOT_TOKEN` varsa botu ayrı daemon thread içinde `run_polling()` ile başlatır.

Gerekli `.env` değişkenleri:

- `TELEGRAM_BOT_TOKEN`: Botun çalışması için gereklidir.
- `TELEGRAM_CHAT_ID`: Scheduler fiyat alarm bildirimlerinin hangi sohbete gönderileceğini belirtir.

### `/start`

- Komut adı: `/start`
- Kullanım formatı: `/start`
- Örnek kullanım: `/start`
- Ne yapar: Hoş geldin mesajı ve komut listesini gönderir.
- Hangi servis/fonksiyonu çağırır: `cmd_start()`
- Başarılı cevap örneği: Bot, ürün ekleme, listeleme, silme, kontrol, chat ID ve yardım komutlarını içeren açıklama gönderir.
- Hata cevap örneği: Fonksiyon içinde özel hata mesajı yoktur; handler hatası `telegram_error_handler()` ile loglanır.

### `/yardim` ve `/help`

- Komut adı: `/yardim`, `/help`
- Kullanım formatı: `/yardim`
- Örnek kullanım: `/help`
- Ne yapar: `/start` ile aynı yardım mesajını gönderir.
- Hangi servis/fonksiyonu çağırır: `cmd_help()`, içeride `cmd_start()`
- Başarılı cevap örneği: Komut listesi.
- Hata cevap örneği: Özel hata mesajı yoktur.

### `/chatid`

- Komut adı: `/chatid`
- Kullanım formatı: `/chatid`
- Örnek kullanım: `/chatid`
- Ne yapar: Mevcut sohbetin Telegram chat ID değerini kullanıcıya gösterir. Bu değer `.env` içindeki `TELEGRAM_CHAT_ID` alanında kullanılabilir.
- Hangi servis/fonksiyonu çağırır: `cmd_chat_id()`
- Başarılı cevap örneği:

```text
Bu sohbetin chat ID değeri:
123456789

Bunu .env içindeki TELEGRAM_CHAT_ID alanına yaz.
```

- Hata cevap örneği: Chat bilgisi okunamazsa `Chat ID okunamadı.`

### `/ekle`

- Komut adı: `/ekle`
- Kullanım formatı: `/ekle <url> [hedef_fiyat]`
- Örnek kullanım:

```text
/ekle https://www.trendyol.com/ornek/urun-p-123
/ekle https://www.amazon.com.tr/dp/B000000000 1500
```

- Ne yapar: URL'yi doğrular, ürünü scrape eder, takip listesine ekler.
- Hangi servis/fonksiyonu çağırır: `cmd_add()`, `validate_url()`, `add_tracked_product()`
- Başarılı cevap örneği:

```text
Ürün takibe alındı!
Ürün: ...
Fiyat: 1299.99 TRY
Platform: Trendyol
Hedef: 1000 TRY
```

- Hata cevap örnekleri:
  - Argüman yoksa: `Kullanım: /ekle <ürün_url> [hedef_fiyat]`
  - Hedef fiyat geçersizse: `Geçersiz hedef fiyat.`
  - URL geçersizse: `URL 'http://' veya 'https://' ile başlamalıdır.`
  - Scrape başarısızsa: `Ürün bilgileri alınamadı: ...`

### `/liste`

- Komut adı: `/liste`
- Kullanım formatı: `/liste`
- Örnek kullanım: `/liste`
- Ne yapar: Takip edilen ürünleri sıra numarasıyla listeler.
- Hangi servis/fonksiyonu çağırır: `cmd_list()`, `get_tracker()`, `PriceTracker.get_all_products()`
- Başarılı cevap örneği:

```text
Takip Listeniz:

1. Ürün başlığı
   1299.99 TRY | Trendyol
   Hedef: 1000 TRY
```

- Hata/boş liste cevabı:

```text
Takip listeniz boş.
/ekle komutuyla ürün ekleyebilirsiniz.
```

### `/sil`

- Komut adı: `/sil`
- Kullanım formatı: `/sil <sıra_numarası>`
- Örnek kullanım: `/sil 1`
- Ne yapar: `/liste` çıktısındaki sıra numarasına göre ürünü takipten çıkarır.
- Hangi servis/fonksiyonu çağırır: `cmd_remove()`, `PriceTracker.get_all_products()`, `PriceTracker.remove_product()`
- Başarılı cevap örneği:

```text
Takipten çıkarıldı: Ürün adı
```

- Hata cevap örnekleri:
  - Argüman yoksa: `Kullanım: /sil <sıra_numarası>`
  - Sayı değilse: `Geçersiz numara.`
  - Aralık dışındaysa: `Geçersiz numara. 1-N arası bir değer girin.`

### `/kontrol`

- Komut adı: `/kontrol`
- Kullanım formatı: `/kontrol`
- Örnek kullanım: `/kontrol`
- Ne yapar: Tüm takip edilen ürünleri manuel olarak kontrol eder, oluşan alarm mesajlarını aynı Telegram konuşmasına gönderir.
- Hangi servis/fonksiyonu çağırır: `cmd_check()`, `check_all_tracked_products()`, `acknowledge_alert()`
- Başarılı cevap örneği:

```text
Kontrol tamamlandı.
3 ürün kontrol edildi.
1 alarm tespit edildi.
```

- Hata/boş liste cevabı:

```text
Takip listeniz boş.
```

### Telegram alarm gönderimi: `send_telegram_alert(alert)`

- Kullanıldığı yer: Scheduler otomatik kontrol akışı.
- Parametreler: Alarm dict'i.
- Dönen değer: `bool`
- Davranış:
  - `TELEGRAM_BOT_TOKEN` veya `TELEGRAM_CHAT_ID` eksikse bildirim atlanır, warning log yazılır ve `False` döner.
  - `image_url` varsa önce fotoğraf + caption gönderilmeye çalışılır.
  - Fotoğraf gönderilemezse metin mesajı denenir.
  - Genel hata olursa exception loglanır ve `False` döner.
- Sistem çökme davranışı: Bildirim gönderilemezse fonksiyon `False` döndürür; scheduler bu durumda cooldown kaydı yazmaz ve uygulamayı çökertmez.

### Bot token yoksa sistem davranışı

- `create_telegram_app()` içinde `TELEGRAM_BOT_TOKEN` yoksa `None` döner ve Telegram bot devre dışı kalır.
- [main.py](../main.py) token yoksa "Telegram bot devre dışı" bilgisini loglar.
- Web arayüzü ve scheduler çalışmaya devam eder.

### Telegram polling conflict

`telegram_error_handler()` `telegram.error.Conflict` hatasını özel olarak yakalar ve aynı bot tokeniyle başka polling/getUpdates işlemi çalıştığını loglar. [main.py](../main.py) ayrıca `data/price_tracker.lock` ile ikinci local instance başlatmayı engellemeye çalışır.

## 8. Email Bildirimleri

E-posta bildirimi [app/email_service.py](../app/email_service.py) içinde Gmail SMTP üzerinden yapılır.

Gerekli `.env` değişkenleri:

- `GMAIL_ADDRESS`: Gönderici Gmail adresi.
- `GMAIL_APP_PASSWORD`: Gmail uygulama şifresi.
- `NOTIFICATION_EMAIL`: Alıcı e-posta adresi.

SMTP ayarı:

```text
Host: smtp.gmail.com
Port: 465
Protokol: SMTP_SSL
```

### `_build_alert_html(alert)`

- Parametreler: Alarm dict'i.
- Dönen değer: HTML e-posta içeriği string'i.
- Görevi: Alarm türüne göre HTML mail gövdesi oluşturur.
- Alarm türüne göre görünüm:
  - `target_reached`: Yeşil başlık ve hedef fiyat bilgisi.
  - Diğer durumlar: Fiyat düşüşü başlığı, eski ve yeni fiyat bilgisi.
- Görsel: `image_url` varsa HTML içinde ürün görseli eklenir.

### `send_price_alert_email(alert)`

- Parametreler: Alarm dict'i.
- Dönen değer: `bool`
- Görevi: Hem düz metin hem HTML içeren MIME e-postası oluşturur ve Gmail SMTP ile gönderir.
- Mail subject formatı:

```text
Fiyat Alarmı: <ürün başlığı>
```

- Fiyat düşünce tetiklenme yeri: Scheduler `_run_price_check()` içinde alarm listesi üzerinde çağrılır.
- Hata davranışı:
  - Gerekli Gmail ayarları eksikse log yazar, e-posta gönderimini atlar ve `False` döner.
  - SMTP kimlik doğrulama hatası varsa log yazar ve `False` döner.
  - SMTP hatası varsa log yazar ve `False` döner.
  - Beklenmeyen hata varsa log yazar ve `False` döner.
- Sistem çökme davranışı: Fonksiyon kendi içinde hataları yakalayıp `False` döndürür. Scheduler ayrıca çağrıyı `try/except` içinde yapar.

## 9. Scheduler / Otomatik Fiyat Kontrolü

Scheduler kodu [app/scheduler.py](../app/scheduler.py) içindedir ve APScheduler `BackgroundScheduler` kullanır.

### Kontrol aralığı

Fiyat kontrol aralığı `SCRAPE_INTERVAL_HOURS` değişkeninden okunur. Varsayılan değer:

```text
6 saat
```

Bu değer [config.py](../config.py) içinde `int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))` olarak tanımlıdır. `.env.example` içinde de `SCRAPE_INTERVAL_HOURS=6` yer alır.

Kodda 3 saatlik sabit bir kontrol mantığı yoktur. İstenirse `.env` üzerinden `SCRAPE_INTERVAL_HOURS=3` verilerek 3 saate indirilebilir, ancak mevcut varsayılan 6 saattir.

### `start_scheduler()`

- Dönen değer: `BackgroundScheduler`
- Görevi: Scheduler'ı başlatır ve `price_check_job` adında interval job ekler.
- Job ayarları:
  - Trigger: `IntervalTrigger(hours=SCRAPE_INTERVAL_HOURS)`
  - `replace_existing=True`
  - `max_instances=1`
- Uygulama başlarken otomatik çalışır mı: Evet. [main.py](../main.py) içinde Flask başlatılmadan önce `start_scheduler()` çağrılır.
- Çakışma davranışı: `max_instances=1` aynı job'un aynı anda birden fazla instance olarak çalışmasını engeller. Ayrıca `start_scheduler()` scheduler zaten çalışıyorsa mevcut instance'ı döndürür.

### `_run_price_check()`

- Görevi: APScheduler tarafından çağrılan senkron wrapper fonksiyondur.
- Akış:
  1. Yeni asyncio event loop oluşturur.
  2. `_check_all_prices()` ile tüm ürünleri kontrol eder.
  3. Her alarm için `send_price_alert_email()` çağırır.
  4. Her alarm için `send_telegram_alert()` çağırır.
  5. E-posta veya Telegram başarılıysa `acknowledge_alert()` ile cooldown kaydı yazar.
  6. Hiçbir bildirim gönderilemezse cooldown yazmaz.
  7. Event loop'u kapatır.

### `_check_all_prices()`

- Dönen değer: Alarm dict listesi.
- Görevi: `check_all_tracked_products(headless=HEADLESS_BROWSER)` çağırır.

### `trigger_manual_check()`

- Dönen değer: Alarm dict listesi.
- Kullanıldığı yer: Web endpointi `POST /check`
- Görevi: Manuel fiyat kontrolü için yeni event loop açar ve `_check_all_prices()` çalıştırır.

### `stop_scheduler()`

- Görevi: Scheduler çalışıyorsa `shutdown(wait=False)` ile durdurur.
- Kullanıldığı yer: Mevcut kodda route tarafından çağrılmıyor; yardımcı fonksiyondur.

### Manuel kontrol ile scheduler farkı

| Konu | Manuel kontrol | Scheduler |
| --- | --- | --- |
| Tetikleme | Kullanıcı butonu veya Telegram komutu | APScheduler interval job |
| Bildirim | Web'de flash, Telegram komutunda sohbet mesajı | E-posta ve Telegram alarm bildirimi |
| Cooldown kaydı | Web/Telegram manuel akışında alarm kullanıcıya gösterilince yazılır | Sadece e-posta veya Telegram gönderimi başarılıysa yazılır |
| Zamanlama | Anında | `SCRAPE_INTERVAL_HOURS` kadar aralıkla |

### Anti-ban açısından bekleme/delay/retry

- Detay scraping içinde `_human_delay()` ve `_scroll_page()` kullanılır.
- Toplu URL scraping helper'ında istekler arası `delay_between=(3.0, 7.0)` vardır.
- `scrape_product_url()` bazı platformlarda headless sonuç yetersizse headed retry dener.
- Scheduler'ın kendisinde ek retry/backoff mekanizması yoktur; scraper seviyesindeki davranışlara dayanır.

## 10. Veri Saklama Yapısı

Projede veri JSON dosyalarında tutulur:

- Ürün kayıtları: [data/products.json](../data/products.json)
- Fiyat geçmişi: [data/price_history.json](../data/price_history.json)

`PriceTracker` başlatıldığında bu dosyaları okur. Dosya yoksa boş dict ile devam eder. JSON decode veya IO hatası olursa hata loglanır ve boş yapı döner.

### `products.json` şeması

```json
{
  "abc123def456": {
    "url": "https://www.trendyol.com/ornek/urun-p-123",
    "title": "Ürün adı",
    "platform": "trendyol",
    "image_url": "https://...",
    "target_price": 1000.0,
    "current_price": 1299.99,
    "currency": "TRY",
    "added_at": "2026-04-28T12:00:00+00:00",
    "last_checked": "2026-04-28T12:00:00+00:00",
    "in_stock": true,
    "last_alert_at": "2026-04-28T15:00:00+00:00",
    "last_alert_kind": "target"
  }
}
```

Alan açıklamaları:

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `url` | string | Ürün URL'si. |
| `title` | string | Scraper veya karşılaştırma sonucundan gelen ürün adı. |
| `platform` | string | `trendyol`, `amazon`, `hepsiburada`. |
| `image_url` | string | Ürün görsel URL'si. |
| `target_price` | float/null | Kullanıcının belirlediği hedef fiyat. |
| `current_price` | float/null | Son bilinen fiyat. |
| `currency` | string | Varsayılan `TRY`. |
| `added_at` | string | ISO formatında eklenme zamanı. |
| `last_checked` | string/null | Son fiyat kontrol zamanı. |
| `in_stock` | bool | Stok durumu. |
| `last_alert_at` | string | Alarm başarıyla gösterildi/gönderildi ise son alarm zamanı. |
| `last_alert_kind` | string | Son alarm türü: `target` veya `drop`. |

`last_alert_at` ve `last_alert_kind` ilk ürün ekleme sırasında zorunlu değildir; alarm başarıyla acknowledge edilince eklenir.

### `price_history.json` şeması

```json
{
  "abc123def456": [
    {
      "price": 1299.99,
      "in_stock": true,
      "timestamp": "2026-04-28T12:00:00+00:00"
    },
    {
      "price": 1199.99,
      "in_stock": true,
      "timestamp": "2026-04-28T18:00:00+00:00"
    }
  ]
}
```

Alan açıklamaları:

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `price` | float | O kontrolde bulunan fiyat. |
| `in_stock` | bool | O kontroldeki stok durumu. |
| `timestamp` | string | ISO formatında kayıt zamanı. |

## 11. Karşılaştırma / Arama Servisi

Karşılaştırma mantığı [app/search_engine.py](../app/search_engine.py) içindedir.

### `validate_search_query(query)`

- Parametreler: `query`
- Dönen değer: `bool`
- Görevi: Sorgunun string ve boş olmayan bir değer olduğunu kontrol eder.
- Kullanıldığı yer: `POST /compare/search`

### `build_search_url(platform, query)`

- Parametreler:
  - `platform`: `trendyol`, `amazon`, `hepsiburada`
  - `query`: Arama metni
- Dönen değer: Platform arama URL'si.
- Hata davranışı: Platform desteklenmiyorsa `ValueError`.

Platform URL şablonları:

```python
{
  "trendyol": "https://www.trendyol.com/sr?q={query}",
  "amazon": "https://www.amazon.com.tr/s?k={query}",
  "hepsiburada": "https://www.hepsiburada.com/ara?q={query}"
}
```

### `SearchEngine.search_platform(platform, query)`

- Parametreler: Platform adı ve sorgu.
- Dönen değer: En fazla 3 ürün sonucu içeren liste.
- Görevi: İlgili platform scraper'ını açar, arama yapar, her sonuca `id` alanı ekler ve fiyatı olanları artan fiyata göre sıralar.
- Hata davranışı: Desteklenmeyen platformda `ValueError`; üst seviye `search_all()` bunu yakalar.
- Özel davranış: `HEADLESS_BROWSER=True` ve Amazon/Hepsiburada sonuç dönmezse headed fallback denenir.

### `SearchEngine.search_all(query)`

- Parametreler: Arama sorgusu.
- Dönen değer:

```json
{
  "trendyol": [],
  "amazon": [],
  "hepsiburada": []
}
```

veya platform bazında:

```json
{
  "amazon": {
    "error": "hata mesajı",
    "results": []
  }
}
```

- Görevi: Üç platformda eş zamanlı arama yapar. Bir platform hata verirse diğerleri devam eder.

## 12. Ortam Değişkenleri

[.env.example](../.env.example) içinde tanımlı değişkenler:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
NOTIFICATION_EMAIL=recipient@example.com

SCRAPE_INTERVAL_HOURS=6
HEADLESS_BROWSER=true

FLASK_SECRET_KEY=change_this_to_a_random_secret_key
FLASK_PORT=5000
FLASK_DEBUG=false
```

[config.py](../config.py), örnek placeholder değerlerini gerçek ayar gibi kabul etmez; `_clean_env()` bu değerleri boş string'e çevirir. Bu yüzden `.env.example` içindeki placeholder değerler değiştirilmezse Telegram ve e-posta servisleri devre dışı kabul edilir.

## 13. Sağlık Kontrolü / Test Endpointi Durumu

Mevcut Flask uygulamasında ayrı bir health check endpointi yoktur. Kodda `/health`, `/ping`, `/test` gibi bir route tanımlı değildir.

Test veya smoke amaçlı dosyalar route değildir:

- [scripts/smoke.py](../scripts/smoke.py)
- [tests/test_scraper_properties.py](../tests/test_scraper_properties.py)
- [tests/test_alert_delivery.py](../tests/test_alert_delivery.py)

## 14. Mevcut API Yüzeyinin Kısa Listesi

| Method | URL | Tip | Amaç |
| --- | --- | --- | --- |
| `GET` | `/` | HTML | Takip paneli. |
| `POST` | `/add` | HTML form | Ürün ekleme. |
| `POST` | `/remove/<product_id>` | HTML form | Ürün silme. |
| `POST` | `/target/<product_id>` | HTML form | Hedef fiyat güncelleme. |
| `POST` | `/check` | HTML form | Manuel fiyat kontrolü. |
| `GET` | `/api/history/<product_id>` | JSON | Fiyat geçmişi ve istatistikler. |
| `GET` | `/compare` | HTML | Karşılaştırma sayfası. |
| `POST` | `/compare/search` | JSON | Ürün adıyla platformlarda arama. |
| `POST` | `/compare/add` | JSON | Karşılaştırma sonucunu takibe ekleme. |

Telegram komutları:

| Komut | Amaç |
| --- | --- |
| `/start` | Karşılama ve komut listesi. |
| `/yardim` | Yardım mesajı. |
| `/help` | Yardım mesajı. |
| `/chatid` | Mevcut sohbet ID'sini gösterir. |
| `/ekle <url> [hedef_fiyat]` | Ürün ekler. |
| `/liste` | Takip listesini gösterir. |
| `/sil <no>` | Ürünü sıra numarasına göre siler. |
| `/kontrol` | Manuel fiyat kontrolü yapar. |

## 15. Bilinen Sınırlar

- Ürün yönetiminin ana yüzeyi REST API değil, HTML form tabanlıdır.
- JSON endpointleri sadece fiyat geçmişi ve karşılaştırma ekranı için vardır.
- Veri saklama JSON dosyalarıyla yapılır; yüksek eş zamanlı kullanım için tasarlanmamıştır.
- E-ticaret siteleri HTML veya API yapılarını değiştirdiğinde scraper fonksiyonları bozulabilir.
- Anti-bot sistemleri nedeniyle scraping sonucu her zaman garanti değildir.
- Scheduler uygulama başlarken çalışmaya başlar, ancak hemen ilk taramayı yapmaz; interval süresini bekler. Anında kontrol için webde `POST /check`, Telegram'da `/kontrol` kullanılır.
