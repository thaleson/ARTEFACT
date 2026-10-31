"""SQLite repository implementations for operational and policy data."""

import json
import sqlite3
from decimal import Decimal

from app.domain.models import Order, PolicyChunk, Product, Promotion
from app.domain.rules import normalize_phone, normalize_text


class SqliteCatalogRepository:
    """Query catalog products using parameterized SQLite statements.

    Attributes:
        connection (sqlite3.Connection): SQLite connection used for catalog queries.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def search_products(
        self,
        query: str | None = None,
        category_id: int | None = None,
        max_price: Decimal | None = None,
        available_only: bool = True,
    ) -> list[Product]:
        """Search products with optional terms, category, price, and availability.

        Args:
            query (str | None): Product-name or description terms.
            category_id (int | None): Optional category filter.
            max_price (Decimal | None): Optional maximum price.
            available_only (bool): Exclude inactive or zero-stock products when true.

        Returns:
            list[Product]: Products ordered by price and name.
        """
        conditions = ["1 = 1"]
        parameters: list[object] = []
        if query:
            for term in query.split():
                conditions.append(
                    "(LOWER(p.name) LIKE LOWER(?) OR LOWER(p.description) LIKE LOWER(?))"
                )
                wildcard = f"%{term}%"
                parameters.extend([wildcard, wildcard])
        if category_id is not None:
            conditions.append("p.category_id = ?")
            parameters.append(category_id)
        if max_price is not None:
            conditions.append("CAST(p.price_brl AS REAL) <= CAST(? AS REAL)")
            parameters.append(str(max_price))
        if available_only:
            conditions.extend(["p.status = 'active'", "p.stock_quantity > 0"])
        query_sql = f"""
            SELECT p.*
            FROM products p
            WHERE {' AND '.join(conditions)}
            ORDER BY CAST(p.price_brl AS REAL), p.name
        """
        rows = self.connection.execute(query_sql, parameters).fetchall()
        return [_product_from_row(row) for row in rows]

    def get_product(self, product_id: int) -> Product | None:
        """Fetch one product by primary key.

        Args:
            product_id (int): Catalog product identifier.

        Returns:
            Product | None: Product record when found.
        """
        row = self.connection.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
        return _product_from_row(row) if row is not None else None


class SqlitePromotionRepository:
    """Retrieve active promotions from SQLite.

    Attributes:
        connection (sqlite3.Connection): SQLite connection used for promotion queries.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_active_for_product(self, product_id: int) -> Promotion | None:
        """Fetch the highest active discount for a product.

        Args:
            product_id (int): Product identifier.

        Returns:
            Promotion | None: Active promotion when found.
        """
        row = self.connection.execute(
            """
            SELECT * FROM promotions
            WHERE product_id = ? AND is_active = 1
            ORDER BY discount_percent DESC, promotion_id
            LIMIT 1
            """,
            (product_id,),
        ).fetchone()
        return _promotion_from_row(row) if row is not None else None


class SqliteOrderRepository:
    """Retrieve order records only after customer identity verification.

    Attributes:
        connection (sqlite3.Connection): SQLite connection used for order queries.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_verified_order(
        self,
        order_id: int,
        customer_email: str | None,
        customer_phone: str | None,
    ) -> Order | None:
        """Fetch an order only when email or phone matches its customer.

        Args:
            order_id (int): Order identifier.
            customer_email (str | None): Optional customer email.
            customer_phone (str | None): Optional customer phone.

        Returns:
            Order | None: Authorized order record or no result.
        """
        row = self.connection.execute(
            """
            SELECT o.*, c.email AS customer_email, c.phone AS customer_phone
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            WHERE o.order_id = ?
            """,
            (order_id,),
        ).fetchone()
        if row is None or not _matches_customer(row, customer_email, customer_phone):
            return None
        return _order_from_row(row)


class SqlitePolicyRepository:
    """Rank policy chunks using transparent lexical term scoring.

    Attributes:
        connection (sqlite3.Connection): SQLite connection used for policy queries.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def search(self, query: str, limit: int = 3) -> list[PolicyChunk]:
        """Return policy chunks ranked by normalized term frequency.

        Args:
            query (str): Customer policy question or canonical topic terms.
            limit (int): Maximum number of chunks to return.

        Returns:
            list[PolicyChunk]: Ranked policy excerpts with page metadata.
        """
        stop_words = {
            "a", "as", "ao", "aos", "com", "como", "da", "das", "de", "do",
            "dos", "e", "em", "este", "esta", "meu", "minha", "o", "os", "para",
            "qual", "quais", "que", "se", "sobre", "um", "uma", "voce",
        }
        terms = [
            term
            for term in normalize_text(query).split()
            if len(term) > 2 and term not in stop_words
        ]
        if not terms:
            return []
        rows = self.connection.execute(
            "SELECT chunk_id, page_number, content FROM policy_chunks"
        ).fetchall()
        scored: list[tuple[int, sqlite3.Row]] = []
        for row in rows:
            content = normalize_text(row["content"])
            score = sum(content.count(term) for term in terms)
            if score:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], item[1]["page_number"], item[1]["chunk_id"]))
        return [_policy_from_row(row) for _, row in scored[:limit]]


