import sqlite3
from pathlib import Path


class SqliteDatabase:
    def __init__(self, database_path: Path) -> None:
        if str(database_path) != ":memory:":
            database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            str(database_path), check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def initialize_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                price_brl TEXT NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(category_id),
                description TEXT NOT NULL,
                stock_quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                specs TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                total_brl TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                tracking_code TEXT,
                estimated_delivery TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER NOT NULL REFERENCES orders(order_id),
                quantity INTEGER NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                PRIMARY KEY (order_id, product_id)
            );

            CREATE TABLE IF NOT EXISTS promotions (
                promotion_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                discount_percent TEXT NOT NULL,
                description TEXT NOT NULL,
                is_active INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS policy_chunks (
                chunk_id INTEGER PRIMARY KEY,
                page_number INTEGER NOT NULL,
                content TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def clear_seeded_data(self) -> None:
        self.connection.executescript(
            """
            DELETE FROM policy_chunks;
            DELETE FROM promotions;
            DELETE FROM order_items;
            DELETE FROM orders;
            DELETE FROM products;
            DELETE FROM customers;
            DELETE FROM categories;
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
