"""Streamlit entry point for the Empório da Música demonstration client."""

import streamlit as st

from frontend.api_client import BackendClient
from frontend.session import initialize_session
from frontend.ui.chat import process_messages, render_messages
from frontend.ui.header import render_header
from frontend.ui.overview import render_overview
from frontend.ui.quick_actions import render_quick_actions
from frontend.ui.sidebar import render_sidebar
from frontend.ui.styles import render_styles


def main() -> None:
    """Compose the Streamlit presentation from isolated UI components."""
    st.set_page_config(
        page_title="Empório da Música | Atendimento",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    render_styles()
    initialize_session()
    client = BackendClient()
    render_sidebar(client)
    render_header()
    render_overview()
    render_quick_actions()
    process_messages(client)
    render_messages()


if __name__ == "__main__":
    main()
