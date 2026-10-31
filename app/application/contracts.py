from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChatInput:
    message: str
    order_id: int | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


@dataclass(frozen=True)
class SourceReference:
    source_type: str
    reference: str


@dataclass(frozen=True)
class AgentResponse:
    reply: str
    mode: str
    sources: list[SourceReference] = field(default_factory=list)
