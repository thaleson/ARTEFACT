"""Visual theme for the Streamlit demonstration interface."""

import streamlit as st


def render_styles() -> None:
    """Inject the visual theme used by the demonstration interface."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');
        :root { --ink: #1d1b2a; --muted: #777486; --violet: #6c4ce8; --gold: #f3b63f; --paper: #fbfaff; }
        .stApp { background: radial-gradient(circle at 82% 0%, #eee8ff 0, #fbfaff 36%, #ffffff 72%); color: var(--ink); }
        .main, .main * { color: var(--ink); }
        .main input, .main textarea, .main [data-baseweb="input"], .main [data-baseweb="textarea"] { background: #ffffff !important; color: var(--ink) !important; caret-color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
        .main input::placeholder, .main textarea::placeholder { color: var(--muted) !important; opacity: 1 !important; -webkit-text-fill-color: var(--muted) !important; }
        [data-testid="stSidebar"] { background: #1d1b2a; border-right: 0; }
        [data-testid="stSidebar"] * { color: #f8f6ff !important; }
        [data-testid="stSidebar"] [data-testid="stTextInput"] input,
        [data-testid="stSidebar"] [data-testid="stNumberInput"] input { background: #2a2739 !important; border: 1px solid #48435b; color: #f8f6ff !important; caret-color: #f8f6ff !important; -webkit-text-fill-color: #f8f6ff !important; }
        [data-testid="stSidebar"] input::placeholder { color: #aca6bf !important; opacity: 1 !important; -webkit-text-fill-color: #aca6bf !important; }
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
        .stButton > button { background: #fff; border: 1px solid #e7e2f3; border-radius: 13px; color: var(--ink) !important; font-weight: 600; min-height: 3.1rem; box-shadow: 0 5px 18px rgba(49, 36, 93, .05); -webkit-text-fill-color: var(--ink); }
        .stButton > button:hover { border-color: var(--violet); color: var(--violet) !important; -webkit-text-fill-color: var(--violet); }
        [data-testid="stChatMessage"] { background: rgba(255, 255, 255, .82); border: 1px solid #eeeaf8; border-radius: 18px; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"], [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * { color: var(--ink) !important; }
        [data-testid="stChatMessage"] p { color: var(--ink) !important; font-size: 1rem; line-height: 1.58; }
        [data-testid="stChatInput"] { background: #ffffff !important; border: 1px solid #d9d2ed; border-radius: 16px; box-shadow: 0 7px 24px rgba(49, 36, 93, .08); }
        [data-testid="stChatInput"] textarea { background: #ffffff !important; color: var(--ink) !important; caret-color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
        [data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; opacity: 1 !important; -webkit-text-fill-color: var(--muted) !important; }
        [data-testid="stSpinner"] * { color: var(--violet) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
