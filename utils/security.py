"""
Güvenlik yardımcı fonksiyonları.
URL doğrulama, sanitizasyon ve rate limiting.
"""

import re
import time
import hashlib
import secrets
from urllib.parse import urlparse
from typing import Optional
from functools import wraps


# ── Desteklenen Platformlar ───────────────────────────────
SUPPORTED_DOMAINS = {
    "trendyol.com": "trendyol",
    "www.trendyol.com": "trendyol",
    "amazon.com.tr": "amazon",
    "www.amazon.com.tr": "amazon",
    "hepsiburada.com": "hepsiburada",
    "www.hepsiburada.com": "hepsiburada",
}


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    URL'nin geçerli ve desteklenen bir e-ticaret sitesine ait olduğunu kontrol eder.

    Returns:
        (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL boş olamaz."

    url = url.strip()

    # Temel URL formatı kontrolü
    if not re.match(r"^https?://", url):
        return False, "URL 'http://' veya 'https://' ile başlamalıdır."

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Geçersiz URL formatı."

    if not parsed.netloc:
        return False, "URL'de geçerli bir domain bulunamadı."

    # Desteklenen domain kontrolü
    domain = parsed.netloc.lower()
    if domain not in SUPPORTED_DOMAINS:
        supported = ", ".join(sorted(set(SUPPORTED_DOMAINS.values())))
        return False, f"Desteklenmeyen platform. Desteklenen: {supported}"

    return True, None


def detect_platform(url: str) -> Optional[str]:
    """URL'den platformu tespit eder (trendyol, amazon)."""
    try:
        parsed = urlparse(url.strip())
        domain = parsed.netloc.lower()
        return SUPPORTED_DOMAINS.get(domain)
    except Exception:
        return None


def sanitize_url(url: str) -> str:
    """URL'yi temizler ve normalize eder."""
    url = url.strip()

    # Tracking parametrelerini temizle
    tracking_params = [
        "utm_source", "utm_medium", "utm_campaign", "utm_term",
        "utm_content", "ref", "tag", "linkCode", "gclid", "fbclid",
    ]

    parsed = urlparse(url)
    if parsed.query:
        from urllib.parse import parse_qs, urlencode

        params = parse_qs(parsed.query, keep_blank_values=True)
        clean_params = {
            k: v for k, v in params.items()
            if k.lower() not in tracking_params
        }
        clean_query = urlencode(clean_params, doseq=True)
        url = parsed._replace(query=clean_query).geturl()

    return url


def generate_product_id(url: str) -> str:
    """URL'den benzersiz bir ürün ID'si üretir."""
    normalized = sanitize_url(url).lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def generate_secret_key() -> str:
    """Flask için güvenli bir secret key üretir."""
    return secrets.token_hex(32)


# ── Rate Limiter ──────────────────────────────────────────
class RateLimiter:
    """Basit in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def is_allowed(self, key: str = "global") -> bool:
        """İstek yapılıp yapılamayacağını kontrol eder."""
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []

        # Pencere dışındaki istekleri temizle
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self.window_seconds
        ]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def wait_time(self, key: str = "global") -> float:
        """Bir sonraki istek için beklenecek süreyi döndürür (saniye)."""
        if key not in self._requests or not self._requests[key]:
            return 0.0

        now = time.time()
        oldest = min(self._requests[key])
        remaining = self.window_seconds - (now - oldest)
        return max(0.0, remaining)


# Global rate limiter (scraping istekleri için)
scraper_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
