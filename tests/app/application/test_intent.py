from decimal import Decimal

from app.application.intent import IntentRouter


def test_router_detects_catalog_filter_in_portuguese() -> None:
    intent = IntentRouter().route("Quais opções de violões até R$ 1.000?")

    assert intent.kind == "product_search"
    assert intent.category_id == 5
    assert intent.max_price == Decimal("1000")


def test_router_detects_product_detail() -> None:
    intent = IntentRouter().route("Quanto custa o Takamine GD20?")

    assert intent.kind == "product_detail"
    assert intent.product_query == "takamine gd20"


def test_router_detects_order_and_preserves_provided_id() -> None:
    intent = IntentRouter().route("Qual o status do meu pedido?", provided_order_id=8)

    assert intent.kind == "order_status"
    assert intent.order_id == 8


def test_router_detects_policy_accessories_and_unknown_messages() -> None:
    router = IntentRouter()

    assert router.route("Posso devolver uma compra online?").kind == "policy"
    assert router.route("Me arrependi da minha compra, posso devolver meu pedido?").kind == "policy"
    assert router.route("Onde fica a loja?").kind == "policy"
    assert router.route("Qual o prazo de entrega para outra cidade?").kind == "policy"
    assert router.route("Vocês vendem cabos?").kind == "accessory"
    assert router.route("Quero conversar sobre futebol").kind == "unknown"

    combined_policy = router.route("Qual o endereço e o horário da loja?")
    assert combined_policy.policy_query == "endereco empresa horario funcionamento"
    assert router.route("Qual o endereço da loja?").policy_query == "endereco"


def test_router_detects_active_promotion_list() -> None:
    intent = IntentRouter().route("Quais promoções estão ativas?")

    assert intent.kind == "promotion_search"
    assert intent.product_query is None
