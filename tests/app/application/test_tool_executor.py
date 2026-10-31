import json

import pytest

from app.application.contracts import ChatInput
from app.application.tool_executor import ToolExecutor


def make_executor(repositories: dict[str, object]) -> ToolExecutor:
    return ToolExecutor(
        catalog=repositories["catalog"],
        promotions=repositories["promotions"],
        orders=repositories["orders"],
        policies=repositories["policies"],
    )


def test_search_products_returns_catalog_data(repositories: dict[str, object]) -> None:
    executor = make_executor(repositories)

    raw_result, sources = executor.execute(
        "search_products",
        {"category_id": 5, "max_price": 1000},
        ChatInput("catalog"),
    )
    result = json.loads(raw_result)

    assert len(result["products"]) == 12
    assert len(sources) == 12


def test_get_product_and_active_promotion_include_calculated_price(
    repositories: dict[str, object],
) -> None:
    executor = make_executor(repositories)

    product_result, _ = executor.execute(
        "get_product",
        {"product_id": 94},
        ChatInput("product"),
    )
    promotion_result, _ = executor.execute(
        "get_active_promotion",
        {"product_id": 94},
        ChatInput("promotion"),
    )

    assert json.loads(product_result)["product"]["available"] is True
    assert json.loads(promotion_result)["promotional_price"] == "R$ 5.519,08"


def test_order_tool_uses_request_identity_instead_of_model_arguments(
    repositories: dict[str, object],
) -> None:
    executor = make_executor(repositories)

    raw_result, _ = executor.execute(
        "get_verified_order",
        {"order_id": 8, "customer_email": "wrong@example.com"},
        ChatInput("order", customer_email="anacarol.ferreira@coldmail.com"),
    )

    assert json.loads(raw_result)["authorized"] is True


def test_order_tool_requires_identity(repositories: dict[str, object]) -> None:
    executor = make_executor(repositories)

    raw_result, sources = executor.execute(
        "get_verified_order",
        {"order_id": 8},
        ChatInput("order"),
    )

    assert json.loads(raw_result) == {
        "authorized": False,
        "verification_required": True,
    }
    assert sources == []


def test_policy_tool_and_invalid_tool_arguments(repositories: dict[str, object]) -> None:
    executor = make_executor(repositories)

    raw_result, sources = executor.execute(
        "search_policies",
        {"query": "devolucao arrependimento compra online"},
        ChatInput("policy"),
    )
    unknown_result, unknown_sources = executor.execute(
        "missing_tool",
        {},
        ChatInput("unknown"),
    )

    assert json.loads(raw_result)["chunks"]
    assert sources[0].source_type == "policy"
    assert json.loads(unknown_result)["error"] == "Unknown tool"
    assert unknown_sources == []
    with pytest.raises(ValueError, match="integer"):
        executor.execute("get_product", {"product_id": "bad"}, ChatInput("product"))
