"""Repository protocols that invert infrastructure dependencies."""

from decimal import Decimal
from typing import Protocol

from app.domain.models import Order, PolicyChunk, Product, Promotion


class CatalogRepository(Protocol):
    """Define catalog queries required by the application layer."""

    def search_products(
        self,
        query: str | None = None,
        category_id: int | None = None,
        max_price: Decimal | None = None,
        available_only: bool = True,
    ) -> list[Product]:
        """Search products using optional catalog filters.

        Args:
            query (str | None): Product-name or description terms.
            category_id (int | None): Optional catalog category filter.
            max_price (Decimal | None): Optional maximum catalog price.
            available_only (bool): Whether to exclude unavailable products.

        Returns:
            list[Product]: Matching catalog products.
        """
        ...

    def get_product(self, product_id: int) -> Product | None:
        """Get one product by its catalog identifier.

        Args:
            product_id (int): Product identifier.

        Returns:
            Product | None: Matching product when it exists.
        """
        ...


class PromotionRepository(Protocol):
    """Define access to active product promotions."""

    def get_active_for_product(self, product_id: int) -> Promotion | None:
        """Get the active promotion for a product.

        Args:
            product_id (int): Product identifier.

        Returns:
            Promotion | None: Active promotion when one exists.
        """
        ...


class OrderRepository(Protocol):
    """Define privacy-aware order lookup behavior."""

    def get_verified_order(
        self,
        order_id: int,
        customer_email: str | None,
        customer_phone: str | None,
    ) -> Order | None:
        """Get an order only when customer identity matches.

        Args:
            order_id (int): Order identifier.
            customer_email (str | None): Optional verified customer email.
            customer_phone (str | None): Optional verified customer phone.

        Returns:
            Order | None: Authorized order or no result.
        """
        ...


class PolicyRepository(Protocol):
    """Define retrieval of relevant policy-manual excerpts."""

    def search(self, query: str, limit: int = 3) -> list[PolicyChunk]:
        """Search policy chunks using a customer query.

        Args:
            query (str): Policy topic or customer question.
            limit (int): Maximum number of chunks to return.

        Returns:
            list[PolicyChunk]: Ranked policy excerpts.
        """
        ...
