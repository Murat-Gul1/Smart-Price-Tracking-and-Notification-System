"""
Smart Price Tracker - Smoke Test

Run quick local checks for imports, deterministic utilities, and optionally a
network-backed add/list/remove flow.

Usage:
    python scripts/smoke.py
    python scripts/smoke.py --with-network --url "https://www.trendyol.com/..."
"""

import argparse
import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        print(f"{GREEN}[OK]{RESET} {name}")
        passed += 1
    else:
        suffix = f" - {detail}" if detail else ""
        print(f"{RED}[FAIL]{RESET} {name}{suffix}")
        failed += 1


def t1_imports() -> None:
    try:
        from app.services import (  # noqa: F401
            add_tracked_product,
            check_all_tracked_products,
            list_tracked_products,
            normalize_scrape_result,
            remove_tracked_product,
        )
        from app.logic import get_tracker  # noqa: F401
        from utils.security import generate_product_id, validate_url  # noqa: F401

        report("T1 service and util imports", True)
    except Exception as e:
        report("T1 service and util imports", False, str(e))


def t2_validate_url() -> None:
    try:
        from utils.security import validate_url

        ok, _ = validate_url("https://www.trendyol.com/x/x-p-1")
        bad, _ = validate_url("not-a-url")
        if ok and not bad:
            report("T2 validate_url behavior", True)
        else:
            report("T2 validate_url behavior", False, f"ok={ok}, bad={bad}")
    except Exception as e:
        report("T2 validate_url behavior", False, str(e))


def t3_product_id_deterministic() -> None:
    try:
        from utils.security import generate_product_id

        a = generate_product_id("https://www.trendyol.com/x")
        b = generate_product_id("https://www.trendyol.com/x")
        if a == b and len(a) >= 8:
            report("T3 product_id deterministic", True)
        else:
            report("T3 product_id deterministic", False, f"a={a}, b={b}")
    except Exception as e:
        report("T3 product_id deterministic", False, str(e))


def t4_tracker_singleton() -> None:
    try:
        from app.logic import get_tracker

        t1 = get_tracker()
        t2 = get_tracker()
        if t1 is t2:
            report("T4 PriceTracker singleton", True)
        else:
            report("T4 PriceTracker singleton", False, "two different instances")
    except Exception as e:
        report("T4 PriceTracker singleton", False, str(e))


def t5_normalize_scrape_result() -> None:
    try:
        from app.services import normalize_scrape_result

        result = normalize_scrape_result({"title": "X", "price": 100}, "https://example.com")
        keys = {
            "title",
            "price",
            "currency",
            "url",
            "platform",
            "image_url",
            "in_stock",
            "rating",
            "error",
        }
        missing = keys - set(result.keys())
        if not missing:
            report("T5 normalize_scrape_result fields", True)
        else:
            report("T5 normalize_scrape_result fields", False, f"missing: {sorted(missing)}")
    except Exception as e:
        report("T5 normalize_scrape_result fields", False, str(e))


async def t6_add_remove_with_network(test_url: str) -> None:
    try:
        from app.services import add_tracked_product, list_tracked_products, remove_tracked_product

        info = await add_tracked_product(test_url)
        pid = info["product_id"]
        if pid not in list_tracked_products():
            report("T6 add_tracked_product -> list", False, "product not listed")
            return
        if not remove_tracked_product(pid):
            report("T6 remove_tracked_product", False, "remove returned False")
            return
        if pid in list_tracked_products():
            report("T6 remove then absent from list", False, "product still listed")
            return
        report("T6 end-to-end add/list/remove (network)", True)
    except Exception as e:
        report("T6 end-to-end add/list/remove (network)", False, str(e))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-network", action="store_true", help="Run network-backed tests too")
    parser.add_argument(
        "--url",
        default="{{TEST_PRODUCT_URL}}",
        help="Product URL used by the network test",
    )
    args = parser.parse_args()

    print("\n=== Smart Price Tracker - Smoke Test ===\n")
    t1_imports()
    t2_validate_url()
    t3_product_id_deterministic()
    t4_tracker_singleton()
    t5_normalize_scrape_result()

    if args.with_network:
        if args.url and not args.url.startswith("{{"):
            print("\n--- Network test ---")
            asyncio.run(t6_add_remove_with_network(args.url))
        else:
            print("\n[SKIP] Network test: pass --url with a real product URL.")

    print(f"\n=== {passed} OK, {failed} FAIL ===")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
