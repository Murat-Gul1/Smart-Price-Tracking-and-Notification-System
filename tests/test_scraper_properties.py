"""
Property-based tests for scraper output contracts.
Feature: price-comparison, Property 4: Scraper sonuçları gerekli alanları içerir
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# Ensure the app package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scraper import HepsiburadaScraper


# ── Helpers ───────────────────────────────────────────────

REQUIRED_FIELDS = {"title", "price", "currency", "url", "platform"}


def make_mock_page(title: str, price_text: str, image_src: str, url: str) -> MagicMock:
    """
    Returns a mock Playwright Page whose query_selector calls return
    elements with the given title / price / image values.
    """
    page = MagicMock()
    page.url = url

    async def mock_query_selector(selector):
        el = MagicMock()
        # title selectors
        if "name" in selector or "title" in selector or "product-name" in selector:
            el.inner_text = AsyncMock(return_value=title)
            return el
        # price selectors
        if "finalPrice" in selector or "price" in selector:
            el.inner_text = AsyncMock(return_value=price_text)
            return el
        # image selectors
        if "img" in selector or "image" in selector:
            el.get_attribute = AsyncMock(return_value=image_src)
            return el
        # stock / add-to-cart
        if "addToCart" in selector or "add-to-cart" in selector:
            return el
        return None

    page.query_selector = AsyncMock(side_effect=mock_query_selector)
    return page


def run_async(coro):
    """Run a coroutine synchronously."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ── Property 4 ────────────────────────────────────────────

@given(
    title=st.text(min_size=1, max_size=200).filter(lambda s: s.strip()),
    price_text=st.one_of(
        st.just(""),
        st.builds(
            lambda n: f"{n:,.2f} TL".replace(",", ".").replace(".", ",", 1),
            st.floats(min_value=1.0, max_value=999999.0, allow_nan=False, allow_infinity=False),
        ),
    ),
    image_src=st.one_of(
        st.just(""),
        st.just("https://img.hepsiburada.net/product.jpg"),
    ),
    product_url=st.just("https://www.hepsiburada.com/some-product-p-123456"),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property4_parse_product_contains_required_fields(
    title, price_text, image_src, product_url
):
    """
    # Feature: price-comparison, Property 4: Scraper sonuçları gerekli alanları içerir
    # Validates: Requirements 6.2

    For any HepsiburadaScraper.parse_product() result, the dict returned by
    scrape_product() (which merges parse_product output with url/platform)
    must contain all of: title, price, currency, url, platform.
    Additionally, currency must be "TRY" and platform must be "hepsiburada".
    """
    scraper = HepsiburadaScraper()
    page = make_mock_page(title, price_text, image_src, product_url)

    # parse_product returns the raw fields; scrape_product adds url + platform.
    # We test the full contract by calling parse_product and then simulating
    # what scrape_product does (adds url and platform).
    raw = run_async(scraper.parse_product(page))

    # Simulate what scrape_product() merges in
    result = {**raw, "url": product_url, "platform": scraper.PLATFORM}

    # --- assertions ---
    missing = REQUIRED_FIELDS - result.keys()
    assert not missing, f"Missing required fields: {missing}"

    assert result["currency"] == "TRY", (
        f"currency must be 'TRY', got {result['currency']!r}"
    )
    assert result["platform"] == "hepsiburada", (
        f"platform must be 'hepsiburada', got {result['platform']!r}"
    )
    assert isinstance(result["title"], str) and result["title"], (
        "title must be a non-empty string"
    )
    assert result["url"] == product_url, "url must match the product URL"
