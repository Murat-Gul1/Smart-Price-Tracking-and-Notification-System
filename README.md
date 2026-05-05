# Smart Price Tracking and Notification System

This project is a Python application developed to track product prices on e-commerce websites, store price history, perform cross-platform comparisons, and send notifications when prices drop.

The main purpose of the current codebase is as follows:

- Tracking products on Trendyol, Amazon.com.tr, and Hepsiburada
- Defining a target price for a specific product
- Storing price history in JSON files
- Periodically checking prices
- Sending email/Telegram notifications when the price drops or the target price is reached
- Adding, deleting products, updating target prices, and performing manual checks via the web interface
- Searching for the same product on different platforms and comparing prices

## General Working Principles of the Project

The application basically consists of 5 parts:

1. A `Flask`-based web interface receives a product URL or search query from the user.
2. A scraper layer using `Playwright + playwright-stealth` retrieves product information.
3. The `PriceTracker` class writes the products and price history to JSON files under `data/`.
4. `APScheduler` performs price checks at regular intervals.
5. If an alarm occurs, a notification is sent via `email_service.py` and/or `telegram_bot.py`.

In short, the workflow is as follows:

`User -> Web/Telegram -> Scraper -> PriceTracker -> JSON Data -> Scheduler -> Notification`

## Key Features

- Direct product tracking via URL
- Target price setting
- Min/max/average price statistics
- Manual price control
- Automatic periodic checks
- Product management with Telegram bot commands
- HTML email notification via Gmail SMTP
- Simultaneous search and price comparison across 3 platforms
- Simple but user-friendly web interface

## Technologies Used

- Python 3.10+
- Flask
- APScheduler
- Playwright
- playwright-stealth
- python-telegram-bot
- python-dotenv

## Folder and File Structure

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

Note: This tree block is a summary structure. For a full description of current services and helper files, see the "File Description" section below.

## File Description

### Introduction and Configuration

- `main.py`
The application's main entry point. It configures logging, prepares the `data/` folder, obtains a single-instance lock, creates the Flask application, starts the scheduler, and activates the Telegram bot if one exists.

- `config.py`
It reads all settings from the `.env` file. Port, Flask debug mode, scheduler interval, headless browser settings, Gmail and Telegram information are all centralized here.
- `requirements.txt`
Lists the Python packages required for the project to run.

- `.env.example`
Example template file for environment variables. A copy of this should be used as a `.env` file in the actual project.

### Application Core

- `app/web.py`
Defines Flask routes. The homepage, product adding, product deletion, target price update, manual check, price history API, and comparison page are located here.

- `app/logic.py`
This is the core of the project's business logic. The `PriceTracker` class:
- adds/updates/deletes products
- keeps track of price history
- generates statistics
- calculates price drop and target price alerts

- `app/scheduler.py`
Performs periodic price checks with `APScheduler`. Calls the scraper for all tracked products, records the new prices, and sends the resulting alarms to notification services.

- `app/services.py`
This is a shared service layer between the web interface, scheduler, and Telegram bot. It brings together product addition, scrape result normalization, and bulk price check workflows in one place.

- `app/scraper.py`
This is one of the most critical files. It contains the Playwright-based scraping layer.
Contents:
- `StealthScraper`: common base class
- `TrendyolScraper`
- `AmazonScraper`
- `HepsiburadaScraper`
- `get_scraper()`: selects the appropriate scraper based on the URL
- `scrape_product_url()`: easy-to-use function for a single URL
- `scrape_multiple_urls()`: bulk scraping helper

- `app/search_engine.py`
Manages the background logic of the comparison screen. Runs the user query separately for 3 platforms, sums and sorts the results, and finds the lowest priced product.

- `app/email_service.py`
Sends price alert emails via Gmail SMTP. Creates emails in both plain text and HTML format.

