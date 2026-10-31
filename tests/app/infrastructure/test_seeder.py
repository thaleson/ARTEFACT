from pathlib import Path

from app.domain.models import PolicyChunk
from app.infrastructure.database import SqliteDatabase
from app.infrastructure.seeder import CsvDataSeeder, parse_specs


class OneChunkExtractor:
    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
        return [PolicyChunk(1, 1, "Policy")]


def test_seeder_loads_all_source_tables_and_is_idempotent() -> None:
    database = SqliteDatabase(Path(":memory:"))
    try:
        seeder = CsvDataSeeder(database, Path("data/raw"), OneChunkExtractor())

        seeder.seed()
        seeder.seed()

        counts = {
            table: database.connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in (
                "categories",
                "customers",
                "products",
                "orders",
                "order_items",
                "promotions",
                "policy_chunks",
            )
        }
    finally:
        database.close()

    assert counts == {
        "categories": 9,
        "customers": 50,
        "products": 65,
        "orders": 20,
        "order_items": 22,
        "promotions": 25,
        "policy_chunks": 1,
    }


def test_parse_specs_returns_json_mapping() -> None:
    assert parse_specs('{"top":"Spruce","strings":"steel"}') == {
        "top": "Spruce",
        "strings": "steel",
    }
