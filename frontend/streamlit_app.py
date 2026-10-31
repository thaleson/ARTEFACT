"""Streamlit demonstration interface for the Empório da Música support agent."""

import os
from collections.abc import Mapping
from typing import cast

import httpx
import streamlit as st


QUICK_ACTIONS: tuple[tuple[str, str], ...] = (
    ("Catálogo até R$ 1.000", "Quais violões estão disponíveis por até R$ 1.000?"),
    ("Preço do Takamine", "Quanto custa o Takamine GD20?"),
    ("Política de devolução", "Me arrependi da compra online. Posso devolver?"),
    ("Promoções ativas", "Quais promoções estão ativas?"),
)


def main() -> None:
    """Render the customer-support demonstration application."""
    st.set_page_config(
        page_title="Empório da Música | Atendimento",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _render_styles()
    _initialize_state()
    _render_sidebar()
    _render_header()
    _render_quick_actions()
    _render_messages()
    _process_pending_message()


def _initialize_state() -> None:
    """Initialize chat history and one-shot quick-action state."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Eu sou o assistente da Empório da Música. 🎶 "
                    "Posso ajudar com instrumentos, preços, estoque, promoções, "
                    "pedidos e políticas da loja."
                ),
                "sources": [],
            }
        ]
    st.session_state.setdefault("pending_message", None)


def _render_sidebar() -> None:
    """Render brand information, backend status, and order context fields."""
    with st.sidebar:
        st.markdown(
            '<div class="brand-mark"><span>♫</span><div><b>EMPÓRIO</b>'
            '<small>DA MÚSICA</small></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="sidebar-copy">Sua música começa aqui.</p>',
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown("### Status do atendimento")
        if _backend_is_available():
            st.success("Backend conectado", icon="✅")
        else:
            st.error("Backend indisponível", icon="⚠️")
        st.caption(f"API: {_backend_url()}")
        st.divider()
        st.markdown("### Consultar pedido")
        st.caption("Preencha os dados somente quando quiser consultar um pedido.")
        st.number_input(
            "Número do pedido",
            min_value=0,
            step=1,
            key="order_id",
            help="Obrigatório junto com e-mail ou telefone para ver o status.",
        )
        st.text_input("E-mail cadastrado", key="customer_email")
        st.text_input("Telefone cadastrado", key="customer_phone")
        st.divider()
        st.caption("SQLite • Policy retrieval • Function calling opcional")


def _render_header() -> None:
    """Render the main product title and value proposition."""
    st.markdown(
        '<div class="hero"><div class="eyebrow">ATENDIMENTO INTELIGENTE</div>'
        '<h1>Encontre o instrumento<br><em>que combina com você.</em></h1>'
        '<p>Informação precisa sobre catálogo, pedidos e políticas da loja.</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_quick_actions() -> None:
    """Render one-click prompts for the most useful demonstration scenarios."""
    st.markdown("<div class='section-label'>Experimente agora</div>", unsafe_allow_html=True)
    columns = st.columns(len(QUICK_ACTIONS))
    for column, (label, message) in zip(columns, QUICK_ACTIONS):
        with column:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state.pending_message = message


def _render_messages() -> None:
    """Render the current conversation and non-sensitive source references."""
    for message in st.session_state.messages:
        role = cast(str, message["role"])
        avatar = "🎵" if role == "assistant" else "🙂"
        with st.chat_message(role, avatar=avatar):
            st.markdown(cast(str, message["content"]))
            sources = message.get("sources", [])
            if isinstance(sources, list) and sources:
                with st.expander("Fontes consultadas", expanded=False):
                    for source in sources:
                        if isinstance(source, Mapping):
                            source_type = source.get("source_type", "source")
                            reference = source.get("reference", "")
                            st.caption(f"{source_type} · {reference}")


def _process_pending_message() -> None:
    """Send a chat-input or quick-action message to the backend."""
    typed_message = st.chat_input("Digite sua dúvida para a loja...")
    pending_message = st.session_state.pop("pending_message", None)
    message = typed_message or pending_message
    if not isinstance(message, str) or not message.strip():
        return
    _append_message("user", message.strip(), [])
    with st.chat_message("assistant", avatar="🎵"):
        with st.spinner("Consultando o catálogo e as políticas..."):
            try:
                response = _send_chat(message.strip())
                reply = str(response.get("reply", "Não recebi uma resposta válida."))
                sources = response.get("sources", [])
            except httpx.HTTPError:
                reply = "Não consegui conectar ao atendimento agora. Tente novamente em instantes."
                sources = []
            except (TypeError, ValueError):
                reply = "Recebi uma resposta inválida do atendimento. Tente novamente."
                sources = []
        st.markdown(reply)
    _append_message("assistant", reply, sources if isinstance(sources, list) else [])


def _send_chat(message: str) -> dict[str, object]:
    """Send one message and the optional order context to the FastAPI backend.

    Args:
        message (str): Customer message to submit.

    Returns:
        dict[str, object]: Backend response payload.

    Raises:
        httpx.HTTPError: If the backend cannot be reached or rejects the request.
        ValueError: If the backend returns a non-object JSON response.
    """
    payload: dict[str, object] = {"message": message}
    order_id = st.session_state.get("order_id", 0)
    if isinstance(order_id, int) and order_id > 0:
        payload["order_id"] = order_id
    for field in ("customer_email", "customer_phone"):
        value = st.session_state.get(field, "")
        if isinstance(value, str) and value.strip():
            payload[field] = value.strip()
    with httpx.Client(base_url=_backend_url(), timeout=30.0) as client:
        response = client.post("/chat", json=payload)
        response.raise_for_status()
        result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Backend response must be a JSON object")
    return cast(dict[str, object], result)


@st.cache_data(ttl=20, show_spinner=False)
def _backend_is_available() -> bool:
    """Check whether the FastAPI health endpoint is responding.

    Returns:
        bool: Whether the backend returned HTTP 200.
    """
    try:
        response = httpx.get(f"{_backend_url()}/health", timeout=3.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def _append_message(role: str, content: str, sources: object) -> None:
    """Append one message to the current Streamlit conversation.

    Args:
        role (str): Message role, either user or assistant.
        content (str): Renderable message content.
        sources (object): Optional backend source list.
    """
    st.session_state.messages.append(
        {"role": role, "content": content, "sources": sources}
    )


def _backend_url() -> str:
    """Return the configured backend URL without a trailing slash."""
    return os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


def _render_styles() -> None:
    """Inject the visual theme used by the demonstration interface."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');
        :root { --ink: #1d1b2a; --muted: #777486; --violet: #6c4ce8; --gold: #f3b63f; --paper: #fbfaff; }
        .stApp { background: radial-gradient(circle at 82% 0%, #eee8ff 0, #fbfaff 36%, #ffffff 72%); color: var(--ink); }
        [data-testid="stSidebar"] { background: #1d1b2a; border-right: 0; }
        [data-testid="stSidebar"] * { color: #f8f6ff !important; }
        [data-testid="stSidebar"] [data-testid="stTextInput"] input,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] input { background: #2a2739; border: 1px solid #48435b; }
        .brand-mark { display: flex; align-items: center; gap: 11px; color: #fff; letter-spacing: .13em; }
        .brand-mark span { color: var(--gold); font-size: 2.2rem; line-height: 1; }
        .brand-mark b, .brand-mark small { display: block; }
        .brand-mark b { font-size: .94rem; }
        .brand-mark small { color: var(--gold) !important; font-size: .58rem; letter-spacing: .25em; margin-top: 2px; }
        .sidebar-copy { color: #aca6bf !important; font-family: 'Playfair Display', serif; font-style: italic; margin-top: -8px; }
        .hero { padding: 2.7rem 0 1.4rem; }
        .eyebrow, .section-label { color: var(--violet); font-size: .72rem; font-weight: 700; letter-spacing: .19em; text-transform: uppercase; }
        .hero h1 { color: var(--ink); font-family: 'DM Sans', sans-serif; font-size: clamp(2.1rem, 5vw, 4.3rem); letter-spacing: -.06em; line-height: .98; margin: .5rem 0 1rem; }
        .hero h1 em { color: var(--violet); font-family: 'Playfair Display', serif; font-weight: 600; letter-spacing: -.04em; }
        .hero p { color: var(--muted); font-size: 1.04rem; margin: 0; }
        .section-label { margin: .7rem 0 .65rem; }
        .stButton > button { background: #fff; border: 1px solid #e7e2f3; border-radius: 13px; color: var(--ink); font-weight: 600; min-height: 3.1rem; box-shadow: 0 5px 18px rgba(49, 36, 93, .05); }
        .stButton > button:hover { border-color: var(--violet); color: var(--violet); }
        [data-testid="stChatMessage"] { border-radius: 18px; }
        [data-testid="stChatMessage"] p { font-size: 1rem; line-height: 1.58; }
        [data-testid="stChatInput"] { border-color: #d9d2ed; border-radius: 16px; box-shadow: 0 7px 24px rgba(49, 36, 93, .08); }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
