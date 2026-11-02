"""Pure business rules for inventory, pricing, and text normalization."""

import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

from app.domain.models import Product, Promotion


CENT = Decimal("0.01")
PIX_DISCOUNT = Decimal("0.05")


def is_available(product: Product) -> bool:
    """Determine whether a product can be presented as currently available.

    Args:
        product (Product): Product to evaluate.

    Returns:
        bool: Whether the product is active and has positive stock.
    """
    return product.status == "active" and product.stock_quantity > 0


def promotional_price(product: Product, promotion: Promotion) -> Decimal:
    """Calculate a promotion price rounded to Brazilian currency cents.

    Args:
        product (Product): Product catalog price.
        promotion (Promotion): Active promotion to apply.

    Returns:
        Decimal: Rounded promotional price.

    Raises:
        ValueError: If the promotion is inactive.
    """
    if not promotion.is_active:
        raise ValueError("Cannot calculate an inactive promotion")
    price = product.price_brl * (
        Decimal("100") - promotion.discount_percent
    ) / Decimal("100")
    return price.quantize(CENT, rounding=ROUND_HALF_UP)


def pix_price(product: Product) -> Decimal:
    """Calculate the cash price after the store's PIX discount.

    Args:
        product (Product): Catalog product price used as the discount base.

    Returns:
        Decimal: Price with the five-percent PIX discount, rounded to cents.
    """
    price = product.price_brl * (Decimal("1") - PIX_DISCOUNT)
    return price.quantize(CENT, rounding=ROUND_HALF_UP)


def normalize_text(value: str) -> str:
    """Normalize text to lowercase ASCII-like search terms.

    Args:
        value (str): Text to normalize.

    Returns:
        str: Lowercase text without accents or punctuation.
    """
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


def normalize_phone(value: str) -> str:
    """Keep only digits in a phone value for identity comparison.

    Args:
        value (str): Phone value with optional punctuation.

    Returns:
        str: Digits-only phone value.
    """
    return "".join(character for character in value if character.isdigit())
