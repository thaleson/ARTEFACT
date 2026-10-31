"""Streamlit session-state helpers for the demonstration conversation."""

from typing import cast

import streamlit as st

from frontend.models import OrderContext, SourceReference


WELCOME_MESSAGE = (
    "Olá! Eu sou o assistente da Empório da Música. 🎶 "
    "Posso ajudar com instrumentos, preços, estoque, promoções, "
    "pedidos e políticas da loja."
)


def initialize_session() -> None:
    """Create the initial conversation and pending-message state."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MESSAGE, "sources": ()}
        ]
    st.session_state.setdefault("pending_message", None)


def messages() -> list[dict[str, object]]:
    """Return the current conversation message list.

    Returns:
        list[dict[str, object]]: Mutable messages stored in the current session.
    """
    return cast(list[dict[str, object]], st.session_state.messages)


def append_message(
    role: str,
    content: str,
    sources: tuple[SourceReference, ...] = (),
) -> None:
    """Append one role/content/source record to the conversation.

    Args:
        role (str): Message role, either user or assistant.
        content (str): Renderable message text.
        sources (tuple[SourceReference, ...]): Optional backend sources.
    """
    messages().append({"role": role, "content": content, "sources": sources})


def set_pending_message(message: str) -> None:
    """Store a quick-action message for processing after rerun.

    Args:
        message (str): Prompt selected by the user.
    """
    st.session_state.pending_message = message


def consume_pending_message() -> object:
    """Read and clear the one-shot quick-action message.

    Returns:
        object: Pending message value, if one was stored.
    """
    return st.session_state.pop("pending_message", None)


def order_context() -> OrderContext:
    """Build order-verification context from sidebar fields.

    Returns:
        OrderContext: Optional normalized order ID, email, and phone.
    """
    raw_order_id = st.session_state.get("order_id_input", "")
    order_id: int | None = None
    if isinstance(raw_order_id, int) and raw_order_id > 0:
        order_id = raw_order_id
    elif isinstance(raw_order_id, str) and raw_order_id.strip().isdigit():
        parsed_order_id = int(raw_order_id.strip())
        order_id = parsed_order_id if parsed_order_id > 0 else None
    email = st.session_state.get("customer_email", "")
    phone = st.session_state.get("customer_phone", "")
    return OrderContext(
        order_id=order_id,
        customer_email=email.strip() if isinstance(email, str) and email.strip() else None,
        customer_phone=phone.strip() if isinstance(phone, str) and phone.strip() else None,
    )
