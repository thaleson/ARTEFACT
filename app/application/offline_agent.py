"""Deterministic support agent for local execution and automated verification."""

from app.application.contracts import AgentResponse, ChatInput, SourceReference
from app.application.formatting import format_order, format_product_line
from app.application.input_normalizer import enrich_identity
from app.application.intent import DetectedIntent, IntentRouter
from app.domain.ports import (
    CatalogRepository,
    OrderRepository,
    PolicyRepository,
    PromotionRepository,
)
from app.domain.rules import is_available


class OfflineSupportAgent:
    """Answer supported customer scenarios without an external model.

    The agent delegates catalog, promotion, order, and policy facts to injected
    repositories and keeps response composition separate from data access.

    Attributes:
        catalog (CatalogRepository): Product catalog access boundary.
        promotions (PromotionRepository): Active promotion access boundary.
        orders (OrderRepository): Verified order access boundary.
        policies (PolicyRepository): Policy retrieval boundary.
        router (IntentRouter): Deterministic message classifier.
    """

    def __init__(
        self,
        catalog: CatalogRepository,
        promotions: PromotionRepository,
        orders: OrderRepository,
        policies: PolicyRepository,
        router: IntentRouter | None = None,
    ) -> None:
        self.catalog = catalog
        self.promotions = promotions
        self.orders = orders
        self.policies = policies
        self.router = router or IntentRouter()

    def respond(self, chat_input: ChatInput) -> AgentResponse:
        """Route one customer message to the appropriate support handler.

        Args:
            chat_input (ChatInput): Customer message and optional verification context.

        Returns:
            AgentResponse: Customer-facing answer with source references.

        Raises:
            ValueError: If the message is blank.
        """
        chat_input = enrich_identity(chat_input)
        message = chat_input.message.strip()
        if not message:
            raise ValueError("Message cannot be empty")
        intent = self.router.route(message, chat_input.order_id)
        handlers = {
            "accessory": self._accessory_response,
            "order_status": lambda: self._order_response(intent, chat_input),
            "product_search": lambda: self._product_search_response(intent),
            "product_detail": lambda: self._product_detail_response(intent),
            "promotion_search": self._promotion_search_response,
            "policy": lambda: self._policy_response(intent),
            "unknown": self._unknown_response,
        }
        return handlers[intent.kind]()

    def _accessory_response(self) -> AgentResponse:
        """Explain that the store does not sell accessories.

        Returns:
            AgentResponse: Scope clarification in the store's tone.
        """
        return AgentResponse(
            reply=(
                "A gente trabalha exclusivamente com instrumentos musicais. "
                "Não comercializamos cordas, palhetas, cabos, cases, pedais ou "
                "amplificadores. Posso ajudar a encontrar um instrumento?"
            ),
            mode="offline",
        )

    def _order_response(
        self,
        intent: DetectedIntent,
        chat_input: ChatInput,
    ) -> AgentResponse:
        """Handle order lookup with identity verification and safe refusal.

        Args:
            intent (DetectedIntent): Detected order intent and optional order ID.
            chat_input (ChatInput): Message and explicit customer identity values.

        Returns:
            AgentResponse: Verification request, safe refusal, or authorized order data.
        """
        if intent.order_id is None:
            return AgentResponse(
                reply=(
                    "Para consultar o pedido, preciso do número dele e do e-mail "
                    "ou telefone cadastrado. Essas informações são necessárias "
                    "para proteger seus dados."
                ),
                mode="offline",
            )
        if not chat_input.customer_email and not chat_input.customer_phone:
            return AgentResponse(
                reply=(
                    "Por segurança, confirme o e-mail ou telefone cadastrado junto "
                    "com o número do pedido para eu consultar o status."
                ),
                mode="offline",
            )
        order = self.orders.get_verified_order(
            order_id=intent.order_id,
            customer_email=chat_input.customer_email,
            customer_phone=chat_input.customer_phone,
        )
        if order is None:
            return AgentResponse(
                reply=(
                    "Não consegui validar os dados informados. Confira o número do "
                    "pedido e o e-mail ou telefone cadastrado; por segurança, não "
                    "posso confirmar detalhes sem essa validação."
                ),
                mode="offline",
            )
        return AgentResponse(
            reply=format_order(order),
            mode="offline",
            sources=[SourceReference("order", f"order:{order.order_id}")],
        )

    def _product_search_response(self, intent: DetectedIntent) -> AgentResponse:
        """Search and format currently available catalog products.

        Args:
            intent (DetectedIntent): Catalog filters extracted from the message.

        Returns:
            AgentResponse: Matching products and catalog source references.
        """
        products = self.catalog.search_products(
            category_id=intent.category_id,
            max_price=intent.max_price,
            available_only=True,
        )
        if not products:
            return AgentResponse(
                reply="Não encontrei opções disponíveis com esses filtros no catálogo atual.",
                mode="offline",
            )
        lines = []
        sources = []
        for product in products:
            promotion = self.promotions.get_active_for_product(product.product_id)
            lines.append(format_product_line(product, promotion))
            sources.append(
                SourceReference("catalog", f"product:{product.product_id}")
            )
        intro = f"Encontrei {len(products)} opção(ões) disponível(is):"
        return AgentResponse(
            reply=f"{intro}\n" + "\n".join(lines),
            mode="offline",
            sources=sources,
        )

    def _product_detail_response(self, intent: DetectedIntent) -> AgentResponse:
        """Resolve a product query and present catalog details or alternatives.

        Args:
            intent (DetectedIntent): Product terms extracted from the message.

        Returns:
            AgentResponse: Product detail, disambiguation, or safe not-found response.
        """
        if not intent.product_query:
            return AgentResponse(
                reply="Qual é o nome ou modelo do instrumento que você quer consultar?",
                mode="offline",
            )
        products = self.catalog.search_products(
            query=intent.product_query,
            available_only=False,
        )
        if not products:
            return AgentResponse(
                reply="Não encontrei esse produto no catálogo fornecido.",
                mode="offline",
            )
        if len(products) > 1:
            lines = [format_product_line(product) for product in products[:5]]
            return AgentResponse(
                reply=(
                    "Encontrei mais de um produto parecido. Você quis dizer:\n"
                    + "\n".join(lines)
                ),
                mode="offline",
                sources=[
                    SourceReference("catalog", f"product:{product.product_id}")
                    for product in products[:5]
                ],
            )
        product = products[0]
        promotion = self.promotions.get_active_for_product(product.product_id)
        detail = format_product_line(
            product,
            promotion if is_available(product) else None,
        )
        return AgentResponse(
            reply=f"Aqui estão os dados do catálogo:\n{detail}\n{product.description}",
            mode="offline",
            sources=[SourceReference("catalog", f"product:{product.product_id}")],
        )

    def _promotion_search_response(self) -> AgentResponse:
        """List active promotions attached to currently available products.

        Returns:
            AgentResponse: Active promotion summaries and source references.
        """
        products = self.catalog.search_products(available_only=True)
        promoted = []
        sources = []
        for product in products:
            promotion = self.promotions.get_active_for_product(product.product_id)
            if promotion is not None:
                promoted.append(format_product_line(product, promotion))
                sources.append(
                    SourceReference("promotion", f"promotion:product:{product.product_id}")
                )
        if not promoted:
            return AgentResponse(
                reply="Não encontrei promoções ativas para produtos disponíveis.",
                mode="offline",
            )
        return AgentResponse(
            reply="Estas são as promoções ativas no catálogo:\n" + "\n".join(promoted),
            mode="offline",
            sources=sources,
        )

    def _policy_response(self, intent: DetectedIntent) -> AgentResponse:
        """Retrieve and present the most relevant store-policy passages.

        Args:
            intent (DetectedIntent): Policy retrieval query.

        Returns:
            AgentResponse: Grounded policy excerpts and page references.
        """
        chunks = self.policies.search(intent.policy_query or "", limit=3)
        if not chunks:
            return AgentResponse(
                reply=(
                    "Não encontrei uma regra específica para essa dúvida no manual. "
                    "Posso encaminhar o caso para a equipe da loja."
                ),
                mode="offline",
            )
        excerpts = [
            f"(p. {chunk.page_number}) {_compact(chunk.content)}" for chunk in chunks
        ]
        return AgentResponse(
            reply="Segundo o manual da loja:\n" + "\n".join(excerpts),
            mode="offline",
            sources=[
                SourceReference("policy", f"page:{chunk.page_number}")
                for chunk in chunks
            ],
        )

    def _unknown_response(self) -> AgentResponse:
        """Explain the supported scope when intent cannot be resolved.

        Returns:
            AgentResponse: Safe clarification prompt.
        """
        return AgentResponse(
            reply=(
                "Posso ajudar com instrumentos do catálogo, preços, disponibilidade, "
                "promoções, pedidos e políticas de pagamento, troca, entrega ou "
                "garantia. O que você gostaria de consultar?"
            ),
            mode="offline",
        )


def _compact(content: str, maximum_length: int = 500) -> str:
    """Collapse whitespace and truncate a policy excerpt for chat output.

    Args:
        content (str): Retrieved policy content.
        maximum_length (int): Maximum output length including the ellipsis.

    Returns:
        str: Compact policy excerpt.
    """
    compacted = " ".join(content.split())
    if len(compacted) <= maximum_length:
        return compacted
    return compacted[: maximum_length - 3].rstrip() + "..."
