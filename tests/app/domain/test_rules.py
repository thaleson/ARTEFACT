from decimal import Decimal

import pytest

from app.domain.models import Product, Promotion
from app.domain.rules import (
    is_available,
    normalize_phone,
    normalize_text,
    promotional_price,
)


def make_product(status: str = "active", stock_quantity: int = 3) -> Product:
    return Product(
        product_id=1,
        price_brl=Decimal("100.00"),
        name="Instrument",
        category_id=1,
        description="Description",
        stock_quantity=stock_quantity,
        status=status,
        specs={},
        created_at="2025-01-01",
    )


def make_promotion(active: bool = True) -> Promotion:
    return Promotion(
        promotion_id=1,
        product_id=1,
        discount_percent=Decimal("15"),
        description="Offer",
        is_active=active,
    )


def test_is_available_requires_active_status_and_positive_stock() -> None:
    assert is_available(make_product()) is True
    assert is_available(make_product(stock_quantity=0)) is False
    assert is_available(make_product(status="discontinued")) is False


def test_promotional_price_rounds_to_brl_cents() -> None:
    result = promotional_price(make_product(), make_promotion())

    assert result == Decimal("85.00")


def test_promotional_price_rejects_inactive_promotion() -> None:
    with pytest.raises(ValueError, match="inactive"):
        promotional_price(make_product(), make_promotion(active=False))


def test_normalizers_remove_accents_and_phone_punctuation() -> None:
    assert normalize_text("Violões disponíveis") == "violoes disponiveis"
    assert normalize_phone("(67) 99812-3456") == "67998123456"
