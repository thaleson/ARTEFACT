"""Conversation rendering and message submission components."""

import httpx
import streamlit as st

from frontend.api_client import BackendClient
from frontend.models import ChatResult, SourceReference
from frontend.session import (
    append_message,
    consume_pending_message,
    messages,
    order_context,
)


def render_messages() -> None:
    """Render the current conversation and non-sensitive source references."""
    for message in messages():
        role = str(message["role"])
        avatar = "🎵" if role == "assistant" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.markdown(str(message["content"]))
            sources = message.get("sources", ())
            if isinstance(sources, tuple) and sources:
                _render_sources(sources)


def process_messages(client: BackendClient) -> None:
    """Process chat input and quick-action prompts through the backend.

    Args:
        client (BackendClient): Backend client used for message submission.
    """
    typed_message = st.chat_input("Digite sua dúvida para a loja...")
    pending_message = consume_pending_message()
    message = typed_message or pending_message
    if not isinstance(message, str) or not message.strip():
        return
    normalized_message = message.strip()
    append_message("user", normalized_message)
    with st.chat_message("assistant", avatar="🎵"):
        with st.spinner("Consultando o catálogo e as políticas..."):
            try:
                result = client.chat(normalized_message, order_context())
            except httpx.HTTPError:
                result = _connection_error_result()
            except ValueError:
                result = _invalid_response_result()
        st.markdown(result.reply)
    append_message("assistant", result.reply, result.sources)


def _render_sources(sources: tuple[SourceReference, ...]) -> None:
    """Render expandable source references for one assistant message.

    Args:
        sources (tuple[SourceReference, ...]): Sources used by the backend response.
    """
    with st.expander("Fontes consultadas", expanded=False):
        for source in sources:
            st.caption(f"{source.source_type} · {source.reference}")


def _connection_error_result() -> ChatResult:
    """Build a safe response for backend connectivity failures."""
    return ChatResult(
        reply="Não consegui conectar ao atendimento agora. Tente novamente em instantes.",
        mode="error",
        sources=(),
    )


def _invalid_response_result() -> ChatResult:
    """Build a safe response for malformed backend payloads."""
    return ChatResult(
        reply="Recebi uma resposta inválida do atendimento. Tente novamente.",
        mode="error",
        sources=(),
    )
