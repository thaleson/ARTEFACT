import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

from app.domain.models import Product, Promotion


CENT = Decimal("0.01")


def is_available(product: Product) -> bool:
    return product.status == "active" and product.stock_quantity > 0


def promotional_price(product: Product, promotion: Promotion) -> Decimal:
    if not promotion.is_active:
        raise ValueError("Cannot calculate an inactive promotion")
    price = product.price_brl * (
        Decimal("100") - promotion.discount_percent
    ) / Decimal("100")
    return price.quantize(CENT, rounding=ROUND_HALF_UP)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()


def normalize_phone(value: str) -> str:
    return "".join(character for character in value if character.isdigit())
