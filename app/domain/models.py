"""Immutable domain records used across application boundaries."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class Product:
    """Represent one catalog product and its current inventory state."""

    product_id: int
    price_brl: Decimal
    name: str
    category_id: int
    description: str
    stock_quantity: int
    status: str
    specs: Mapping[str, str]
    created_at: str


@dataclass(frozen=True)
class Promotion:
    """Represent a product promotion and its activation state."""

    promotion_id: int
    product_id: int
    discount_percent: Decimal
    description: str
    is_active: bool


@dataclass(frozen=True)
class Order:
    """Represent historical order data safe for an authorized response."""

    order_id: int
    customer_id: int
    order_date: str
    status: str
    total_brl: Decimal
    payment_method: str
    tracking_code: str | None
    estimated_delivery: str | None
    notes: str | None


@dataclass(frozen=True)
class PolicyChunk:
    """Represent one page-aware excerpt extracted from the policy manual."""

    chunk_id: int
    page_number: int
    content: str
