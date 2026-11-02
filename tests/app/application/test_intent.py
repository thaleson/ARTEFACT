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


def test_router_detects_product_name_after_tem() -> None:
    intent = IntentRouter().route("Tem Yamaha C40?")

    assert intent.kind == "product_detail"
    assert intent.product_query == "yamaha c40"


def test_router_detects_order_and_preserves_provided_id() -> None:
    intent = IntentRouter().route("Qual o status do meu pedido?", provided_order_id=8)

    assert intent.kind == "order_status"
    assert intent.order_id == 8


def test_router_extracts_order_id_with_punctuation() -> None:
    intent = IntentRouter().route("Qual o status do pedido: 8 e meu e-mail é cliente@exemplo.com")

    assert intent.kind == "order_status"
    assert intent.order_id == 8


def test_router_detects_policy_accessories_and_unknown_messages() -> None:
    router = IntentRouter()

    assert router.route("Posso devolver uma compra online?").kind == "policy"
    assert router.route("Me arrependi da minha compra, posso devolver meu pedido?").kind == "policy"
    assert router.route("Posso devolver meu pedido?").kind == "policy"
    assert router.route("Onde fica a loja?").kind == "policy"
    assert router.route("Qual o prazo de entrega para outra cidade?").kind == "policy"
    assert router.route("Vocês vendem cabos?").kind == "accessory"
    assert router.route("Quero conversar sobre futebol").kind == "unknown"

    combined_policy = router.route("Qual o endereço e o horário da loja?")
    assert combined_policy.policy_query == "endereco empresa horario funcionamento"
    assert router.route("Qual o endereço da loja?").policy_query == "endereco"
    assert router.route("Qual o WhatsApp da loja?").policy_query == "whatsapp atendimento remoto"

    assert router.route("Cordas orquestrais").kind == "product_search"
    assert router.route("Cordas orquestrais").category_id == 8


def test_router_detects_active_promotion_list() -> None:
    intent = IntentRouter().route("Quais promoções estão ativas?")

    assert intent.kind == "promotion_search"
    assert intent.product_query is None


def test_router_distinguishes_instrument_variants_from_accessories() -> None:
    intent = IntentRouter().route("Vocês têm violão de 7 cordas?")

    assert intent.kind == "product_search"
    assert intent.category_id == 5
    assert intent.product_query == "7 cordas"


def test_router_does_not_match_baixo_inside_abaixo() -> None:
    intent = IntentRouter().route("Quero um violão abaixo de 1000 reais")

    assert intent.kind == "product_search"
    assert intent.category_id == 5
    assert intent.max_price == Decimal("1000")


def test_router_detects_product_stock_and_payment_context() -> None:
    router = IntentRouter()

    stock = router.route("Tem Takamine GD20 em estoque?")
    parcel = router.route("Posso parcelar em 6 vezes?")
    pix = router.route("Quanto custa o Taylor 110e no PIX?")

    assert stock.kind == "product_detail"
    assert stock.product_query == "takamine gd20"
    assert parcel.kind == "policy"
    assert parcel.policy_query == "parcelamento pagamento"
    assert pix.kind == "product_detail"
    assert pix.product_query == "taylor 110e"
    assert pix.payment_method == "pix"


def test_router_preserves_decimal_price_limits() -> None:
    intent = IntentRouter().route("Quais produtos custam abaixo de R$ 1.000.50?")

    assert intent.max_price == Decimal("1000.50")


def test_router_detects_defect_exchange_policy() -> None:
    intent = IntentRouter().route("Meu instrumento veio com defeito")

    assert intent.kind == "policy"
    assert intent.policy_query == "troca defeito produto"
