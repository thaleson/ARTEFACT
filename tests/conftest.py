from pathlib import Path

import pytest

from app.application.offline_agent import OfflineSupportAgent
from app.domain.models import PolicyChunk
from app.infrastructure.database import SqliteDatabase
from app.infrastructure.repositories import (
    SqliteCatalogRepository,
    SqliteOrderRepository,
    SqlitePolicyRepository,
    SqlitePromotionRepository,
)
from app.infrastructure.seeder import CsvDataSeeder


class StaticPolicyExtractor:
    def extract(self, pdf_path: Path) -> list[PolicyChunk]:
        return [
            PolicyChunk(
                1,
                1,
                "Empório da Música, Rua 14 de Maio, 3200 — Centro, "
                "Campo Grande - MS, CEP 79202-333.",
            ),
            PolicyChunk(
                2,
                2,
                "Segunda a sexta-feira: 09:00 às 18:00. Sábado: 09:00 às 13:00.",
            ),
            PolicyChunk(
                3,
                3,
                "PIX tem 5% de desconto. Cartão de crédito em até 12x sem juros.",
            ),
            PolicyChunk(
                4,
                4,
                "Compras online podem ser devolvidas em até 7 dias corridos "
                "após o recebimento, sem necessidade de justificativa.",
            ),
            PolicyChunk(
                5,
                5,
                "PAC: 5 a 12 dias úteis. SEDEX: 2 a 5 dias úteis.",
            ),
            PolicyChunk(
                6,
                6,
                "Promoções não são cumulativas e o desconto de PIX não se aplica "
                "a preços promocionais.",
            ),
            PolicyChunk(
                7,
                7,
                "Todos os produtos possuem garantia legal de 90 dias contra "
                "defeitos de fabricação.",
            ),
        ]


@pytest.fixture
def database() -> SqliteDatabase:
    database = SqliteDatabase(Path(":memory:"))
    CsvDataSeeder(
        database=database,
        raw_data_dir=Path("data/raw"),
        policy_extractor=StaticPolicyExtractor(),
    ).seed()
    yield database
    database.close()


@pytest.fixture
def repositories(database: SqliteDatabase) -> dict[str, object]:
    connection = database.connection
    return {
        "catalog": SqliteCatalogRepository(connection),
        "orders": SqliteOrderRepository(connection),
        "policies": SqlitePolicyRepository(connection),
        "promotions": SqlitePromotionRepository(connection),
    }


@pytest.fixture
def offline_agent(repositories: dict[str, object]) -> OfflineSupportAgent:
    return OfflineSupportAgent(
        catalog=repositories["catalog"],
        promotions=repositories["promotions"],
        orders=repositories["orders"],
        policies=repositories["policies"],
    )
