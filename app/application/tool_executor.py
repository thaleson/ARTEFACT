"""Execute typed support tools against injected repositories."""

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
from app.domain.rules import is_available, normalize_text, pix_price, promotional_price


class ToolExecutor:
    """Dispatch model-selected tools while enforcing application boundaries.

    Attributes:
        catalog (CatalogRepository): Product catalog access boundary.
        promotions (PromotionRepository): Promotion access boundary.
        orders (OrderRepository): Verified order access boundary.
        policies (PolicyRepository): Policy retrieval boundary.
    """

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
        """Execute a named tool and return serialized data with sources.

        Args:
            name (str): Tool name selected by the model.
            arguments (Mapping[str, object]): Validated or model-provided arguments.
            chat_input (ChatInput): Original message and trusted identity context.

        Returns:
            tuple[str, list[SourceReference]]: JSON tool result and source references.
        """
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
        """Search available products and include active promotion data.

        Args:
            arguments (Mapping[str, object]): Optional catalog filters.
            chat_input (ChatInput): Original customer context.

        Returns:
            tuple[str, list[SourceReference]]: Serialized products and catalog sources.
        """
        query = _optional_string(arguments.get("query"))
        category_id = _optional_int(arguments.get("category_id"))
        max_price = _optional_decimal(arguments.get("max_price"))
        products = self.catalog.search_products(
            query=query,
            category_id=category_id,
            max_price=max_price,
            available_only=True,
        )
        result = []
        for product in products:
            promotion = self.promotions.get_active_for_product(product.product_id)
            product_result = {
                "product_id": product.product_id,
                "name": product.name,
                "price": format_brl(product.price_brl),
                "stock_quantity": product.stock_quantity,
                "description": product.description,
                "promotion": _promotion_data(product, promotion),
            }
            if _is_pix_request(chat_input.message):
                product_result.update(_pix_data(product, promotion))
            result.append(product_result)
        return json.dumps({"products": result}, ensure_ascii=False), [
            SourceReference("catalog", f"product:{product.product_id}")
            for product in products
        ]

    def _get_product(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        """Return one product with availability and promotion information.

        Args:
            arguments (Mapping[str, object]): Required product ID.
            chat_input (ChatInput): Original customer context.

        Returns:
            tuple[str, list[SourceReference]]: Serialized product and catalog source.
        """
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
        if _is_pix_request(chat_input.message):
            result.update(_pix_data(product, promotion))
        return json.dumps({"product": result}, ensure_ascii=False), [
            SourceReference("catalog", f"product:{product.product_id}")
        ]

    def _get_active_promotion(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        """Return a valid active promotion and calculated promotional price.

        Args:
            arguments (Mapping[str, object]): Required product ID.
            chat_input (ChatInput): Original customer context.

        Returns:
            tuple[str, list[SourceReference]]: Promotion payload and source reference.
        """
        product_id = _required_int(arguments.get("product_id"))
        product = self.catalog.get_product(product_id)
        promotion = self.promotions.get_active_for_product(product_id)
        if product is None or promotion is None or not is_available(product):
            return json.dumps({"promotion": None}), []
        result = {
            "promotion": _promotion_data(product, promotion),
            "original_price": format_brl(product.price_brl),
            "promotional_price": format_brl(promotional_price(product, promotion)),
        }
        if _is_pix_request(chat_input.message):
            result.update(_pix_data(product, promotion))
        return json.dumps(result, ensure_ascii=False), [
            SourceReference("promotion", f"promotion:product:{product_id}")
        ]

    def _get_verified_order(
        self,
        arguments: Mapping[str, object],
        chat_input: ChatInput,
    ) -> tuple[str, list[SourceReference]]:
        """Return order data only when trusted request identity matches the order.

        Args:
            arguments (Mapping[str, object]): Required order ID.
            chat_input (ChatInput): Customer identity supplied outside model arguments.

        Returns:
            tuple[str, list[SourceReference]]: Authorized order payload or safe refusal.
        """
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
        """Retrieve policy chunks relevant to a model-generated query.

        Args:
            arguments (Mapping[str, object]): Required policy query.
            chat_input (ChatInput): Original customer context.

        Returns:
            tuple[str, list[SourceReference]]: Serialized policy chunks and pages.
        """
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


def _is_pix_request(message: str) -> bool:
    """Return whether the customer explicitly asks for a PIX price."""
    return "pix" in normalize_text(message).split()


def _pix_data(
    product: Product,
    promotion: Promotion | None,
) -> dict[str, object]:
    """Serialize PIX pricing without stacking it on an active promotion."""
    if not is_available(product):
        return {"pix_price": None, "pix_discount_applied": False}
    if promotion is not None:
        return {
            "pix_price": None,
            "pix_discount_applied": False,
            "pix_note": "The PIX discount is not cumulative with the active promotion.",
        }
    return {
        "pix_price": format_brl(pix_price(product)),
        "pix_discount_applied": True,
    }


def _promotion_data(
    product: Product,
    promotion: Promotion | None,
) -> dict[str, object] | None:
    """Serialize an active promotion only for an available product.

    Args:
        product (Product): Product associated with the promotion.
        promotion (Promotion | None): Promotion candidate.

    Returns:
        dict[str, object] | None: Promotion data or no promotion.
    """
    if promotion is None or not is_available(product):
        return None
    return {
        "description": promotion.description,
        "discount_percent": str(promotion.discount_percent),
        "promotional_price": format_brl(promotional_price(product, promotion)),
    }


def _optional_string(value: object) -> str | None:
    """Normalize an optional non-empty string tool argument.

    Args:
        value (object): Raw tool argument.

    Returns:
        str | None: Stripped value or no value.
    """
    return value.strip() if isinstance(value, str) and value.strip() else None


def _required_string(value: object) -> str:
    """Validate a required non-empty string tool argument.

    Args:
        value (object): Raw tool argument.

    Returns:
        str: Stripped non-empty string.

    Raises:
        ValueError: If the value is missing or not a non-empty string.
    """
    result = _optional_string(value)
    if result is None:
        raise ValueError("A non-empty string argument is required")
    return result


def _optional_int(value: object) -> int | None:
    """Normalize an optional integer tool argument.

    Args:
        value (object): Raw tool argument.

    Returns:
        int | None: Parsed integer or no value.

    Raises:
        ValueError: If a supplied value is not an integer.
    """
    if value is None:
        return None
    return _required_int(value)


def _required_int(value: object) -> int:
    """Validate and parse a required integer tool argument.

    Args:
        value (object): Raw tool argument.

    Returns:
        int: Parsed integer.

    Raises:
        ValueError: If the value is boolean or cannot be parsed as an integer.
    """
    if isinstance(value, bool):
        raise ValueError("An integer argument is required")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("An integer argument is required") from exc


def _optional_decimal(value: object) -> Decimal | None:
    """Normalize an optional decimal tool argument.

    Args:
        value (object): Raw tool argument.

    Returns:
        Decimal | None: Parsed decimal or no value.

    Raises:
        ValueError: If a supplied value cannot be parsed as a number.
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise ValueError("A numeric argument is required") from exc
