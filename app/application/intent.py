"""Detect supported customer intents from Portuguese messages."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.domain.rules import normalize_text


@dataclass(frozen=True)
class DetectedIntent:
    """Represent the normalized intent and extracted query parameters."""

    kind: str
    product_query: str | None = None
    payment_method: str | None = None
    category_id: int | None = None
    max_price: Decimal | None = None
    policy_query: str | None = None
    order_id: int | None = None


class IntentRouter:
    """Classify messages into deterministic catalog, order, policy, or scope flows.

    The router uses lightweight Portuguese keyword and pattern matching so the core
    scenarios remain available without an external model.
    """

    def route(self, message: str, provided_order_id: int | None = None) -> DetectedIntent:
        """Detect the primary intent for a customer message.

        Args:
            message (str): Customer message in Portuguese.
            provided_order_id (int | None): Optional order ID supplied by the API.

        Returns:
            DetectedIntent: Normalized intent and extracted parameters.
        """
        normalized = normalize_text(message)
        accessory_terms = (
            "corda", "cordas", "palheta", "palhetas", "cabo", "cabos",
            "case", "cases", "pedal", "pedais", "amplificador", "amplificadores",
        )
        if _contains_any(normalized, accessory_terms) and not _is_stringed_instrument_variant(
            normalized
        ):
            return DetectedIntent(kind="accessory")
        order_terms = ("pedido", "rastreamento", "rastreio")
        if _contains_any(normalized, order_terms) and _contains_any(
            normalized, ("status", "rastreamento", "rastreio", "acompanhar")
        ):
            return DetectedIntent(
                kind="order_status",
                order_id=provided_order_id or _extract_order_id(message),
            )

        category_id = _category_id(normalized)
        detail_terms = (
            "preco", "custa", "valor", "detalhes", "especificacao", "tem",
            "estoque", "disponibilidade",
        )
        product_query = _product_query(normalized)
        has_product_reference = (
            category_id is not None
            or bool(re.search(r"\d", product_query))
            or not _contains_any(
                normalized,
                (
                    "endereco", "localizacao", "horario", "funcionamento", "pagamento",
                    "troca", "devolucao", "devolver", "arrependimento", "arrependi",
                    "frete", "garantia", "privacidade", "lgpd", "whatsapp", "telefone",
                    "email", "e mail", "entrega", "prazo", "envio", "correios", "pac", "sedex",
                    "pix", "cartao", "boleto", "defeito", "defeitos", "parcelar",
                    "parcelamento", "vezes",
                ),
            )
        )
        if (
            _contains_any(normalized, detail_terms)
            and _extract_max_price(message) is None
            and product_query
            and has_product_reference
            and _instrument_variant_query(normalized) is None
        ):
            return DetectedIntent(
                kind="product_detail",
                product_query=product_query,
                payment_method=_payment_method(normalized),
            )

        policy_terms = (
            "endereco", "onde fica", "localizacao", "horario", "funcionamento",
            "pagamento", "pagamentos", "troca", "devolucao", "devolver", "arrependimento",
            "arrependi", "frete", "garantia", "privacidade", "lgpd", "whatsapp",
            "telefone", "email", "e mail", "entrega", "prazo", "envio", "correios", "pac",
            "sedex", "pix", "cartao", "boleto", "defeito", "defeitos", "parcelar",
            "parcelamento", "vezes",
        )
        if _contains_any(normalized, policy_terms):
            return DetectedIntent(
                kind="policy",
                policy_query=_policy_query(normalized, message),
            )
        if _contains_any(normalized, order_terms):
            return DetectedIntent(
                kind="order_status",
                order_id=provided_order_id or _extract_order_id(message),
            )
        if _contains_any(normalized, ("promocao", "promocoes", "desconto")):
            product_query = _product_query(normalized)
            return DetectedIntent(
                kind="product_detail" if product_query else "promotion_search",
                product_query=product_query or None,
            )
        max_price = _extract_max_price(message)
        if category_id is not None or max_price is not None or _contains_any(
            normalized,
            (
                "produto", "produtos", "catalogo", "disponivel", "disponiveis",
                "instrumento", "instrumentos",
            ),
        ):
            return DetectedIntent(
                kind="product_search",
                product_query=_instrument_variant_query(normalized),
                category_id=category_id,
                max_price=max_price,
            )
        return DetectedIntent(kind="unknown")


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    """Check whether any configured term occurs in a normalized value.

    Args:
        value (str): Normalized message text.
        terms (tuple[str, ...]): Terms to search for.

    Returns:
        bool: Whether at least one term is present.
    """
    return any(
        re.search(rf"(?<!\w){re.escape(term)}(?!\w)", value) is not None
        for term in terms
    )


def _category_id(message: str) -> int | None:
    """Map instrument keywords to the supplied catalog category IDs.

    Args:
        message (str): Normalized customer message.

    Returns:
        int | None: Matching category ID, if one can be identified.
    """
    category_terms = {
        1: ("guitarra", "guitarras"),
        2: ("baixo", "baixos", "contrabaixo", "contrabaixos"),
        3: ("bateria", "baterias", "percussao"),
        4: (
            "teclado", "teclados", "piano", "pianos", "sintetizador", "sintetizadores",
        ),
        5: ("violao", "violoes"),
        6: (
            "flauta", "flautas", "clarinete", "clarinetes", "saxofone", "saxofones", "madeira",
        ),
        7: (
            "trompete", "trompetes", "trombone", "trombones", "tuba", "tubas", "metais",
        ),
        8: (
            "violino", "violinos", "viola", "violas", "violoncelo", "violoncelos",
            "orquestral", "orquestrais",
        ),
        9: ("ukulele", "ukuleles"),
    }
    for category_id, terms in category_terms.items():
        if _contains_any(message, terms):
            return category_id
    return None


def _extract_order_id(message: str) -> int | None:
    """Extract an order number written next to the word pedido or order.

    Args:
        message (str): Original customer message.

    Returns:
        int | None: Parsed order ID, if present.
    """
    match = re.search(
        r"\b(?:pedido|order)\s*(?:de\s+)?"
        r"(?:(?:n[úu]mero|n[ºo°]?|#)\s*)?[:#-]?\s*(\d+)",
        message,
        re.IGNORECASE,
    )
    return int(match.group(1)) if match else None


def _extract_max_price(message: str) -> Decimal | None:
    """Extract a Portuguese maximum-price constraint from a message.

    Args:
        message (str): Original customer message containing a price limit.

    Returns:
        Decimal | None: Parsed maximum price, if a supported pattern is found.
    """
    pattern = (
        r"(?:até|ate|menos de|abaixo de|no máximo|maximo)\s*"
        r"(?:r\$\s*)?(\d+(?:[.,]\d+)*)"
    )
    match = re.search(pattern, message, re.IGNORECASE)
    if not match:
        return None
    raw_value = _normalize_price_token(match.group(1))
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        return None


def _product_query(normalized_message: str) -> str:
    """Remove conversational stop words and retain product search terms.

    Args:
        normalized_message (str): Accent-free normalized message.

    Returns:
        str: Terms suitable for catalog lookup.
    """
    stop_words = {
        "quanto", "custa", "qual", "preco", "valor", "do", "da", "de", "o", "a",
        "produto", "tem", "voce", "voces", "detalhes", "sobre", "me", "fale", "especificacao",
        "promocao", "promocoes", "desconto", "existe", "ainda", "ativo", "ativa",
        "ativos", "ativas", "quais", "estao", "ha", "existem", "em", "no", "na",
        "estoque", "disponivel", "disponiveis", "disponibilidade", "pix", "real", "reais",
        "via", "por", "pagamento", "pagamentos",
    }
    terms = [term for term in normalized_message.split() if term not in stop_words]
    return " ".join(terms)


def _policy_query(normalized_message: str, original_message: str) -> str:
    """Map common policy wording to stable retrieval terms.

    Args:
        normalized_message (str): Accent-free normalized message.
        original_message (str): Original message used as a fallback query.

    Returns:
        str: Query sent to the policy repository.
    """
    address_terms = ("endereco", "onde fica", "localizacao")
    if _contains_any(normalized_message, address_terms) and _contains_any(
        normalized_message, ("horario", "funcionamento")
    ):
        return "endereco empresa horario funcionamento"
    if _contains_any(normalized_message, ("whatsapp",)) and _contains_any(
        normalized_message, ("telefone", "email", "e mail")
    ):
        return "telefone WhatsApp email"
    topic_queries = (
        (address_terms, "endereco"),
        (
            ("devolucao", "devolver", "arrependimento", "arrependi"),
            "devolucao arrependimento compra online",
        ),
        (("troca", "defeito", "defeitos"), "troca defeito produto"),
        (("horario", "funcionamento"), "horario funcionamento"),
        (("entrega", "prazo", "frete", "envio"), "entrega prazo frete PAC SEDEX"),
        (("parcelar", "parcelamento", "vezes"), "parcelamento pagamento"),
        (
            (
                "pagamento", "pagamentos", "pix", "cartao", "boleto", "parcelar",
                "parcelamento", "vezes",
            ),
            "pagamento PIX cartao boleto",
        ),
        (("garantia",), "garantia legal fabricante"),
        (("privacidade", "lgpd"), "privacidade LGPD dados"),
        (("whatsapp",), "whatsapp atendimento remoto"),
        (("telefone",), "telefone WhatsApp"),
        (("email", "e mail"), "contato"),
        (("whatsapp", "telefone", "email", "e mail"), "telefone WhatsApp email"),
    )
    for terms, query in topic_queries:
        if _contains_any(normalized_message, terms):
            return query
    return original_message


def _is_stringed_instrument_variant(normalized_message: str) -> bool:
    """Recognize numbered-string instruments before accessory classification."""
    return (
        re.search(r"\b\d+\s+cordas?\b", normalized_message) is not None
        and _category_id(normalized_message) in {1, 2, 5, 9}
    ) or (
        _category_id(normalized_message) == 8
        and _contains_any(normalized_message, ("orquestral", "orquestrais"))
    )


def _instrument_variant_query(normalized_message: str) -> str | None:
    """Extract a numbered-string variant for a category-constrained search."""
    match = re.search(r"\b(\d+)\s+cordas?\b", normalized_message)
    return f"{match.group(1)} cordas" if match else None


def _payment_method(normalized_message: str) -> str | None:
    """Extract a supported payment method when it qualifies a product price."""
    return "pix" if _contains_any(normalized_message, ("pix",)) else None


def _normalize_price_token(raw_value: str) -> str:
    """Normalize Brazilian or decimal price notation to Decimal input text."""
    value = raw_value.replace(" ", "")
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            return value.replace(".", "").replace(",", ".")
        return value.replace(",", "")
    if "," in value:
        return value.replace(",", ".")
    if value.count(".") > 1 and len(value.rsplit(".", 1)[-1]) == 2:
        integer_part, decimal_part = value.rsplit(".", 1)
        return f"{integer_part.replace('.', '')}.{decimal_part}"
    parts = value.split(".")
    if len(parts) > 1 and len(parts[-1]) == 3:
        return "".join(parts)
    return value
