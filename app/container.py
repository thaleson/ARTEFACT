"""Dependency composition for the application runtime."""

from dataclasses import dataclass

from app.application.llm_agent import LlmSupportAgent
from app.application.model_provider import OpenAICompatibleChatModel
from app.application.offline_agent import OfflineSupportAgent
from app.application.tool_executor import ToolExecutor
from app.config import Settings
from app.infrastructure.database import SqliteDatabase
from app.infrastructure.policy_extractor import PdfPolicyExtractor
from app.infrastructure.repositories import (
    SqliteCatalogRepository,
    SqliteOrderRepository,
    SqlitePolicyRepository,
    SqlitePromotionRepository,
)
from app.infrastructure.seeder import CsvDataSeeder


@dataclass
class ApplicationContainer:
    """Own the database connection and configured support agent.

    Attributes:
        database (SqliteDatabase): Database resource owned by the container.
        agent (OfflineSupportAgent | LlmSupportAgent): Configured support agent.
    """

    database: SqliteDatabase
    agent: OfflineSupportAgent | LlmSupportAgent

    def close(self) -> None:
        """Release the database resource owned by the container."""
        self.database.close()


def build_container(settings: Settings) -> ApplicationContainer:
    """Build repositories, agents, and database state from application settings.

    Args:
        settings (Settings): Runtime paths and model configuration.

    Returns:
        ApplicationContainer: Fully wired application dependencies.
    """
    database = SqliteDatabase(settings.database_path)
    CsvDataSeeder(
        database=database,
        raw_data_dir=settings.data_dir,
        policy_extractor=PdfPolicyExtractor(),
    ).seed()
    catalog = SqliteCatalogRepository(database.connection)
    promotions = SqlitePromotionRepository(database.connection)
    orders = SqliteOrderRepository(database.connection)
    policies = SqlitePolicyRepository(database.connection)
    offline_agent = OfflineSupportAgent(catalog, promotions, orders, policies)
    if settings.agent_mode == "llm" and settings.llm_api_key:
        model = OpenAICompatibleChatModel(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
        agent: OfflineSupportAgent | LlmSupportAgent = LlmSupportAgent(
            model=model,
            tools=ToolExecutor(catalog, promotions, orders, policies),
            fallback=offline_agent,
        )
    else:
        agent = offline_agent
    return ApplicationContainer(database=database, agent=agent)
