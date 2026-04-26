"""
Ürün Arama Motoru
~~~~~~~~~~~~~~~~~
Kullanıcının girdiği ürün adını Trendyol, Amazon.com.tr ve Hepsiburada'da
eş zamanlı olarak arar; sonuçları karşılaştırma için döndürür.
"""

import asyncio
import logging
from urllib.parse import quote_plus

from utils.security import generate_product_id

logger = logging.getLogger(__name__)

# Desteklenen platformlar ve arama URL şablonları
PLATFORM_SEARCH_URLS = {
    "trendyol": "https://www.trendyol.com/sr?q={query}",
    "amazon": "https://www.amazon.com.tr/s?k={query}",
    "hepsiburada": "https://www.hepsiburada.com/ara?q={query}",
}


# ── Yardımcı Fonksiyonlar ─────────────────────────────────

def validate_search_query(query: str) -> bool:
    """
    Arama sorgusunun geçerli olup olmadığını kontrol eder.

    Args:
        query: Kullanıcının girdiği arama metni

    Returns:
        True — sorgu geçerliyse (boş/whitespace değilse)
        False — sorgu boş veya yalnızca whitespace karakterlerinden oluşuyorsa
    """
    if not isinstance(query, str):
        return False
    return bool(query.strip())


def build_search_url(platform: str, query: str) -> str:
    """
    Verilen platform ve sorgu için arama URL'si üretir.

    Args:
        platform: "trendyol", "amazon" veya "hepsiburada"
        query: Arama metni (URL encode edilmemiş)

    Returns:
        Platform'a özgü arama URL'si

    Raises:
        ValueError: Desteklenmeyen platform adı verildiğinde
    """
    platform = platform.lower()
    if platform not in PLATFORM_SEARCH_URLS:
        supported = ", ".join(PLATFORM_SEARCH_URLS.keys())
        raise ValueError(f"Desteklenmeyen platform: '{platform}'. Desteklenen: {supported}")

    encoded_query = quote_plus(query)
    return PLATFORM_SEARCH_URLS[platform].format(query=encoded_query)


def _sort_by_price(items: list) -> list:
    """
    Ürün listesini fiyata göre artan sırada sıralar.
    Fiyatı None olan ürünler listenin sonuna yerleştirilir.

    Args:
        items: SearchResult dict listesi

    Returns:
        Fiyata göre sıralanmış yeni liste
    """
    def sort_key(item: dict):
        price = item.get("price")
        if price is None:
            return (1, 0)  # None fiyatlılar sona
        return (0, price)

    return sorted(items, key=sort_key)


def _find_lowest_price(results: dict) -> str | None:
    """
    Tüm platform sonuçları arasında en düşük fiyatlı ürünün ID'sini bulur.

    Args:
        results: search_all() çıktısı — {"trendyol": [...], "amazon": [...], "hepsiburada": [...]}
                 Her platform için hata durumunda {"error": "...", "results": []} olabilir.

    Returns:
        En düşük fiyatlı ürünün ID'si, ya da hiç fiyatlı ürün yoksa None
    """
    lowest_price: float | None = None
    lowest_id: str | None = None

    for platform, platform_data in results.items():
        # Hata durumunda platform_data bir dict olabilir: {"error": ..., "results": []}
        if isinstance(platform_data, dict) and "error" in platform_data:
            items = platform_data.get("results", [])
        elif isinstance(platform_data, list):
            items = platform_data
        else:
            continue

        for item in items:
            price = item.get("price")
            item_id = item.get("id")
            if price is not None and item_id is not None:
                if lowest_price is None or price < lowest_price:
                    lowest_price = price
                    lowest_id = item_id

    return lowest_id


# ══════════════════════════════════════════════════════════
#  SearchEngine Sınıfı
# ══════════════════════════════════════════════════════════
class SearchEngine:
    """
    Ürün adından platform bazlı arama URL'si üretir ve
    scraper'ları koordine ederek eş zamanlı arama yapar.
    """

    def build_search_url(self, platform: str, query: str) -> str:
        """Platform için arama URL'si üretir (modül düzeyindeki fonksiyona delege eder)."""
        return build_search_url(platform, query)

    async def search_platform(self, platform: str, query: str) -> list[dict]:
        """
        Tek bir platformda arama yapar ve top 3 sonucu döndürür.

        Her sonuca sha256(url)[:12] formatında benzersiz bir "id" alanı eklenir.

        Args:
            platform: "trendyol", "amazon" veya "hepsiburada"
            query: Arama metni

        Returns:
            SearchResult dict listesi (en fazla 3 öğe)
        """
        from app.scraper import TrendyolScraper, AmazonScraper, HepsiburadaScraper

        scraper_map = {
            "trendyol": TrendyolScraper,
            "amazon": AmazonScraper,
            "hepsiburada": HepsiburadaScraper,
        }

        platform = platform.lower()
        if platform not in scraper_map:
            raise ValueError(f"Desteklenmeyen platform: '{platform}'")

        scraper_cls = scraper_map[platform]
        # headless=False: Trendyol (Cloudflare) ve Hepsiburada bot korumasını geçmek için
        scraper = scraper_cls(headless=False)

        try:
            await scraper.launch()
            page = await scraper._create_stealth_page()
            try:
                results = await scraper.search_products(page, query)
            finally:
                await page.close()
        finally:
            await scraper.close()

        # Her sonuca ID ekle
        for item in results:
            url = item.get("url", "")
            item["id"] = generate_product_id(url)

        # Fiyata göre sırala
        return _sort_by_price(results)

    async def search_all(self, query: str) -> dict[str, list[dict]]:
        """
        3 platformda eş zamanlı arama yapar.

        Bir platformun başarısız olması diğerlerini etkilemez.

        Args:
            query: Arama metni

        Returns:
            {
                "trendyol": list[SearchResult] | {"error": str, "results": []},
                "amazon":   list[SearchResult] | {"error": str, "results": []},
                "hepsiburada": list[SearchResult] | {"error": str, "results": []},
            }
        """
        platforms = ["trendyol", "amazon", "hepsiburada"]

        async def safe_search(platform: str) -> tuple[str, list[dict] | dict]:
            try:
                results = await self.search_platform(platform, query)
                return platform, results
            except Exception as e:
                logger.error(f"[search_engine] {platform} arama hatası: {e}")
                return platform, {"error": str(e), "results": []}

        tasks = [safe_search(p) for p in platforms]
        gathered = await asyncio.gather(*tasks)

        return {platform: result for platform, result in gathered}
