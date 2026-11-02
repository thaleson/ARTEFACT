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


def test_stringed_instrument_variant_uses_catalog_search(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Vocês têm violão de 7 cordas?"))

    assert "Encontrei 4" in response.reply
    assert "Rozini RV-174 7 Cordas" in response.reply
    assert "Shelby SN-7C" not in response.reply


def test_stock_question_resolves_product_detail(offline_agent: OfflineSupportAgent) -> None:
    response = offline_agent.respond(ChatInput("Tem Takamine GD20 em estoque?"))

    assert "R$ 2.199,00" in response.reply
    assert "5 unidade(s) em estoque" in response.reply


def test_product_name_question_resolves_without_price_keyword(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Tem Yamaha C40?"))

    assert "Yamaha C40 Nylon Natural" in response.reply
    assert "R$ 599,90" in response.reply


def test_pix_price_applies_discount_when_no_promotion(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Quanto custa o Takamine GD20 no PIX?"))

    assert "R$ 2.089,05 no PIX" in response.reply
    assert "R$ 2.199,00" in response.reply


def test_decimal_price_limit_is_not_treated_as_thousands(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(
        ChatInput("Quais violões estão disponíveis abaixo de R$ 1.000.50?")
    )

    assert "Encontrei 12" in response.reply


def test_orchestral_strings_are_instrument_category(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Cordas orquestrais"))

    assert "exclusivamente com instrumentos" not in response.reply
    assert "Não encontrei opções" in response.reply


def test_policy_questions_do_not_become_catalog_search(
    offline_agent: OfflineSupportAgent,
) -> None:
    defect = offline_agent.respond(ChatInput("Meu instrumento veio com defeito"))
    installments = offline_agent.respond(ChatInput("Posso parcelar em 6 vezes?"))
    pix = offline_agent.respond(ChatInput("Quanto custa o Taylor 110e no PIX?"))

    assert "30 dias corridos" in defect.reply
    assert "4x a 6x" in installments.reply
    assert "R$ 5.519,08" in pix.reply
    assert pix.sources[0].source_type == "catalog"


def test_return_question_with_order_word_stays_in_policy_flow(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Posso devolver meu pedido?"))

    assert "Segundo o manual" in response.reply
    assert "dias corridos" in response.reply


def test_whatsapp_question_prefers_remote_channel(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(ChatInput("Qual o WhatsApp da loja?"))

    assert "(67) 3321-4500" in response.reply
    assert "(67) 3341-4444" not in response.reply


def test_order_number_and_identity_in_same_message_are_used(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(
        ChatInput(
            "Qual o status do pedido: 8 e meu e-mail é "
            "anacarol.ferreira@coldmail.com"
        )
    )

    assert "BRJL5544332BR" in response.reply


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


def test_identity_follow_up_completes_order_lookup(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(
        ChatInput(
            "Meu e-mail é anacarol.ferreira@coldmail.com",
            order_id=8,
        )
    )

    assert "está enviado" in response.reply
    assert "BRJL5544332BR" in response.reply


def test_standalone_email_follow_up_completes_order_lookup(
    offline_agent: OfflineSupportAgent,
) -> None:
    response = offline_agent.respond(
        ChatInput(
            "anacarol.ferreira@coldmail.com",
            order_id=8,
        )
    )

    assert "está enviado" in response.reply
    assert "BRJL5544332BR" in response.reply


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
