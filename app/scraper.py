"""
Playwright + Stealth tabanlı Web Scraper Modülü.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Trendyol ve Amazon.com.tr gibi anti-bot korumalı e-ticaret sitelerinden
ürün fiyatı, başlık ve görsel URL'si çeker.

requests kütüphanesi KULLANILMAZ — tüm HTTP işlemleri
Playwright tarayıcı otomasyonu üzerinden yapılır.
playwright-stealth ile bot tespiti engellenir.
"""

import asyncio
import logging
import random
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth.stealth import Stealth

from utils.security import detect_platform, sanitize_url

logger = logging.getLogger(__name__)

# ── User-Agent Havuzu ─────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
]


# ══════════════════════════════════════════════════════════
#  Base Scraper
# ══════════════════════════════════════════════════════════
class StealthScraper(ABC):
    """
    Playwright + playwright-stealth tabanlı soyut (abstract) scraper.
    Her e-ticaret platformu bu sınıftan türetilir.
    """

    PLATFORM: str = ""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    # ── Tarayıcı Yaşam Döngüsü ───────────────────────────

    async def launch(self) -> None:
        """Playwright tarayıcısını stealth modda başlatır."""
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--disable-extensions",
            ],
        )

        # Gerçekçi tarayıcı profili oluştur
        self._context = await self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            # Gerçekçi ekran ve donanım bilgileri
            screen={"width": 1920, "height": 1080},
            color_scheme="light",
            java_script_enabled=True,
            accept_downloads=False,
            extra_http_headers={
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        logger.info(f"[{self.PLATFORM}] Stealth tarayıcı başlatıldı (headless={self.headless})")

    async def _create_stealth_page(self) -> Page:
        """Stealth patch uygulanmış yeni bir sayfa oluşturur."""
        if not self._context:
            await self.launch()

        page = await self._context.new_page()

        # playwright-stealth patch'ini uygula
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        # Ek anti-detection önlemleri
        await page.add_init_script("""
            // WebDriver property'sini gizle
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Chrome runtime objesini simüle et
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // Permissions API'yi override et
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Plugins dizisini doldur
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['tr-TR', 'tr', 'en-US', 'en']
            });
        """)

        return page

    async def close(self) -> None:
        """Tarayıcı kaynaklarını serbest bırakır."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            logger.info(f"[{self.PLATFORM}] Tarayıcı kapatıldı.")
        except Exception as e:
            logger.warning(f"[{self.PLATFORM}] Tarayıcı kapatılırken hata: {e}")

    # ── İnsan Davranışı Simülasyonu ───────────────────────

    async def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        """Rastgele bekleme süresi (bot tespitini engeller)."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _scroll_page(self, page: Page) -> None:
        """Sayfayı insan gibi kaydırır."""
        for _ in range(random.randint(2, 4)):
            scroll_amount = random.randint(200, 500)
            await page.mouse.wheel(0, scroll_amount)
            await self._human_delay(0.3, 0.8)

    # ── Ana Scraping Metodu ───────────────────────────────

    async def scrape_product(self, url: str) -> dict:
        """
        Verilen URL'den ürün bilgilerini çeker.

        Returns:
            dict: Ürün bilgileri (title, price, currency, image_url, vb.)

        Raises:
            ScraperError: Scraping başarısız olduğunda.
        """
        url = sanitize_url(url)
        page = None

        try:
            page = await self._create_stealth_page()

            logger.info(f"[{self.PLATFORM}] Sayfa yükleniyor: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Sayfanın tamamen yüklenmesini bekle
            await self._human_delay(2.0, 4.0)

            # Sayfayı kaydır (lazy-loaded görseller için)
            await self._scroll_page(page)
            await self._human_delay(1.0, 2.0)

            # Platforma özel parsing
            product_data = await self.parse_product(page)

            # Ortak meta verileri ekle
            product_data.update({
                "url": url,
                "platform": self.PLATFORM,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

            logger.info(
                f"[{self.PLATFORM}] Başarılı: {product_data.get('title', 'N/A')[:50]}... "
                f"→ {product_data.get('price', 'N/A')} {product_data.get('currency', '')}"
            )

            return product_data

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] Scraping hatası ({url}): {e}")
            raise ScraperError(f"[{self.PLATFORM}] {url} scrape edilemedi: {e}") from e

        finally:
            if page:
                await page.close()

    # ── Alt Sınıfların Uygulaması Gereken Metot ──────────

    @abstractmethod
    async def parse_product(self, page: Page) -> dict:
        """
        Sayfadan ürün bilgilerini çıkarır.
        Her platform kendi CSS selektörlerini burada tanımlar.
        """
        ...


# ══════════════════════════════════════════════════════════
#  Trendyol Scraper
# ══════════════════════════════════════════════════════════
class TrendyolScraper(StealthScraper):
    """
    Trendyol.com için özelleştirilmiş scraper.

    Trendyol micro-frontend (SPA) mimarisi kullandığından ürün bilgileri
    standart HTML'de bulunmaz. Strateji:
    1. Sayfaya giderek cookie/session oluştur (anti-bot bypass)
    2. Trendyol'un dahili API'sine browser context üzerinden istek at
    3. API başarısız olursa, page title'dan fallback parsing yap
    """

    PLATFORM = "trendyol"

    # Trendyol dahili API endpoint
    API_BASE = "https://public.trendyol.com/discovery-sfint-productgw-service/api/productDetail"

    @staticmethod
    def _extract_content_id(url: str) -> Optional[str]:
        """URL'den Trendyol content (product) ID'sini çıkarır.
        Örnek: https://www.trendyol.com/apple/iphone-15-128-gb-p-782425137
        → '782425137'
        """
        match = re.search(r"-p-(\d+)", url)
        return match.group(1) if match else None

    async def parse_product(self, page: Page) -> dict:
        """
        Trendyol ürün bilgilerini hibrit yöntemle çeker:
        1. Önce API'den JSON veri al (en güvenilir)
        2. Başarısız olursa page title + meta tag'lerden parse et
        """
        url = page.url

        # Yöntem 1: Dahili API üzerinden veri çek
        content_id = self._extract_content_id(url)
        if content_id:
            api_data = await self._fetch_from_api(page, content_id)
            if api_data:
                return api_data

        logger.warning("[trendyol] API başarısız, fallback parsing yapılıyor...")

        # Yöntem 2: Page title + meta tag'lerden fallback
        return await self._fallback_parse(page)

    async def _fetch_from_api(self, page: Page, content_id: str) -> Optional[dict]:
        """
        Trendyol'un ürün verilerini iki yöntemle çeker:
        1. Playwright context.request ile API (CORS yok)
        2. Window objesinden fragment verilerini oku
        """
        # Yöntem A: Micro-frontend fragment'tan window data çek
        try:
            fragment_data = await page.evaluate("""() => {
                // Trendyol fragment verilerini window'a koyar
                const keys = Object.keys(window).filter(k =>
                    k.includes('PROPS') && (k.includes('product') || k.includes('key-info') || k.includes('actions'))
                );
                const result = {};
                for (const k of keys) {
                    try { result[k] = window[k]; } catch(e) {}
                }
                return result;
            }""")

            if fragment_data:
                parsed = self._parse_fragment_data(fragment_data, content_id)
                if parsed and parsed.get("price"):
                    logger.info(f"[trendyol] Fragment verisi başarılı: {parsed.get('title', 'N/A')[:50]}")
                    return parsed
        except Exception as e:
            logger.debug(f"[trendyol] Fragment veri hatası: {e}")

        # Yöntem B: Playwright context.request ile API çağrısı (CORS kısıtlaması yok)
        if self._context:
            api_urls = [
                f"https://apigw.trendyol.com/discovery-sfint-productgw-service/api/productDetail/{content_id}",
                f"https://public-mdc.trendyol.com/discovery-sfint-productgw-service/api/productDetail/{content_id}",
            ]
            for api_url in api_urls:
                try:
                    resp = await self._context.request.get(api_url, headers={
                        "Accept": "application/json",
                        "storefrontId": "1",
                        "culture": "tr-TR",
                        "Referer": "https://www.trendyol.com/",
                        "Origin": "https://www.trendyol.com",
                    })
                    if resp.ok:
                        data = await resp.json()
                        if data and "result" in data:
                            return self._parse_api_response(data["result"])
                except Exception as e:
                    logger.debug(f"[trendyol] API hatası ({api_url}): {e}")

        return None

    @staticmethod
    def _parse_fragment_data(fragment_data: dict, content_id: str) -> Optional[dict]:
        """Trendyol micro-frontend fragment verilerinden ürün bilgisi çıkarır."""
        import json as _json

        # Fragment key'lerinden ürün bilgisi ara
        for key, value in fragment_data.items():
            if not isinstance(value, dict):
                continue

            # product key-info fragment'ı kontrol
            product = value.get("product") or value.get("productDetail") or value
            if not product:
                continue

            name = product.get("name") or product.get("productName") or ""
            if not name:
                continue

            # Fiyat bilgisi
            price = None
            price_info = product.get("price", {})
            if isinstance(price_info, dict):
                price = (
                    price_info.get("sellingPrice")
                    or price_info.get("discountedPrice")
                    or price_info.get("originalPrice")
                )

            brand_info = product.get("brand", {})
            brand = brand_info.get("name", "") if isinstance(brand_info, dict) else ""

            # Görsel
            images = product.get("images", [])
            image_url = None
            if images:
                img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
                if img and not img.startswith("http"):
                    img = f"https://cdn.dsmcdn.com{img}"
                image_url = img

            title = f"{brand} {name}".strip() if brand else name

            return {
                "title": title or "Başlık bulunamadı",
                "brand": brand,
                "price": price,
                "currency": "TRY",
                "image_url": image_url,
                "in_stock": product.get("inStock", True),
                "rating": None,
            }

    @staticmethod
    def _parse_api_response(result: dict) -> Optional[dict]:
        """Trendyol API JSON yanıtından ürün bilgisi çıkarır."""
        # Fiyat
        price = None
        try:
            price_info = result.get("price", {})
            price = (
                price_info.get("sellingPrice")
                or price_info.get("discountedPrice")
                or price_info.get("originalPrice")
            )
        except (TypeError, KeyError):
            pass

        # Görsel
        image_url = None
        try:
            images = result.get("images", [])
            if images:
                img = images[0] if isinstance(images[0], str) else images[0].get("url", "")
                if img and not img.startswith("http"):
                    img = f"https://cdn.dsmcdn.com{img}"
                image_url = img
        except (IndexError, TypeError):
            pass

        # Başlık
        name = result.get("name", "")
        brand = result.get("brand", {}).get("name", "") if isinstance(result.get("brand"), dict) else ""
        title = f"{brand} {name}".strip() if brand else name

        # Stok
        in_stock = result.get("inStock", True)

        # Rating
        rating = None
        try:
            rating_data = result.get("ratingScore", {})
            if rating_data:
                rating = rating_data.get("averageRating")
        except (TypeError, KeyError):
            pass

        return {
            "title": title or "Başlık bulunamadı",
            "brand": brand,
            "price": price,
            "currency": "TRY",
            "image_url": image_url,
            "in_stock": in_stock,
            "rating": rating,
        }

    async def _fallback_parse(self, page: Page) -> dict:
        """
        API başarısız olduğunda page title ve meta tag'lerden veri çıkarır.
        Trendyol page title formatı: "Ürün Adı Fiyatı, Yorumları - Trendyol"
        """
        page_title = await page.title()
        title = page_title

        # Title'dan "Fiyatı, Yorumları - Trendyol" kısmını temizle
        if title:
            title = re.sub(r"\s*Fiyatı,?\s*Yorumları\s*-?\s*Trendyol\s*$", "", title, flags=re.IGNORECASE).strip()

        # Meta description'dan fiyat aramayı dene
        price = None
        try:
            meta_desc = await page.evaluate(
                "() => document.querySelector('meta[name=\"description\"]')?.content || ''"
            )
            if meta_desc:
                price_match = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*TL", meta_desc)
                if price_match:
                    price = self._parse_price_text(price_match.group(0))
        except Exception:
            pass

        # og:image meta tag'inden görsel URL al
        image_url = None
        try:
            image_url = await page.evaluate(
                "() => document.querySelector('meta[property=\"og:image\"]')?.content || ''"
            )
        except Exception:
            pass

        return {
            "title": title or "Başlık bulunamadı",
            "brand": None,
            "price": price,
            "currency": "TRY",
            "image_url": image_url or None,
            "in_stock": True,
            "rating": None,
        }

    async def search_products(self, page: Page, query: str) -> list[dict]:
        """Trendyol arama sonuçlarından top 3 ürün çeker."""
        from urllib.parse import quote_plus

        search_url = f"https://www.trendyol.com/sr?q={quote_plus(query)}"
        results = []

        try:
            # networkidle ile tam yüklenmeyi bekle (Cloudflare challenge geçmek için)
            await page.goto(search_url, wait_until="networkidle", timeout=45000)
            await self._human_delay(2.0, 4.0)
            await self._scroll_page(page)
            await self._human_delay(1.0, 2.0)

            # Cloudflare / bot-detection kontrolü
            title_check = await page.title()
            if "attention required" in title_check.lower() or "cloudflare" in title_check.lower():
                logger.warning("[trendyol] Cloudflare engeli tespit edildi.")
                return results

            # Trendyol'da ürün kartı = a[data-testid=product-card] (kart kendisi bir link)
            cards = await page.query_selector_all("a[data-testid=product-card]")
            logger.info(f"[trendyol] {len(cards)} ürün kartı bulundu.")

            for card in cards[:3]:
                try:
                    # Link — kartın kendi href'i
                    href = await card.get_attribute("href") or ""
                    url = href if href.startswith("http") else f"https://www.trendyol.com{href}"

                    # Başlık
                    title_el = await card.query_selector(".product-name, [class*=product-name]")
                    title = (await title_el.inner_text()).strip() if title_el else ""

                    # Fiyat — .single-price (gerçek satış fiyatı)
                    price_el = await card.query_selector(".single-price, [class*=single-price]")
                    if not price_el:
                        price_el = await card.query_selector(".price-section, [class*=price-section]")
                    price_text = (await price_el.inner_text()).strip() if price_el else ""
                    price = self._parse_price_text(price_text)

                    # Görsel
                    img_el = await card.query_selector("img[data-testid=image-img], img")
                    image_url = None
                    if img_el:
                        src = await img_el.get_attribute("src")
                        if src and src.startswith("http"):
                            image_url = src

                    if title:
                        results.append({
                            "title": title,
                            "price": price,
                            "currency": "TRY",
                            "url": url,
                            "image_url": image_url,
                            "platform": self.PLATFORM,
                            "in_stock": True,
                        })
                except Exception as e:
                    logger.debug(f"[trendyol] Kart parse hatası: {e}")
                    continue
        except Exception as e:
            logger.error(f"[trendyol] Arama hatası: {e}")

        return results

    @staticmethod
    def _parse_price_text(text: str) -> Optional[float]:
        """Fiyat metnini float'a çevirir: '1.299,99 TL' → 1299.99"""
        if not text:
            return None
        cleaned = re.sub(r"[^\d.,]", "", text)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None


# ══════════════════════════════════════════════════════════
#  Amazon Scraper
# ══════════════════════════════════════════════════════════
class AmazonScraper(StealthScraper):
    """Amazon.com.tr için özelleştirilmiş scraper."""

    PLATFORM = "amazon"

    # Amazon CSS Selektörleri
    SELECTORS = {
        "title": "#productTitle",
        "price_whole": "span.a-price-whole",
        "price_fraction": "span.a-price-fraction",
        "price_symbol": "span.a-price-symbol",
        "price_deal": "#dealprice_feature div span.a-offscreen",
        "price_our": "#ourprice_feature div span.a-offscreen",
        "price_block": "span.a-price span.a-offscreen",
        "image": "#landingImage",
        "image_alt": "#imgBlkFront",
        "brand": "#bylineInfo",
        "rating": "span.a-icon-alt",
        "review_count": "#acrCustomerReviewText",
        "availability": "#availability span",
        "in_stock_btn": "#add-to-cart-button",
    }

    async def parse_product(self, page: Page) -> dict:
        """Amazon ürün sayfasını parse eder."""

        # CAPTCHA kontrolü
        if await self._check_captcha(page):
            logger.warning("[amazon] CAPTCHA tespit edildi. Sayfayı yeniden yükleniyor...")
            await self._human_delay(3.0, 6.0)
            await page.reload(wait_until="domcontentloaded")
            await self._human_delay(2.0, 4.0)

        # Ürün başlığı
        title = await self._get_text(page, self.SELECTORS["title"])

        # Marka
        brand = await self._get_text(page, self.SELECTORS["brand"])

        # Fiyat
        price = await self._extract_price(page)

        # Ürün görseli
        image_url = await self._get_image_url(page)

        # Stok durumu
        in_stock = await self._check_stock(page)

        # Değerlendirme
        rating = await self._get_text(page, self.SELECTORS["rating"])

        return {
            "title": title or "Başlık bulunamadı",
            "brand": brand,
            "price": price,
            "currency": "TRY",
            "image_url": image_url,
            "in_stock": in_stock,
            "rating": self._parse_rating(rating),
        }

    async def _check_captcha(self, page: Page) -> bool:
        """CAPTCHA sayfası olup olmadığını kontrol eder."""
        try:
            captcha = await page.query_selector("form[action*='validateCaptcha']")
            return captcha is not None
        except Exception:
            return False

    async def _extract_price(self, page: Page) -> Optional[float]:
        """Amazon fiyat bilgisini çeker."""
        # Yöntem 1: a-offscreen fiyat (en güvenilir)
        for selector in [
            self.SELECTORS["price_deal"],
            self.SELECTORS["price_our"],
            self.SELECTORS["price_block"],
        ]:
            price_text = await self._get_text(page, selector)
            if price_text:
                parsed = self._parse_price_text(price_text)
                if parsed:
                    return parsed

        # Yöntem 2: whole + fraction birleştir
        whole = await self._get_text(page, self.SELECTORS["price_whole"])
        fraction = await self._get_text(page, self.SELECTORS["price_fraction"])
        if whole:
            whole_clean = whole.replace(".", "").replace(",", "").strip()
            fraction_clean = (fraction or "00").strip()
            try:
                return float(f"{whole_clean}.{fraction_clean}")
            except ValueError:
                pass

        return None

    async def _get_image_url(self, page: Page) -> Optional[str]:
        """Ürün görsel URL'sini çeker."""
        for selector in [self.SELECTORS["image"], self.SELECTORS["image_alt"]]:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Amazon görselleri genelde 'src' veya 'data-old-hires' attribute'unda
                    for attr in ["data-old-hires", "src"]:
                        src = await element.get_attribute(attr)
                        if src and src.startswith("http"):
                            return src
            except Exception:
                continue
        return None

    async def _check_stock(self, page: Page) -> bool:
        """Stok durumunu kontrol eder."""
        # "Sepete Ekle" butonu varsa stokta
        add_btn = await page.query_selector(self.SELECTORS["in_stock_btn"])
        if add_btn:
            return True

        # Availability text'ini kontrol et
        avail_text = await self._get_text(page, self.SELECTORS["availability"])
        if avail_text:
            lower = avail_text.lower()
            if "stokta" in lower or "stock" in lower:
                return True
            if "tükendi" in lower or "unavailable" in lower:
                return False

        return False

    @staticmethod
    async def _get_text(page: Page, selector: str) -> Optional[str]:
        """CSS selektöründen metin çıkarır."""
        try:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
                return text.strip() if text else None
        except Exception:
            return None
        return None

    async def search_products(self, page: Page, query: str) -> list[dict]:
        """Amazon arama sonuçlarından top 3 ürün çeker."""
        from urllib.parse import quote_plus

        search_url = f"https://www.amazon.com.tr/s?k={quote_plus(query)}"
        results = []

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await self._human_delay(2.0, 3.0)
            await self._scroll_page(page)
            await self._human_delay(1.0, 2.0)

            # CAPTCHA kontrolü
            if await self._check_captcha(page):
                logger.warning("[amazon] Arama sayfasında CAPTCHA tespit edildi.")
                return results

            # Ürün kartlarını seç
            card_selectors = [
                "[data-component-type='s-search-result']",
                ".s-result-item[data-asin]",
            ]
            cards = []
            for selector in card_selectors:
                cards = await page.query_selector_all(selector)
                # Gerçek ürün kartlarını filtrele (reklam olmayan, ASIN'i olan)
                cards = [c for c in cards if await c.get_attribute("data-asin")]
                if cards:
                    break

            for card in cards[:3]:
                try:
                    # Başlık
                    title_el = await card.query_selector("h2 a span, .a-size-medium, .a-size-base-plus")
                    title = (await title_el.inner_text()).strip() if title_el else ""

                    # Fiyat
                    price = None
                    price_el = await card.query_selector(".a-offscreen")
                    if price_el:
                        price_text = await price_el.inner_text()
                        price = self._parse_price_text(price_text.strip())
                    if price is None:
                        whole_el = await card.query_selector(".a-price-whole")
                        if whole_el:
                            whole_text = (await whole_el.inner_text()).strip()
                            price = self._parse_price_text(whole_text)

                    # Link
                    link_el = await card.query_selector("h2 a[href]")
                    href = await link_el.get_attribute("href") if link_el else ""
                    url = href if href.startswith("http") else f"https://www.amazon.com.tr{href}"

                    # Görsel
                    img_el = await card.query_selector(".s-image, img")
                    image_url = None
                    if img_el:
                        src = await img_el.get_attribute("src")
                        if src and src.startswith("http"):
                            image_url = src

                    if title:
                        results.append({
                            "title": title,
                            "price": price,
                            "currency": "TRY",
                            "url": url,
                            "image_url": image_url,
                            "platform": self.PLATFORM,
                            "in_stock": True,
                        })
                except Exception as e:
                    logger.debug(f"[amazon] Kart parse hatası: {e}")
                    continue
        except Exception as e:
            logger.error(f"[amazon] Arama hatası: {e}")

        return results

    @staticmethod
    def _parse_price_text(text: str) -> Optional[float]:
        """Amazon fiyat metnini float'a çevirir: '1.299,99 TL' → 1299.99"""
        if not text:
            return None
        cleaned = re.sub(r"[^\d.,]", "", text)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _parse_rating(text: Optional[str]) -> Optional[float]:
        """Amazon rating metninden puanı çıkarır: '4,5/5 yıldız' → 4.5"""
        if not text:
            return None
        match = re.search(r"([\d,\.]+)", text)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                pass
        return None


# ══════════════════════════════════════════════════════════
#  Hepsiburada Scraper
# ══════════════════════════════════════════════════════════
class HepsiburadaScraper(StealthScraper):
    """Hepsiburada.com için özelleştirilmiş scraper."""

    PLATFORM = "hepsiburada"

    SELECTORS = {
        "title": "h1[data-bind*='name'], [data-test-id='title'], h1.product-name",
        "price": "[data-bind*='finalPrice'], span[class*='price-value'], [data-test-id='price-current-price']",
        "image": "img[data-bind*='src'], .product-image img, [data-test-id='product-image'] img",
        "in_stock": "[data-test-id='add-to-cart'], #addToCart",
        "search_cards": "li[data-bind*='product'], [data-test-id='product-card'], .product-list-item",
    }

    async def parse_product(self, page: Page) -> dict:
        """Hepsiburada ürün detay sayfasını parse eder."""

        # CAPTCHA / bot-detection kontrolü
        if await self._check_captcha(page):
            logger.warning("[hepsiburada] CAPTCHA tespit edildi, boş sonuç dönülüyor.")
            return {
                "title": "",
                "price": None,
                "currency": "TRY",
                "image_url": None,
                "in_stock": False,
                "rating": None,
                "error": "captcha",
            }

        title = await self._get_text(page, self.SELECTORS["title"])
        price = await self._extract_price(page)
        image_url = await self._get_image_url(page)
        in_stock = await self._check_stock(page)

        return {
            "title": title or "Başlık bulunamadı",
            "price": price,
            "currency": "TRY",
            "image_url": image_url,
            "in_stock": in_stock,
            "rating": None,
        }

    async def search_products(self, page: Page, query: str) -> list[dict]:
        """Hepsiburada arama sonuçlarından top 3 ürün çeker."""
        from urllib.parse import quote_plus

        search_url = f"https://www.hepsiburada.com/ara?q={quote_plus(query)}"
        results = []

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await self._human_delay(3.0, 5.0)
            await self._scroll_page(page)
            await self._human_delay(1.0, 2.0)

            # Bot-detection / güvenlik sayfası kontrolü
            title_check = await page.title()
            if "güvenlik" in title_check.lower() or "security" in title_check.lower():
                logger.warning("[hepsiburada] Güvenlik sayfası tespit edildi.")
                return results

            # Güncel selektörler (2025 Hepsiburada HTML yapısı)
            # article[class*=productCard-module_article] veya li[class*=productListContent]
            cards = await page.query_selector_all("article[class*=productCard-module_article]")
            if not cards:
                cards = await page.query_selector_all("li[class*=productListContent]")
            logger.info(f"[hepsiburada] {len(cards)} ürün kartı bulundu.")

            for card in cards[:3]:
                try:
                    # Başlık — h2 elementi
                    title_el = await card.query_selector("h2, h3, [class*=productName]")
                    title = (await title_el.inner_text()).strip() if title_el else ""

                    # Fiyat — price-module_finalPrice
                    price_el = await card.query_selector(
                        "[class*=price-module_finalPrice], [class*=finalPrice], [class*=priceInfo]"
                    )
                    if not price_el:
                        price_el = await card.query_selector("[class*=price]")
                    price_text = (await price_el.inner_text()).strip() if price_el else ""
                    price = self._parse_price_text(price_text)

                    # Link
                    link_el = await card.query_selector("a[href]")
                    href = await link_el.get_attribute("href") if link_el else ""
                    url = href if href.startswith("http") else f"https://www.hepsiburada.com{href}"

                    # Görsel
                    img_el = await card.query_selector("img")
                    image_url = None
                    if img_el:
                        src = await img_el.get_attribute("src")
                        if src and src.startswith("http"):
                            image_url = src

                    if title:
                        results.append({
                            "title": title,
                            "price": price,
                            "currency": "TRY",
                            "url": url,
                            "image_url": image_url,
                            "platform": self.PLATFORM,
                            "in_stock": True,
                        })
                except Exception as e:
                    logger.debug(f"[hepsiburada] Kart parse hatası: {e}")
                    continue
        except Exception as e:
            logger.error(f"[hepsiburada] Arama hatası: {e}")

        return results

    async def _check_captcha(self, page: Page) -> bool:
        """CAPTCHA sayfası kontrolü."""
        try:
            url = page.url
            return "captcha" in url.lower() or "robot" in url.lower()
        except Exception:
            return False

    async def _extract_price(self, page: Page) -> Optional[float]:
        """Hepsiburada fiyat bilgisini çeker."""
        price_text = await self._get_text(page, self.SELECTORS["price"])
        if price_text:
            return self._parse_price_text(price_text)
        return None

    async def _get_image_url(self, page: Page) -> Optional[str]:
        """Ürün görsel URL'sini çeker."""
        try:
            el = await page.query_selector(self.SELECTORS["image"])
            if el:
                return await el.get_attribute("src")
        except Exception:
            pass
        return None

    async def _check_stock(self, page: Page) -> bool:
        """Stok durumunu kontrol eder."""
        try:
            btn = await page.query_selector(self.SELECTORS["in_stock"])
            return btn is not None
        except Exception:
            return False

    @staticmethod
    async def _get_text(page: Page, selector: str) -> Optional[str]:
        """CSS selektöründen metin çıkarır (virgülle ayrılmış çoklu selektör destekler)."""
        for sel in selector.split(","):
            sel = sel.strip()
            try:
                el = await page.query_selector(sel)
                if el:
                    text = await el.inner_text()
                    return text.strip() if text else None
            except Exception:
                continue
        return None

    @staticmethod
    def _parse_price_text(text: str) -> Optional[float]:
        """Fiyat metnini float'a çevirir: '1.299,99 TL' → 1299.99"""
        if not text:
            return None
        cleaned = re.sub(r"[^\d.,]", "", text)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None


# ══════════════════════════════════════════════════════════
#  Özel Hata Sınıfı
# ══════════════════════════════════════════════════════════
class ScraperError(Exception):
    """Scraping işlemi sırasında oluşan hata."""
    pass


# ══════════════════════════════════════════════════════════
#  Fabrika Fonksiyonu
# ══════════════════════════════════════════════════════════
_SCRAPER_MAP = {
    "trendyol": TrendyolScraper,
    "amazon": AmazonScraper,
    "hepsiburada": HepsiburadaScraper,
}


def get_scraper(url: str, headless: bool = True) -> StealthScraper:
    """
    URL'ye göre doğru scraper'ı döndürür.

    Args:
        url: Ürün sayfası URL'si
        headless: Tarayıcıyı arka planda çalıştır

    Returns:
        StealthScraper alt sınıfı

    Raises:
        ValueError: Desteklenmeyen platform
    """
    platform = detect_platform(url)
    if not platform or platform not in _SCRAPER_MAP:
        supported = ", ".join(_SCRAPER_MAP.keys())
        raise ValueError(f"Desteklenmeyen platform. Desteklenen: {supported}")

    return _SCRAPER_MAP[platform](headless=headless)


# ══════════════════════════════════════════════════════════
#  Kolaylık Fonksiyonu (Tek Seferlik Scraping)
# ══════════════════════════════════════════════════════════
async def scrape_product_url(url: str, headless: bool = True) -> dict:
    """
    Tek bir URL'den ürün bilgilerini çeker.
    Tarayıcıyı otomatik olarak açar ve kapatır.

    Args:
        url: Ürün sayfası URL'si
        headless: Tarayıcıyı arka planda çalıştır

    Returns:
        dict: Ürün bilgileri

    Kullanım:
        result = await scrape_product_url("https://www.trendyol.com/...")
        print(result["price"], result["title"])
    """
    scraper = get_scraper(url, headless=headless)
    try:
        await scraper.launch()
        return await scraper.scrape_product(url)
    finally:
        await scraper.close()


# ══════════════════════════════════════════════════════════
#  Toplu Scraping (Birden Fazla URL)
# ══════════════════════════════════════════════════════════
async def scrape_multiple_urls(
    urls: list[str],
    headless: bool = True,
    delay_between: tuple[float, float] = (3.0, 7.0),
) -> list[dict]:
    """
    Birden fazla URL'den ürün bilgilerini sırayla çeker.
    Her istek arasında rastgele gecikme ekler.

    Args:
        urls: Ürün URL'leri listesi
        headless: Tarayıcıyı arka planda çalıştır
        delay_between: İstekler arası min/max bekleme (saniye)

    Returns:
        list[dict]: Ürün bilgileri listesi (başarısız olanlar hata mesajı içerir)
    """
    results = []

    # Platform bazında grupla (aynı tarayıcıyı tekrar kullan)
    platform_urls: dict[str, list[str]] = {}
    for url in urls:
        platform = detect_platform(url)
        if platform:
            platform_urls.setdefault(platform, []).append(url)
        else:
            results.append({
                "url": url,
                "error": "Desteklenmeyen platform",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            })

    # Her platform için ayrı scraper kullan
    for platform, platform_url_list in platform_urls.items():
        scraper = _SCRAPER_MAP[platform](headless=headless)
        try:
            await scraper.launch()

            for i, url in enumerate(platform_url_list):
                try:
                    result = await scraper.scrape_product(url)
                    results.append(result)
                except ScraperError as e:
                    results.append({
                        "url": url,
                        "error": str(e),
                        "platform": platform,
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })

                # Son URL değilse gecikme ekle
                if i < len(platform_url_list) - 1:
                    delay = random.uniform(*delay_between)
                    logger.info(f"[{platform}] Sonraki istek için {delay:.1f}s bekleniyor...")
                    await asyncio.sleep(delay)
        finally:
            await scraper.close()

    return results
