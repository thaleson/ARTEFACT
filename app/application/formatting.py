"""Format domain values for Brazilian Portuguese customer responses."""

from decimal import Decimal, ROUND_HALF_UP

from app.domain.models import Order, Product, Promotion
from app.domain.rules import is_available, promotional_price


def format_brl(value: Decimal) -> str:
    """Format a decimal amount using Brazilian currency separators.

    Args:
        value (Decimal): Monetary value to round and format.

    Returns:
        str: Value formatted as Brazilian reais.
    """
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    formatted = f"{rounded:,.2f}"
    return f"R$ {formatted.replace(',', '_').replace('.', ',').replace('_', '.')}"


def format_product_line(
    product: Product,
    promotion: Promotion | None = None,
) -> str:
    """Format a product with price, promotion, and availability information.

    Args:
        product (Product): Product to present.
        promotion (Promotion | None): Optional active promotion for the product.

    Returns:
        str: Customer-facing product summary.
    """
    availability = (
        f"{product.stock_quantity} unidade(s) em estoque"
        if is_available(product)
        else _status_label(product)
    )
    price = format_brl(product.price_brl)
    if promotion is not None and is_available(product):
        price = (
            f"{price} por {format_brl(promotional_price(product, promotion))} "
            f"({promotion.discount_percent}% off)"
        )
    return f"- {product.name}: {price} — {availability}."


def format_order(order: Order) -> str:
    """Format an authorized order summary without customer personal data.

    Args:
        order (Order): Order record already authorized for the requester.

    Returns:
        str: Customer-facing order status and delivery summary.
    """
    status = {
        "delivered": "entregue",
        "shipped": "enviado",
        "confirmed": "confirmado",
        "pending": "pendente",
        "cancelled": "cancelado",
    }.get(order.status, order.status)
    parts = [
        f"O pedido #{order.order_id} está {status}.",
        f"Total registrado: {format_brl(order.total_brl)}.",
    ]
    if order.tracking_code:
        parts.append(f"Código de rastreamento: {order.tracking_code}.")
    if order.estimated_delivery:
        parts.append(f"Previsão registrada: {order.estimated_delivery}.")
    if order.notes:
        parts.append(f"Observação: {order.notes}.")
    return " ".join(parts)


def _status_label(product: Product) -> str:
    """Return a customer-facing label for a non-available product status.

    Args:
        product (Product): Product whose status should be translated.

    Returns:
        str: Availability label in Portuguese.
    """
    return {
        "discontinued": "produto descontinuado",
        "coming_soon": "em breve",
        "active": "temporariamente indisponível",
    }.get(product.status, "indisponibilidade não confirmada")