- `app/telegram_bot.py`
Contains Telegram bot commands and Telegram notification sending used by the scheduler. Supported commands:
  - `/start`
  - `/yardim`
  - `/ekle <url> [hedef_fiyat]`
  - `/liste`
  - `/sil <no>`
  - `/kontrol`

### Interface(UI)

- `app/templates/index.html`
Main tracking panel. The product addition form, watchlist, target price update area, manual control button, and price statistics are displayed here.

- `app/templates/compare.html`
Comparison page. The user enters the product name, and Trendyol / Amazon / Hepsiburada results are displayed on the same screen.

- `app/static/style.css`
Contains all interface styles. A single CSS file is used for the main tracking page and comparison page.

### Auxiliary Layer

- `utils/security.py`
Contains auxiliary functions for security and data integrity:
- URL validation
- Supported platform detection
- URL sanitization - Product ID generation
- Secret key generation
- Simple in-memory rate limiter

- `utils/stealth_compat.py`
Provides compatibility with Python 3.14 environments by directly loading the JS stealth scripts from the `playwright-stealth` package.

### Data Files

- `data/products.json`
It keeps a real-time record of the active status of the tracked products.

- `data/price_history.json`
It keeps track of price records over time for each product.

These two files are local runtime data. They are populated as the application runs; it is recommended to also check that their contents are intentionally committed before the push.

### Test and Debug Files

- `tests/test_scraper_properties.py`
Checks whether the Hepsiburada scraper outputs guarantee certain fields using property-based testing logic.

- `test_selectors.py`
This is a debug script prepared for API/selector discovery on the Trendyol side.

- `fiyat_getir_ornek.py`
This is a more general/example prototype version of the scraping logic. It is not mandatory in the production flow but is useful as a reference.

- `scripts/smoke.py`
This is a small smoke test script that quickly validates the project's imports and basic helper flows.

- `api_debug.json`, `debug_html.txt`, `debug_output.txt`, `debug_output2.txt`, `debug_output3.txt`, `test_results.json`
These are past debug and test outputs. They are not mandatory in the application's main runtime flow.

## Supported Platforms

Supported platforms according to codebase:
- Trendyol
- Amazon.com.tr
- Hepsiburada

Note: Backend and UI support is provided for all 3 platforms (Trendyol, Amazon.com.tr, Hepsiburada). Telegram bot commands are also compatible with this list.

## Data Structure

### `products.json`

Each product is stored according to the following logic:
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

Time series records are kept for each product:

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

## Alarm Logic

The application generates an alarm in two situations:

1. If the product price falls below or at the target price.
2. If the new price is lower than the previously recorded price.

When the alarm is triggered:

- If email settings are available, an email is sent via Gmail.
- If Telegram settings are available, a Telegram message is sent.

## Environment Variables

Environment variables used according to the `.env.example` file:

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

### Meaning of Variables

- `TELEGRAM_BOT_TOKEN`
Telegram bot token. If left blank, the bot will not activate.

- `TELEGRAM_CHAT_ID`
Chat ID to which notifications will be sent.

- `GMAIL_ADDRESS`
Sender's Gmail address.

- `GMAIL_APP_PASSWORD`
Application password for Gmail. Normal account password is not used.

- `NOTIFICATION_EMAIL`
Recipient's email address to which notifications will be sent.

- `SCRAPE_INTERVAL_HOURS`
How often the automatic price check will be performed (in hours).

- `HEADLESS_BROWSER`
If `true`, the browser opens in the background. If `false`, the browser is visible.

- `FLASK_SECRET_KEY`
Secret key for Flask sessions/Flash messages.

- `FLASK_PORT`
Port for the web interface to run on.

- `FLASK_DEBUG`
Turns Flask debug mode on/off.

## How Do I Run the Project?

The following steps provide the correct startup flow for this project.

### 1. Open the repository
```powershell
cd C:\Users\mertadores\Documents\Smart-Price-Tracking-and-Notification-System
```