def _product_from_row(row: sqlite3.Row) -> Product:
    """Convert a SQLite product row to a domain product.

    Args:
        row (sqlite3.Row): Raw product row.

    Returns:
        Product: Domain product value.
    """
    return Product(
        product_id=int(row["product_id"]),
        price_brl=Decimal(str(row["price_brl"])),
        name=str(row["name"]),
        category_id=int(row["category_id"]),
        description=str(row["description"]),
        stock_quantity=int(row["stock_quantity"]),
        status=str(row["status"]),
        specs=json.loads(str(row["specs"])),
        created_at=str(row["created_at"]),
    )


def _promotion_from_row(row: sqlite3.Row) -> Promotion:
    """Convert a SQLite promotion row to a domain promotion.

    Args:
        row (sqlite3.Row): Raw promotion row.

    Returns:
        Promotion: Domain promotion value.
    """
    return Promotion(
        promotion_id=int(row["promotion_id"]),
        product_id=int(row["product_id"]),
        discount_percent=Decimal(str(row["discount_percent"])),
        description=str(row["description"]),
        is_active=bool(row["is_active"]),
    )


def _order_from_row(row: sqlite3.Row) -> Order:
    """Convert a SQLite order row to a domain order.

    Args:
        row (sqlite3.Row): Raw order row joined with customer identity columns.

    Returns:
        Order: Domain order value without customer personal data.
    """
    return Order(
        order_id=int(row["order_id"]),
        customer_id=int(row["customer_id"]),
        order_date=str(row["order_date"]),
        status=str(row["status"]),
        total_brl=Decimal(str(row["total_brl"])),
        payment_method=str(row["payment_method"]),
        tracking_code=row["tracking_code"],
        estimated_delivery=row["estimated_delivery"],
        notes=row["notes"],
    )


def _policy_from_row(row: sqlite3.Row) -> PolicyChunk:
    """Convert a SQLite policy row to a domain policy chunk.

    Args:
        row (sqlite3.Row): Raw policy row.

    Returns:
        PolicyChunk: Domain policy chunk value.
    """
    return PolicyChunk(
        chunk_id=int(row["chunk_id"]),
        page_number=int(row["page_number"]),
        content=str(row["content"]),
    )


def _matches_customer(
    row: sqlite3.Row,
    customer_email: str | None,
    customer_phone: str | None,
) -> bool:
    """Compare supplied identity values with a customer row.

    Args:
        row (sqlite3.Row): Order row containing customer email and phone.
        customer_email (str | None): Supplied customer email.
        customer_phone (str | None): Supplied customer phone.

    Returns:
        bool: Whether either supplied identity value matches.
    """
    email_matches = bool(
        customer_email
        and customer_email.strip().casefold()
        == str(row["customer_email"]).strip().casefold()
    )
    phone_matches = bool(
        customer_phone
        and normalize_phone(customer_phone)
        == normalize_phone(str(row["customer_phone"]))
    )
    return email_matches or phone_matches
