import csv
import json
from pathlib import Path
from typing import Iterable, Mapping

from app.domain.models import PolicyChunk
from app.infrastructure.database import SqliteDatabase
from app.infrastructure.policy_extractor import PolicyExtractor


class CsvDataSeeder:
    def __init__(
        self,
        database: SqliteDatabase,
        raw_data_dir: Path,
        policy_extractor: PolicyExtractor,
    ) -> None:
        self.database = database
        self.raw_data_dir = raw_data_dir
        self.policy_extractor = policy_extractor

    def seed(self) -> None:
        self.database.initialize_schema()
        self.database.clear_seeded_data()
        connection = self.database.connection
        connection.executemany(
            "INSERT INTO categories VALUES (?, ?, ?)",
            [
                (
                    int(row["category_id"]),
                    row["name"],
                    row["description"],
                )
                for row in _read_rows(self.raw_data_dir / "categories.csv")
            ],
        )
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            [
                (
                    int(row["customer_id"]),
                    row["name"],
                    row["phone"],
                    row["email"],
                    row["city"],
                )
                for row in _read_rows(self.raw_data_dir / "customers.csv")
            ],
        )
        connection.executemany(
            "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    int(row["product_id"]),
                    row["price_brl"],
                    row["name"],
                    int(row["category_id"]),
                    row["description"],
                    int(row["stock_quantity"]),
                    row["status"],
                    row["specs"],
                    row["created_at"],
                )
                for row in _read_rows(self.raw_data_dir / "products.csv")
            ],
        )
        connection.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    int(row["order_id"]),
                    int(row["customer_id"]),
                    row["order_date"],
                    row["status"],
                    row["total_brl"],
                    row["payment_method"],
                    row["tracking_code"] or None,
                    row["estimated_delivery"] or None,
                    row["notes"] or None,
                )
                for row in _read_rows(self.raw_data_dir / "orders.csv")
            ],
        )
        connection.executemany(
            "INSERT INTO order_items VALUES (?, ?, ?)",
            [
                (
                    int(row["order_id"]),
                    int(row["quantity"]),
                    int(row["product_id"]),
                )
                for row in _read_rows(self.raw_data_dir / "order_items.csv")
            ],
        )
        connection.executemany(
            "INSERT INTO promotions VALUES (?, ?, ?, ?, ?)",
            [
                (
                    int(row["promotion_id"]),
                    int(row["product_id"]),
                    row["discount_percent"],
                    row["description"],
                    int(row["is_active"]),
                )
                for row in _read_rows(self.raw_data_dir / "promotions.csv")
            ],
        )
        policy_chunks = self.policy_extractor.extract(
            self.raw_data_dir / "store_policies.pdf"
        )
        connection.executemany(
            "INSERT INTO policy_chunks VALUES (?, ?, ?)",
            _policy_values(policy_chunks),
        )
        connection.commit()


def _read_rows(path: Path) -> list[Mapping[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _policy_values(chunks: Iterable[PolicyChunk]) -> list[tuple[int, int, str]]:
    return [
        (chunk.chunk_id, chunk.page_number, chunk.content) for chunk in chunks
    ]


def parse_specs(raw_specs: str) -> dict[str, str]:
    return json.loads(raw_specs)
