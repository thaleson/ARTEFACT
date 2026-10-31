from pathlib import Path

from app.infrastructure.database import SqliteDatabase


def test_database_initializes_schema_and_closes(tmp_path: Path) -> None:
    database = SqliteDatabase(tmp_path / "agent.db")

    database.initialize_schema()
    tables = database.connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()

    assert {row[0] for row in tables} == {
        "categories",
        "customers",
        "products",
        "orders",
        "order_items",
        "promotions",
        "policy_chunks",
    }
    database.close()


def test_database_clear_seeded_data_removes_rows(database: SqliteDatabase) -> None:
    database.clear_seeded_data()

    count = database.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    assert count == 0
