from app.application.contracts import ChatInput
from app.application.input_normalizer import enrich_identity


def test_identity_is_extracted_from_explicit_message_content() -> None:
    result = enrich_identity(
        ChatInput(
            "Pedido 8, meu e-mail é anacarol.ferreira@coldmail.com e "
            "meu telefone é (67) 99654-7821"
        )
    )

    assert result.customer_email == "anacarol.ferreira@coldmail.com"
    assert result.customer_phone == "(67) 99654-7821"


def test_explicit_request_fields_take_precedence() -> None:
    request = ChatInput(
        "Pedido 8 e-mail wrong@example.com",
        customer_email="anacarol.ferreira@coldmail.com",
    )

    result = enrich_identity(request)

    assert result.customer_email == "anacarol.ferreira@coldmail.com"
