import json
from decimal import Decimal
from typing import Mapping

from app.application.contracts import ChatInput, SourceReference
from app.application.formatting import format_brl
from app.domain.models import Product, Promotion
from app.domain.ports import (
    CatalogRepository,
    OrderRepository,
    PolicyRepository,
    PromotionRepository,
)
from app.domain.rules import is_available, promotional_price


class ToolExecutor:
    def __init__(
        self,
        catalog: CatalogRepository,
        promotions: PromotionRepository,
        orders: OrderRepository,
        policies: PolicyRepository,
    ) -> None:
        self.catalog = catalog
        self.promotions = promotions
        self.orders = orders
        self.policies = policies

    def execute(
        self,
        name: str,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        handlers = {
            "search_products": self._search_products,
            "get_product": self._get_product,
            "get_active_promotion": self._get_active_promotion,
            "get_verified_order": self._get_verified_order,
            "search_policies": self._search_policies,
        }
        handler = handlers.get(name)
        if handler is None:
            return json.dumps({"error": "Unknown tool"}), []
        return handler(arguments, chat_input)

    def _search_products(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        del chat_input
        query = _optional_string(arguments.get("query"))
        category_id = _optional_int(arguments.get("category_id"))
        max_price = _optional_decimal(arguments.get("max_price"))
        products = self.catalog.search_products(
            query=query,
            category_id=category_id,
            max_price=max_price,
            available_only=True,
        )
        result = [
            {
                "product_id": product.product_id,
                "name": product.name,
                "price": format_brl(product.price_brl),
                "stock_quantity": product.stock_quantity,
                "description": product.description,
                "promotion": _promotion_data(
                    product, self.promotions.get_active_for_product(product.product_id)
                ),
            }
            for product in products
        ]
        return json.dumps({"products": result}, ensure_ascii=False), [
            SourceReference("catalog", f"product:{product.product_id}")
            for product in products
        ]

    def _get_product(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        del chat_input
        product_id = _required_int(arguments.get("product_id"))
        product = self.catalog.get_product(product_id)
        if product is None:
            return json.dumps({"product": None}), []
        promotion = self.promotions.get_active_for_product(product.product_id)
        result = {
            "product_id": product.product_id,
            "name": product.name,
            "price": format_brl(product.price_brl),
            "stock_quantity": product.stock_quantity,
            "status": product.status,
            "available": is_available(product),
            "description": product.description,
            "promotion": _promotion_data(product, promotion),
        }
        return json.dumps({"product": result}, ensure_ascii=False), [
            SourceReference("catalog", f"product:{product.product_id}")
        ]

    def _get_active_promotion(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        del chat_input
        product_id = _required_int(arguments.get("product_id"))
        product = self.catalog.get_product(product_id)
        promotion = self.promotions.get_active_for_product(product_id)
        if product is None or promotion is None or not is_available(product):
            return json.dumps({"promotion": None}), []
        return json.dumps(
            {
                "promotion": _promotion_data(product, promotion),
                "original_price": format_brl(product.price_brl),
                "promotional_price": format_brl(promotional_price(product, promotion)),
            },
            ensure_ascii=False,
        ), [SourceReference("promotion", f"promotion:product:{product_id}")]

    def _get_verified_order(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        order_id = _required_int(arguments.get("order_id"))
        if not chat_input.customer_email and not chat_input.customer_phone:
            return json.dumps({"authorized": False, "verification_required": True}), []
        order = self.orders.get_verified_order(
            order_id,
            chat_input.customer_email,
            chat_input.customer_phone,
        )
        if order is None:
            return json.dumps({"authorized": False}), []
        return json.dumps(
            {
                "authorized": True,
                "order_id": order.order_id,
                "status": order.status,
                "total": format_brl(order.total_brl),
                "payment_method": order.payment_method,
                "tracking_code": order.tracking_code,
                "estimated_delivery": order.estimated_delivery,
                "notes": order.notes,
            },
            ensure_ascii=False,
        ), [SourceReference("order", f"order:{order.order_id}")]

    def _search_policies(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        del chat_input
        query = _required_string(arguments.get("query"))
        chunks = self.policies.search(query, limit=4)
        return json.dumps(
            {
                "chunks": [
                    {"page": chunk.page_number, "content": chunk.content}
                    for chunk in chunks
                ]
            },
            ensure_ascii=False,
        ), [
            SourceReference("policy", f"page:{chunk.page_number}")
            for chunk in chunks
        ]


def _promotion_data(
    product: Product,
    promotion: Promotion | None,
) -> dict[str, object] | None:
    if promotion is None or not is_available(product):
        return None
    return {
        "description": promotion.description,
        "discount_percent": str(promotion.discount_percent),
        "promotional_price": format_brl(promotional_price(product, promotion)),
    }


def _optional_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _required_string(value: object) -> str:
    result = _optional_string(value)
    if result is None:
        raise ValueError("A non-empty string argument is required")
    return result


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _required_int(value)


def _required_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("An integer argument is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("An integer argument is required") from exc


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise ValueError("A numeric argument is required") from exc
