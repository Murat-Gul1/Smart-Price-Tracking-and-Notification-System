# Smart Price Tracking and Notification System

Bu proje, e-ticaret sitelerindeki urun fiyatlarini takip etmek, fiyat gecmisini saklamak, platformlar arasi karsilastirma yapmak ve fiyat dususlerinde bildirim gondermek icin gelistirilmis bir Python uygulamasidir.

Mevcut kod tabaninin ana amaci sunlardir:

- Trendyol, Amazon.com.tr ve Hepsiburada urunlerini takip etmek
- Belirli bir urun icin hedef fiyat tanimlamak
- Fiyat gecmisini JSON dosyalarinda saklamak
- Periyodik olarak fiyat kontrolu yapmak
- Fiyat dustugunde veya hedef fiyata ulasildiginda e-posta / Telegram bildirimi gondermek
- Web arayuzu uzerinden urun ekleme, silme, hedef fiyat guncelleme ve manuel kontrol yapmak
- Ayni urunu farkli platformlarda arayip fiyat karsilastirmasi yapmak

## Projenin Genel Calisma Mantigi

Uygulama temel olarak 5 parcadan olusur:

1. `Flask` tabanli web arayuzu kullanicidan urun URL'si veya arama sorgusu alir.
2. `Playwright + playwright-stealth` kullanan scraper katmani urun bilgilerini ceker.
3. `PriceTracker` sinifi urunleri ve fiyat gecmisini `data/` altindaki JSON dosyalarina yazar.
4. `APScheduler` belli araliklarla tekrar fiyat kontrolu yapar.
5. Alarm olusursa `email_service.py` ve/veya `telegram_bot.py` uzerinden bildirim gonderilir.

Kisaca akis su sekildedir:

`Kullanici -> Web/Telegram -> Scraper -> PriceTracker -> JSON Veri -> Scheduler -> Bildirim`

## One Cikan Ozellikler

- URL ile dogrudan urun takibi
- Hedef fiyat belirleme
- Min / max / ortalama fiyat istatistikleri
- Manuel fiyat kontrolu
- Otomatik periyodik kontrol
- Telegram bot komutlari ile urun yonetimi
- Gmail SMTP ile HTML e-posta bildirimi
- 3 platformda es zamanli arama ve fiyat karsilastirma
- Basit ama kullanisli bir web arayuzu

## Kullanilan Teknolojiler

- Python 3.10+
- Flask
- APScheduler
- Playwright
- playwright-stealth
- python-telegram-bot
- python-dotenv

## Klasor ve Dosya Yapisi

```text
Smart-Price-Tracking-and-Notification-System/
├── app/
│   ├── __init__.py
│   ├── email_service.py
│   ├── logic.py
│   ├── scheduler.py
│   ├── scraper.py
│   ├── search_engine.py
│   ├── telegram_bot.py
│   ├── web.py
│   ├── static/
│   │   └── style.css
│   └── templates/
│       ├── compare.html
│       └── index.html
├── data/
│   ├── price_history.json
│   └── products.json
├── tests/
│   └── test_scraper_properties.py
├── utils/
│   └── security.py
├── .env.example
├── .gitignore
├── api_debug.json
├── config.py
├── debug_html.txt
├── debug_output.txt
├── debug_output2.txt
├── debug_output3.txt
├── fiyat_getir_ornek.py
├── main.py
├── requirements.txt
├── test_results.json
└── test_selectors.py
```

## Dosya Dosya Aciklama

### Giris ve konfigurasyon

- `main.py`
  Uygulamanin ana giris noktasi. Loglamayi ayarlar, `data/` klasorunu hazirlar, Flask uygulamasini olusturur, scheduler'i baslatir ve varsa Telegram botu ayaga kaldirir.

- `config.py`
  Tum ayarlari `.env` dosyasindan okur. Port, Flask debug modu, scheduler araligi, headless browser ayari, Gmail ve Telegram bilgileri burada merkezilesir.

- `requirements.txt`
  Projenin calismasi icin gereken Python paketlerini listeler.

- `.env.example`
  Ortam degiskenleri icin ornek sablon dosyasi. Gercek calismada bunun kopyasi `.env` olarak kullanilmalidir.

### Uygulama cekirdegi

