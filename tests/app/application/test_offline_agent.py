import pytest

from app.application.contracts import ChatInput
from app.application.offline_agent import OfflineSupportAgent


def test_product_search_returns_only_expected_available_products(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(
        ChatInput("Quais violões estão disponíveis por até R$ 1.000?")
    )

    assert "Encontrei 12" in response.reply
    assert "Giannini GF-3D" not in response.reply
    assert "Shelby SN-7C" not in response.reply
    assert len(response.sources) == 12


def test_product_detail_returns_price_and_description(offline_agent: OfflineSupportAgent) -> None:
    response = offline_agent.respond(ChatInput("Quanto custa o Takamine GD20?"))

    assert "R$ 2.199,00" in response.reply
    assert "5 unidade(s) em estoque" in response.reply
    assert "tampo sólido em cedro" in response.reply


def test_active_promotion_shows_original_and_promotional_prices(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Quanto custa o Taylor 110e?"))

    assert "R$ 5.999,00" in response.reply
    assert "R$ 5.519,08" in response.reply
    assert "8%" in response.reply


def test_promotion_search_lists_only_active_promotions(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Quais promoções estão ativas?"))

    assert "Taylor 110e" in response.reply
    assert "Takamine GD20" not in response.reply
    assert len(response.sources) == 4


def test_order_requires_identity_and_returns_verified_data(
    offline_agent: OfflineSupportAgent,
) -> None:
    missing_identity = offline_agent.respond(ChatInput("Qual o status do pedido 8?"))
    verified = offline_agent.respond(
        ChatInput(
            "Qual o status do pedido 8?",
            customer_email="anacarol.ferreira@coldmail.com",
        )
    )

    assert "Por segurança" in missing_identity.reply
    assert "está enviado" in verified.reply
    assert "BRJL5544332BR" in verified.reply


def test_invalid_identity_does_not_reveal_order(offline_agent: OfflineSupportAgent) -> None:
    response = offline_agent.respond(
        ChatInput("Qual o status do pedido 8?", customer_email="wrong@example.com")
    )

    assert "Não consegui validar" in response.reply
    assert "BRJL5544332BR" not in response.reply


def test_policy_and_scope_responses_are_grounded(offline_agent: OfflineSupportAgent) -> None:
    return_response = offline_agent.respond(
        ChatInput("Me arrependi da compra online, posso devolver?")
    )
    accessory_response = offline_agent.respond(ChatInput("Vocês vendem cordas?"))

    assert "7 dias corridos" in return_response.reply
    assert "instrumentos musicais" in accessory_response.reply
    assert "cordas" in accessory_response.reply


def test_unknown_and_missing_product_requests_are_safe(offline_agent: OfflineSupportAgent) -> None:
    unknown = offline_agent.respond(ChatInput("Quero falar sobre futebol"))
    missing = offline_agent.respond(ChatInput("Quanto custa o produto inexistente?"))

    assert "Posso ajudar" in unknown.reply
    assert "Não encontrei" in missing.reply


def test_empty_message_is_rejected(offline_agent: OfflineSupportAgent) -> None:
    with pytest.raises(ValueError, match="empty"):
        offline_agent.respond(ChatInput("   "))
