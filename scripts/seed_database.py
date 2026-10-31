"""Seed the derived SQLite database from challenge source files."""

from app.config import Settings
from app.infrastructure.database import SqliteDatabase
from app.infrastructure.policy_extractor import PdfPolicyExtractor
from app.infrastructure.seeder import CsvDataSeeder


def main() -> None:
    """Load CSV records and policy chunks into the configured database."""
    settings = Settings.from_environment()
    database = SqliteDatabase(settings.database_path)
    try:
        CsvDataSeeder(
            database=database,
            raw_data_dir=settings.data_dir,
            policy_extractor=PdfPolicyExtractor(),
        ).seed()
    finally:
        database.close()


if __name__ == "__main__":
    main()
