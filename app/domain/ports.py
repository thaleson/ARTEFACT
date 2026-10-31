from decimal import Decimal
from typing import Protocol

from app.domain.models import Order, PolicyChunk, Product, Promotion


class CatalogRepository(Protocol):
    def search_products(
        self,
        query: str | None = None,
        category_id: int | None = None,
        max_price: Decimal | None = None,
        available_only: bool = True,
    ) -> list[Product]:
        ...

    def get_product(self, product_id: int) -> Product | None:
        ...


class PromotionRepository(Protocol):
    def get_active_for_product(self, product_id: int) -> Promotion | None:
        ...


class OrderRepository(Protocol):
    def get_verified_order(
        self,
        order_id: int,
        customer_email: str | None,
        customer_phone: str | None,
    ) -> Order | None:
        ...


class PolicyRepository(Protocol):
    def search(self, query: str, limit: int = 3) -> list[PolicyChunk]:
        ...
