"""Typed contracts exchanged by the application layer."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChatInput:
    """Represent one customer message and optional order-verification context."""

    message: str
    order_id: int | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


@dataclass(frozen=True)
class SourceReference:
    """Identify the operational or policy source used in a response."""

    source_type: str
    reference: str


@dataclass(frozen=True)
class AgentResponse:
    """Contain the assistant reply, execution mode, and source references."""

    reply: str
    mode: str
    sources: list[SourceReference] = field(default_factory=list)
