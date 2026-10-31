"""Hero header component for the Streamlit client."""

import streamlit as st


def render_header() -> None:
    """Render the product title and customer-service value proposition."""
    st.markdown(
        '<section class="hero"><div class="eyebrow">ATENDIMENTO INTELIGENTE</div>'
        '<h1>Encontre o instrumento<br><em>que combina com você.</em></h1>'
        '<p>Informação precisa sobre catálogo, pedidos e políticas da loja.</p>'
        '</section>',
        unsafe_allow_html=True,
    )
