import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.domain.rules import normalize_text


@dataclass(frozen=True)
class DetectedIntent:
    kind: str
    product_query: str | None = None
    category_id: int | None = None
    max_price: Decimal | None = None
    policy_query: str | None = None
    order_id: int | None = None


class IntentRouter:
    def route(self, message: str, provided_order_id: int | None = None) -> DetectedIntent:
        normalized = normalize_text(message)
        if _contains_any(normalized, ("corda", "palheta", "cabo", "case", "pedal", "amplificador")):
            return DetectedIntent(kind="accessory")
        if _contains_any(normalized, ("pedido", "rastreamento", "rastreio")):
            return DetectedIntent(
                kind="order_status",
                order_id=provided_order_id or _extract_order_id(message),
            )
        policy_terms = (
            "endereco", "horario", "pagamento", "troca", "devolucao", "devolver",
            "arrependimento", "arrependi", "frete", "garantia", "privacidade", "lgpd",
            "whatsapp", "telefone", "email", "entrega", "prazo", "envio", "correios",
            "pac", "sedex", "pix", "cartao", "boleto",
        )
        if _contains_any(normalized, policy_terms):
            return DetectedIntent(
                kind="policy",
                policy_query=_policy_query(normalized, message),
            )
        detail_terms = ("preco", "custa", "valor", "detalhes", "especificacao")
        if _contains_any(normalized, detail_terms) and _extract_max_price(message) is None:
            return DetectedIntent(
                kind="product_detail",
                product_query=_product_query(normalized),
            )
        if _contains_any(normalized, ("promocao", "promocoes", "desconto")):
            product_query = _product_query(normalized)
            return DetectedIntent(
                kind="product_detail" if product_query else "promotion_search",
                product_query=product_query or None,
            )
        category_id = _category_id(normalized)
        max_price = _extract_max_price(message)
        if category_id is not None or max_price is not None or _contains_any(
            normalized, ("produto", "catalogo", "disponivel", "instrumento")
        ):
            return DetectedIntent(
                kind="product_search",
                category_id=category_id,
                max_price=max_price,
            )
        return DetectedIntent(kind="unknown")


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term in value for term in terms)


def _category_id(message: str) -> int | None:
    category_terms = {
        1: ("guitarra",),
        2: ("baixo", "contrabaixo"),
        3: ("bateria", "percussao"),
        4: ("teclado", "piano", "sintetizador"),
        5: ("violao", "violo"),
        6: ("flauta", "clarinete", "saxofone", "madeira"),
        7: ("trompete", "trombone", "tuba", "metais"),
        8: ("violino", "viola", "violoncelo", "orquestral"),
        9: ("ukulele",),
    }
    for category_id, terms in category_terms.items():
        if _contains_any(message, terms):
            return category_id
    return None


def _extract_order_id(message: str) -> int | None:
    match = re.search(
        r"(?:pedido|order)\s*(?:n[úu]mero|n[ºo°]?|#)?\s*(\d+)",
        message,
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def _extract_max_price(message: str) -> Decimal | None:
    pattern = r"(?:até|ate|menos de|abaixo de|no máximo|maximo)\s*(?:r\$\s*)?([\d.,]+)"
    match = re.search(pattern, message, re.IGNORECASE)
    if not match:
        return None
    raw_value = match.group(1).replace(".", "").replace(",", ".")
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        return None


def _product_query(normalized_message: str) -> str:
    stop_words = {
        "quanto", "custa", "qual", "preco", "valor", "do", "da", "de", "o", "a",
        "produto", "tem", "detalhes", "sobre", "me", "fale", "especificacao",
        "promocao", "promocoes", "desconto", "existe", "ainda", "ativo", "ativa",
        "ativos", "ativas", "quais", "estao", "ha", "existem",
    }
    terms = [term for term in normalized_message.split() if term not in stop_words]
    return " ".join(terms)


def _policy_query(normalized_message: str, original_message: str) -> str:
    topic_queries = (
        (
            ("devolucao", "devolver", "arrependimento", "arrependi"),
            "devolucao arrependimento compra online",
        ),
        (("troca", "defeito"), "troca defeito produto"),
        (("horario",), "horario funcionamento"),
        (("endereco",), "endereco empresa"),
        (("entrega", "prazo", "frete", "envio"), "entrega prazo frete PAC SEDEX"),
        (("pagamento", "pix", "cartao", "boleto"), "pagamento PIX cartao boleto"),
        (("garantia",), "garantia legal fabricante"),
        (("privacidade", "lgpd"), "privacidade LGPD dados"),
        (("whatsapp", "telefone", "email"), "telefone WhatsApp email"),
    )
    for terms, query in topic_queries:
        if _contains_any(normalized_message, terms):
            return query
    return original_message
