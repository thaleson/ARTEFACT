"""Sidebar component for backend status and order context."""

import streamlit as st

from frontend.api_client import BackendClient


def render_sidebar(client: BackendClient) -> None:
    """Render brand, backend status, and optional order-verification fields.

    Args:
        client (BackendClient): Backend client used for health status.
    """
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
        if client.health():
            st.success("Backend conectado", icon="✅")
        else:
            st.error("Backend indisponível", icon="⚠️")
        st.caption(f"API: {client.settings.backend_url}")
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
