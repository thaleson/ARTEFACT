"""Quick-action prompt components for the Streamlit client."""

import streamlit as st

from frontend.session import set_pending_message


QUICK_ACTIONS: tuple[tuple[str, str], ...] = (
    ("Catálogo até R$ 1.000", "Quais violões estão disponíveis por até R$ 1.000?"),
    ("Preço do Takamine", "Quanto custa o Takamine GD20?"),
    ("Política de devolução", "Me arrependi da compra online. Posso devolver?"),
    ("Promoções ativas", "Quais promoções estão ativas?"),
)


def render_quick_actions() -> None:
    """Render one-click prompts for common demonstration scenarios."""
    st.markdown(
        "<div class='section-label'>Experimente agora</div>",
        unsafe_allow_html=True,
    )
    columns = st.columns(len(QUICK_ACTIONS))
    for column, (label, message) in zip(columns, QUICK_ACTIONS):
        with column:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                set_pending_message(message)