- `app/web.py`
  Flask route'larini tanimlar. Ana sayfa, urun ekleme, urun silme, hedef fiyat guncelleme, manuel kontrol, fiyat gecmisi API'si ve karsilastirma sayfasi burada bulunur.

- `app/logic.py`
  Projenin is mantiginin merkezidir. `PriceTracker` sinifi:
  - urun ekler / gunceller / siler
  - fiyat gecmisini tutar
  - istatistik uretir
  - fiyat dususu ve hedef fiyat alarmini hesaplar

- `app/scheduler.py`
  `APScheduler` ile periyodik fiyat kontrolu yapar. Takipteki tum urunler icin scraper'i cagirir, yeni fiyatlari kaydeder ve olusan alarmlari bildirim servislerine yollar.

- `app/scraper.py`
  En kritik dosyalardan biridir. Playwright tabanli scraping katmanini barindirir.
  Icerik olarak:
  - `StealthScraper`: ortak temel sinif
  - `TrendyolScraper`
  - `AmazonScraper`
  - `HepsiburadaScraper`
  - `get_scraper()`: URL'ye gore uygun scraper secimi
  - `scrape_product_url()`: tek URL icin kolay kullanim fonksiyonu
  - `scrape_multiple_urls()`: toplu scraping yardimcisi

- `app/search_engine.py`
  Karsilastirma ekraninin arka plan mantigini yonetir. Kullanici sorgusunu 3 platform icin ayri ayri calistirir, sonuclari toplar, siralar ve en dusuk fiyatli urunu bulur.

- `app/email_service.py`
  Gmail SMTP ile fiyat alarm e-postasi gonderir. Hem duz metin hem de HTML formatinda e-posta olusturur.

- `app/telegram_bot.py`
  Telegram bot komutlarini ve scheduler tarafindan kullanilan Telegram bildirim gonderimini icerir.
  Desteklenen komutlar:
  - `/start`
  - `/yardim`
  - `/ekle <url> [hedef_fiyat]`
  - `/liste`
  - `/sil <no>`
  - `/kontrol`

### Arayuz

- `app/templates/index.html`
  Ana takip paneli. Urun ekleme formu, takip listesi, hedef fiyat guncelleme alani, manuel kontrol butonu ve fiyat istatistikleri burada gosterilir.

- `app/templates/compare.html`
  Karsilastirma sayfasi. Kullanici urun adini girer, Trendyol / Amazon / Hepsiburada sonuclari ayni ekranda gosterilir.

- `app/static/style.css`
  Tum arayuz stillerini icerir. Ana takip sayfasi ve karsilastirma sayfasi icin tek CSS dosyasi kullanilir.

### Yardimci katman

- `utils/security.py`
  Guvenlik ve veri butunlugu icin yardimci fonksiyonlari barindirir:
  - URL dogrulama
  - desteklenen platform tespiti
  - URL temizleme
  - urun ID uretme
  - secret key uretme
  - basit in-memory rate limiter

### Veri dosyalari

- `data/products.json`
  Takip edilen urunlerin aktif durumdaki anlik kaydini tutar.

- `data/price_history.json`
  Her urun icin zaman icindeki fiyat kayitlarini tutar.

Su an repodaki iki dosya da bos `{}` olarak duruyor; uygulama calistikca doldurulacaklar.

### Test ve debug dosyalari

- `tests/test_scraper_properties.py`
  Hepsiburada scraper ciktilarinin belirli alanlari garanti edip etmedigini property-based test mantigiyla kontrol eder.

- `test_selectors.py`
  Trendyol tarafinda API/selector kesfi icin hazirlanmis debug scriptidir.

- `fiyat_getir_ornek.py`
  Scraping mantiginin daha genel / ornek bir prototip surumudur. Uretim akisinda zorunlu degildir ama referans olarak yararlidir.

- `api_debug.json`, `debug_html.txt`, `debug_output.txt`, `debug_output2.txt`, `debug_output3.txt`, `test_results.json`
  Gecmis debug ve deneme ciktilaridir. Uygulamanin ana runtime akisinda zorunlu degiller.

## Desteklenen Platformlar

Kod tabanina gore desteklenen platformlar:

- Trendyol
- Amazon.com.tr
- Hepsiburada

Not:

- Ana arayuzdeki bazi sabit metinler hala Trendyol + Amazon vurgusu tasiyor.
- Ancak backend tarafinda `Hepsiburada` destegi bulunuyor.

## Veri Yapisi

### `products.json`

Her urun asagidaki mantikla tutulur:

```json
{
  "product_id": {
    "url": "https://ornek-site.com/urun",
    "title": "Urun Basligi",
    "platform": "trendyol",
    "image_url": "https://...",
    "target_price": 15000.0,
    "current_price": 16499.0,
    "currency": "TRY",
    "added_at": "2026-04-28T12:00:00+00:00",
    "last_checked": "2026-04-28T12:00:00+00:00",
    "in_stock": true
  }
}
```

### `price_history.json`

Her urun icin zaman serisi kayitlari tutulur:

```json
{
  "product_id": [
    {
      "price": 16999.0,
      "in_stock": true,
      "timestamp": "2026-04-28T12:00:00+00:00"
    },
    {
      "price": 16499.0,
      "in_stock": true,
      "timestamp": "2026-04-28T18:00:00+00:00"
    }
  ]
}
```

## Alarm Mantigi

Uygulama iki durumda alarm uretir:

1. Urun fiyati hedef fiyatin altina veya esigine duserse
2. Yeni fiyat, onceki kayitli fiyattan daha dusukse

Alarm oluştugunda:

- E-posta ayarlari varsa Gmail ile e-posta gonderilir
- Telegram ayarlari varsa Telegram mesaji gonderilir

## Ortam Degiskenleri

`.env.example` dosyasina gore kullanilan ortam degiskenleri:

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

### Degiskenlerin anlami

- `TELEGRAM_BOT_TOKEN`
  Telegram bot token'i. Bos birakilirsa bot devreye girmez.

- `TELEGRAM_CHAT_ID`
  Bildirimlerin gidecegi sohbet ID'si.

- `GMAIL_ADDRESS`
  Gonderici Gmail adresi.

- `GMAIL_APP_PASSWORD`
  Gmail icin uygulama sifresi. Normal hesap sifresi kullanilmaz.

- `NOTIFICATION_EMAIL`
  Bildirimlerin gidecegi alici e-posta adresi.

- `SCRAPE_INTERVAL_HOURS`
  Otomatik fiyat kontrolunun kac saatte bir yapilacagi.

- `HEADLESS_BROWSER`
  `true` ise browser arka planda acilir. `false` ise tarayici gorunur.

- `FLASK_SECRET_KEY`
  Flask session / flash mesajlari icin gizli anahtar.

- `FLASK_PORT`
  Web arayuzunun calisacagi port.

- `FLASK_DEBUG`
  Flask debug modunu acar / kapatir.

## Projeyi Nasil Calistiririm?

Asagidaki adimlar bu proje icin en dogru baslatma akisini verir.

### 1. Repoyu acin

```powershell
cd C:\Users\mertadores\Documents\Smart-Price-Tracking-and-Notification-System
```

### 2. Sanal ortam olusturun

```powershell
python -m venv .venv
```

### 3. Sanal ortami aktif edin

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
.venv\Scripts\activate.bat
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 4. Python bagimliliklarini kurun

```powershell
pip install -r requirements.txt
```

### 5. Playwright browser'ini kurun

Bu adim cok onemli. `playwright` paketi tek basina yeterli degildir; Chromium browser binary'si da kurulmalidir.

```powershell
python -m playwright install chromium
```

Gerekirse sistem bagimliliklari icin:

```powershell
python -m playwright install
```

### 6. Ortam dosyasini olusturun

`.env.example` dosyasini kopyalayip `.env` olarak kaydedin.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Daha sonra `.env` dosyasini acip gerekli alanlari doldurun.

Minimum calisma icin genelde su alanlar yeterlidir:

```env
SCRAPE_INTERVAL_HOURS=6
HEADLESS_BROWSER=true
FLASK_SECRET_KEY=buraya_guclu_bir_key_yazin
FLASK_PORT=5000
FLASK_DEBUG=false
```

E-posta ve Telegram tamamen opsiyoneldir.

### 7. Uygulamayi baslatin

```powershell
python main.py
```

Basarili baslatma sonrasinda uygulama tipik olarak su islemleri yapar:

- `data/` klasorunu hazirlar
- Flask uygulamasini olusturur
- scheduler'i baslatir
- Telegram token varsa botu ayaga kaldirir
- web sunucusunu `http://localhost:5000` adresinde acir

### 8. Tarayicida acin

```text
http://localhost:5000
```

## Uygulama Acildiktan Sonra Nasil Kullanilir?

### Web arayuzu

1. Ana sayfada urun URL'si girin
2. Isterseniz hedef fiyat ekleyin
3. `Takibe Al` butonuna basin
4. Urun takip listesine eklenecektir
5. `Manuel Kontrol` ile anlik fiyat kontrolu yapabilirsiniz
6. Hedef fiyat alanindan mevcut kayitlari guncelleyebilirsiniz
7. `Karsilastir` sayfasindan ayni urunu farkli platformlarda aratabilirsiniz

### Telegram bot

`.env` dosyasinda Telegram bilgileri varsa bot da ayaga kalkar.

Ornek kullanim:

```text
/ekle https://www.trendyol.com/...
/ekle https://www.amazon.com.tr/... 15000
/liste
/kontrol
/sil 1
```

## Flask Route'lari

Kod tabaninda tanimli ana endpoint'ler:

- `GET /`
  Ana takip paneli

- `POST /add`
  Yeni urunu takip listesine ekler

- `POST /remove/<product_id>`
  Urunu takipten cikarir

- `POST /target/<product_id>`
  Hedef fiyati gunceller

- `POST /check`
  Manuel fiyat kontrolu yapar

- `GET /api/history/<product_id>`
  Urunun fiyat gecmisini JSON olarak dondurur

- `GET /compare`
  Fiyat karsilastirma sayfasi

- `POST /compare/search`
  Karsilastirma icin arama yapar

- `POST /compare/add`
  Karsilastirma sonucundan urun takibe eklemeyi hedefler

## Testler Nasil Calistirilir?

Projede test dosyasi bulunuyor ancak `pytest` ve `hypothesis` paketleri `requirements.txt` icinde yer almiyor. Test calistirmak icin once bunlari kurmaniz gerekir.

```powershell
pip install pytest hypothesis
pytest -q
```

Mevcut repoda benim yaptigim hizli dogrulama:

- `python -m compileall .` komutu basariyla calisti

Bu, dosyalarin en azindan Python sozdizimi olarak derlenebildigini gosterir.

## Mimari Notlar

- Uygulama veritabani yerine JSON dosyalari kullaniyor.
- Bu nedenle tek kullanicili / kucuk olcekli local kullanim icin daha uygun.
- Scraping tarafinda anti-bot korumalarini asmaga yonelik `stealth` mantigi kullaniliyor.
- `search_engine.py` icinde bazi aramalar `headless=False` ile calisacak sekilde kurgulanmis; bu, korumali platformlarda gorunur browser acilmasina neden olabilir.
- `main.py` icinde Flask `use_reloader=False` ile calisiyor; bu, scheduler cakislarini onlemek icin yapilmis.

## Bilinmesi Gereken Sinirlar

- E-ticaret siteleri HTML yapilarini degistirdiginde selector veya parse mantigi kirilabilir.
- Anti-bot sistemleri nedeniyle scraping her zaman %100 stabil olmayabilir.
- `products.json` ve `price_history.json` dosyalari eszamanli ve yuksek trafikli kullanim icin uygun degildir.
- Scheduler varsayilan olarak belirli araliklarla calisir; uygulama baslar baslamaz otomatik ilk tarama yapmaz, bunun icin `Manuel Kontrol` kullanabilirsiniz.

## Kisa Baslatma Ozeti

Sadece hizli baslatmak istiyorsaniz:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
python main.py
```

Ardindan:

```text
http://localhost:5000
```

## Sonuc

Bu projenin mevcut amaci, tek bir yerden birden fazla e-ticaret platformundaki urunleri takip etmek, fiyat hareketlerini kaydetmek ve kullaniciyi zamaninda haberdar etmektir. Kod yapisi, web arayuzu + scraping + scheduler + bildirim servisleri seklinde bolunmus ve kucuk/orta olcekli bireysel kullanim senaryolari icin uygun bir temel sunmaktadir.
