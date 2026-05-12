# Short API Documentation

## 1. Short Project Overview

Smart Price Tracking and Notification System is a Python project for tracking product prices on e-commerce websites, defining target prices, storing price history, and notifying the user when prices drop.

Main technologies used:

- Flask: Web UI and endpoints.
- Playwright + playwright-stealth: Product scraping from Trendyol, Amazon.com.tr, and Hepsiburada.
- APScheduler: Automatic scheduled price checks.
- python-telegram-bot: Telegram bot commands and Telegram notifications.
- Gmail SMTP: Email notifications.
- JSON files: Product and price history storage.

The project has a web interface. The user can add, list, remove, and update tracked products, set target prices, run manual price checks, and use the product comparison page.

The project has a Telegram bot. The bot can add products, list products, remove products, run manual checks, and show the current chat ID.

The project has email notifications. When a price alert is created, an email is sent if Gmail SMTP settings are configured.

The project has a scheduler. The background scheduler starts when the application starts and checks products periodically based on `SCRAPE_INTERVAL_HOURS`. The default value is 6 hours.

## 2. Running and Environment Information

Local run command:

```powershell
python main.py
```

Local base URL:

```text
http://localhost:5000
```

The port can be changed with `FLASK_PORT` in `.env`. The default port is `5000`.

Required or optional `.env` variables:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Used to run the Telegram bot. If empty, the bot is disabled. |
| `TELEGRAM_CHAT_ID` | Telegram chat ID where scheduler notifications are sent. |
| `GMAIL_ADDRESS` | Sender Gmail address. |
| `GMAIL_APP_PASSWORD` | Gmail app password. |
| `NOTIFICATION_EMAIL` | Recipient email address for notifications. |
| `SCRAPE_INTERVAL_HOURS` | Automatic price check interval. Default: `6`. |
| `HEADLESS_BROWSER` | Whether the browser runs in the background. Default: `true`. |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions/flash messages. |
| `FLASK_PORT` | Flask web port. Default: `5000`. |
| `FLASK_DEBUG` | Flask debug mode. |

Real tokens, passwords, or private `.env` values should not be written into documentation.

## 3. Web Endpoint Summary

| Method | Endpoint | Description | Parameters |
|---|---|---|---|
| `GET` | `/` | Shows the main tracking dashboard. | None |
| `POST` | `/add` | Adds a product from the submitted URL form. | Form: `url`, optional `target_price` |
| `POST` | `/remove/<product_id>` | Removes a product from the tracking list. | Path: `product_id` |
| `POST` | `/target/<product_id>` | Updates the target price for a product. | Path: `product_id`, Form: `target_price` |
| `POST` | `/check` | Starts a manual price check. | None |
| `GET` | `/api/history/<product_id>` | Returns product price history and statistics as JSON. | Path: `product_id` |
| `GET` | `/compare` | Shows the product comparison page. | None |
| `POST` | `/compare/search` | Searches for a product name on Trendyol, Amazon.com.tr, and Hepsiburada. | JSON: `query` |
| `POST` | `/compare/add` | Adds a comparison result to the tracking list. | JSON: `id` or `product_id`, `url`, `title`, `platform`, `image_url`, `price`, optional `target_price` |

## 4. Telegram Bot Commands

| Command | Usage | Description |
|---|---|---|
| `/start` | `/start` | Sends a welcome message and command list. |
| `/yardim` | `/yardim` | Shows the help message. |
| `/help` | `/help` | Shows the help message. |
| `/chatid` | `/chatid` | Shows the current Telegram chat ID. |
| `/ekle` | `/ekle <url> [target_price]` | Validates a product URL, scrapes it, and adds it to the tracking list. |
| `/liste` | `/liste` | Lists tracked products. |
| `/sil` | `/sil <item_number>` | Removes a product by its list number. |
| `/kontrol` | `/kontrol` | Runs a manual price check for all tracked products. |

## 5. Main Service Functions

| File | Function | Purpose |
|---|---|---|
| `app/web.py` | `create_app()` | Creates the Flask app and routes. |
| `app/services.py` | `add_tracked_product()` | Validates a URL, scrapes the product, and adds it to the tracking list. |
| `app/services.py` | `check_all_tracked_products()` | Checks all tracked products again and returns generated alerts. |
| `app/services.py` | `acknowledge_alert()` / `acknowledge_alerts()` | Records cooldown state for alerts that were shown or sent. |
| `app/logic.py` | `PriceTracker.add_product()` | Adds or updates a product record. |
| `app/logic.py` | `PriceTracker.remove_product()` | Removes a product and its price history. |
| `app/logic.py` | `PriceTracker.update_price()` | Stores the latest price and checks whether an alert should be created. |
| `app/logic.py` | `PriceTracker.set_target_price()` | Updates the target price for a product. |
| `app/scraper.py` | `scrape_product_url()` | Scrapes product information from a single product URL. |
| `app/scraper.py` | `get_scraper()` | Selects the correct scraper class based on the URL domain. |
| `app/search_engine.py` | `SearchEngine.search_all()` | Searches products on the three supported platforms concurrently. |
| `app/telegram_bot.py` | `create_telegram_app()` | Creates the Telegram bot application and command handlers. |
| `app/telegram_bot.py` | `send_telegram_alert()` | Sends a price alert to Telegram. |
| `app/email_service.py` | `send_price_alert_email()` | Sends a price alert email through Gmail SMTP. |
| `app/scheduler.py` | `start_scheduler()` | Starts the periodic price check job. |
| `app/scheduler.py` | `trigger_manual_check()` | Runs a manual price check from the web interface. |
| `utils/security.py` | `validate_url()` | Checks whether a URL is valid and belongs to a supported platform. |
| `utils/security.py` | `generate_product_id()` | Generates a unique product ID from a URL. |

## 6. Price Check and Notification Flow

- The user adds a product from the web interface or with the Telegram `/ekle` command.
- The system validates the product URL.
- `scrape_product_url()` fetches product title, price, image, platform, and stock information.
- Product information is stored in JSON files through `PriceTracker`.
- If the user entered a target price, it is stored as `target_price`.
- When a manual check or scheduled check runs, all tracked products are scraped again.
- The new price is compared with the previous price and the target price.
- If the price reaches the target or drops below the previous price, an alert is created.
- If the scheduler creates an alert, it tries to send email and Telegram notifications.
- In the web manual check flow, alert results are shown as flash messages.
- In the Telegram `/kontrol` flow, alert messages are sent to the same Telegram conversation.

## 7. Data Storage

Data is stored in JSON files:

| File | Description |
|---|---|
| `data/products.json` | Stores active tracked product records. |
| `data/price_history.json` | Stores price history records for products. |

A product record usually contains these fields:

```json
{
  "url": "https://...",
  "title": "Product title",
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

Price history records usually contain `price`, `in_stock`, and `timestamp` fields.

## 8. Short Limitations / Unclear Points

- The project is not designed as a full REST API; it is mostly a Flask HTML form based web application.
- JSON endpoints are limited and are mainly used for price history and the comparison page.
- Data is stored in JSON files, so it may not be suitable for high-concurrency or multi-user production usage.
- Scrapers depend on the HTML/API structure of e-commerce websites; scraping can fail if those websites change.
- Telegram and email notifications can be disabled or fail silently if `.env` settings are missing.
- The scheduler runs every 6 hours by default; it does not automatically run the first check immediately when the app starts.
