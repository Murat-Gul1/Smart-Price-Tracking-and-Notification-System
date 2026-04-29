"""
Alert cooldown should begin only after delivery succeeds.
"""

import app.logic as logic


def make_tracker(tmp_path, monkeypatch):
    monkeypatch.setattr(logic, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logic, "PRODUCTS_FILE", tmp_path / "products.json")
    monkeypatch.setattr(logic, "PRICE_HISTORY_FILE", tmp_path / "price_history.json")
    return logic.PriceTracker()


def test_alert_cooldown_starts_after_acknowledgement(tmp_path, monkeypatch):
    tracker = make_tracker(tmp_path, monkeypatch)
    product_id = "product-1"

    tracker.add_product(
        product_id=product_id,
        url="https://www.trendyol.com/x/x-p-1",
        title="Test Urun",
        platform="trendyol",
        target_price=100.0,
        current_price=120.0,
    )

    first_alert = tracker.update_price(product_id, 95.0)
    assert first_alert is not None
    assert first_alert["kind"] == "target"
    assert tracker.get_product(product_id).get("last_alert_at") is None

    second_alert = tracker.update_price(product_id, 90.0)
    assert second_alert is not None, "Cooldown should not start before delivery is acknowledged."

    assert tracker.mark_alert_sent(product_id, second_alert["kind"]) is True

    suppressed_alert = tracker.update_price(product_id, 85.0)
    assert suppressed_alert is None, "Cooldown should start after delivery is acknowledged."
