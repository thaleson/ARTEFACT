"""Typed values exchanged between the Streamlit client and backend API."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderContext:
    """Represent optional order-verification fields entered in the sidebar."""

    order_id: int | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


@dataclass(frozen=True)
class SourceReference:
    """Represent a non-sensitive backend source reference."""

    source_type: str
    reference: str


@dataclass(frozen=True)
class ChatResult:
    """Contain a backend reply and its execution metadata."""

    reply: str
    mode: str
    sources: tuple[SourceReference, ...]
