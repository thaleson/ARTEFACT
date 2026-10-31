"""Trust indicators displayed above the conversation."""

import streamlit as st


def render_overview() -> None:
    """Render concise product capabilities without exposing implementation details."""
    st.markdown(
        """
        <div class="trust-grid">
          <div class="trust-card"><span class="trust-icon">⌕</span><div><b>Catálogo consultado</b><small>Preço e estoque em tempo real</small></div></div>
          <div class="trust-card"><span class="trust-icon">✦</span><div><b>Políticas com fonte</b><small>Respostas baseadas no manual</small></div></div>
          <div class="trust-card"><span class="trust-icon">⌁</span><div><b>Pedido protegido</b><small>Verificação antes de exibir dados</small></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
