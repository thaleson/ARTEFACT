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
        st.markdown(
            '<div class="sidebar-section-label">ATENDIMENTO</div>',
            unsafe_allow_html=True,
        )
        if client.health():
            st.success("Atendimento online", icon="✅")
        else:
            st.error("Atendimento indisponível", icon="⚠️")
        st.caption("Pronto para ajudar com catálogo, pedidos e políticas.")
        st.divider()
        st.markdown(
            '<div class="order-panel"><div class="order-kicker">PEDIDOS</div>'
            '<h3>Acompanhe sua entrega</h3>'
            '<p>Informe o número do pedido e <strong>uma</strong> forma de confirmação.</p>'
            '<div class="order-help">Depois, pergunte no chat:<br>'
            '<em>“Qual o status do meu pedido?”</em></div></div>',
            unsafe_allow_html=True,
        )
        st.text_input(
            "Número do pedido",
            placeholder="Ex.: 8",
            key="order_id_input",
        )
        st.text_input(
            "E-mail cadastrado",
            placeholder="cliente@email.com",
            key="customer_email",
        )
        st.markdown('<div class="order-or">ou</div>', unsafe_allow_html=True)
        st.text_input(
            "Telefone cadastrado",
            placeholder="(00) 00000-0000",
            key="customer_phone",
        )
        st.caption("Os dados são usados apenas para validar o pedido.")
        st.divider()
        st.caption("Proteção de dados ativa • Atendimento seguro")