### 2. Create a virtual environment.

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment.

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

### 4. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 5. Install the Playwright Browser

This step is very important. The `playwright` package alone is not sufficient; the Chromium browser binary must also be installed.

```powershell
python -m playwright install chromium
```

For system dependencies, if necessary:

```powershell
python -m playwright install
```

### 6. Create the Environment File

Copy the `.env.example` file and save it as `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Next, open the `.env` file and fill in the required fields.

Generally, the following fields are sufficient for minimum requirements:

```env
SCRAPE_INTERVAL_HOURS=6
HEADLESS_BROWSER=true
FLASK_SECRET_KEY=buraya_guclu_bir_key_yazin
FLASK_PORT=5000
FLASK_DEBUG=false
```

Email and Telegram are completely optional.

### 7. Launch the application

```powershell
python main.py
```

After a successful launch, the application typically performs the following actions:

- Prepares the `data/` folder
- Creates the Flask application
- Starts the scheduler
- Launches the bot if a Telegram token exists
- Opens the web server at `http://localhost:5000`

### 8. Open in browser

```text
http://localhost:5000
```

## How to Use the Application After Opening?

### Web Interface

1. Enter the product URL on the main page.
2. Add a target price if desired.
3. Click the `Follow` button.
4. The product will be added to your watchlist.
5. You can check the price in real-time with `Manual Check`.
6. You can update existing records from the target price field.
7. You can search for the same product on different platforms from the `Compare` page.

### Telegram bot

`.env` dosyasinda Telegram bilgileri varsa bot da ayaga kalkar.

Example usage:

```text
/ekle https://www.trendyol.com/...
/ekle https://www.amazon.com.tr/... 15000
/liste
/kontrol
/sil 1
```

## Flask Routes

Main endpoints defined in the codebase:

- `GET /`
Main tracking panel

- `POST /add`
Adds the new product to the watchlist

- `POST /remove/<product_id>`
Removes the product from the watchlist

- `POST /target/<product_id>`
Updates the target price

- `POST /check`
Performs a manual price check

- `GET /api/history/<product_id>`
Returns the product's price history as JSON

- `GET /compare`
Price comparison page

- `POST /compare/search`
Searches for comparison

- `POST /compare/add`
Aims to add a product from the comparison result to the watchlist

## How to Run Tests?

Test dependencies are defined in `requirements.txt`. To run the tests after installation:

```powershell
pytest -q
```
For a quick health check:

```powershell
python scripts/smoke.py
```

My quick verification of the current repository:

- The command `python -m compileall .` ran successfully.

This shows that the files can be compiled, at least in Python syntax.

## Architectural Notes

- The application uses JSON files instead of a database.
- Therefore, it is more suitable for single-user/small-scale local use.
- On the scraping side, `stealth` logic is used to bypass anti-bot protections.
- `search_engine.py` gets the headless setting from `config.HEADLESS_BROWSER`; by default it is `True` (no visible window opens). If you experience problems on bot-protected sites, you can set `HEADLESS_BROWSER=false` in `.env`. - Flask uses `use_reloader=False` in `main.py`; this is done to prevent scheduler crashes.

## Important Limitations

- The selector or parse logic may break when e-commerce sites change their HTML structures.
- Scraping may not always be 100% stable due to anti-bot systems.
- The `products.json` and `price_history.json` files are not suitable for simultaneous and high-traffic use.
- The scheduler runs at specific intervals by default; it does not perform an automatic initial scan as soon as the application starts. You can use `Manual Control` for this.

## Short Startup Summary

If you only want a quick start:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
python main.py
```
Then:

```text
http://localhost:5000
```

## Result

The current goal of this project is to track products from multiple e-commerce platforms from a single location, record price movements, and inform the user in a timely manner. The code structure is divided into web interface + scraping + scheduler + notification services, providing a suitable foundation for small/medium-scale individual use cases.
