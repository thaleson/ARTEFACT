from decimal import Decimal

from app.infrastructure.repositories import (
    SqliteCatalogRepository,
    SqliteOrderRepository,
    SqlitePolicyRepository,
    SqlitePromotionRepository,
)


def test_catalog_search_applies_category_price_and_availability(
    repositories: dict[str, object],
) -> None:
    repository: SqliteCatalogRepository = repositories["catalog"]

    products = repository.search_products(category_id=5, max_price=Decimal("1000"))

    assert len(products) == 12
    assert all(product.category_id == 5 for product in products)
    assert all(product.status == "active" and product.stock_quantity > 0 for product in products)
    assert all(product.product_id != 96 for product in products)


def test_catalog_query_matches_each_term_and_reads_specs(repositories: dict[str, object]) -> None:
    repository: SqliteCatalogRepository = repositories["catalog"]

    products = repository.search_products(query="kala ka abp ctg", available_only=False)
    product = repository.get_product(95)

    assert [item.product_id for item in products] == [130]
    assert product is not None
    assert product.specs["top"] == "Cedro Sólido"


def test_catalog_get_product_returns_none_for_unknown_id(repositories: dict[str, object]) -> None:
    repository: SqliteCatalogRepository = repositories["catalog"]

    assert repository.get_product(999) is None


def test_promotion_repository_returns_only_active_promotion(
    repositories: dict[str, object],
) -> None:
    repository: SqlitePromotionRepository = repositories["promotions"]

    active = repository.get_active_for_product(94)
    inactive = repository.get_active_for_product(95)

    assert active is not None
    assert active.discount_percent == Decimal("8")
    assert inactive is None


def test_order_repository_requires_matching_email_or_phone(repositories: dict[str, object]) -> None:
    repository: SqliteOrderRepository = repositories["orders"]

    authorized = repository.get_verified_order(
        8,
        "anacarol.ferreira@coldmail.com",
        None,
    )
    unauthorized = repository.get_verified_order(8, "wrong@example.com", None)

    assert authorized is not None
    assert authorized.tracking_code == "BRJL5544332BR"
    assert unauthorized is None


def test_policy_repository_ranks_relevant_chunks_and_handles_empty_query(
    repositories: dict[str, object],
) -> None:
    repository: SqlitePolicyRepository = repositories["policies"]

    results = repository.search("Qual o prazo de entrega para outra cidade?")

    assert results[0].page_number == 5
    assert repository.search("!!!") == []
