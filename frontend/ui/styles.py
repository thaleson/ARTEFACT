"""Visual theme for the Streamlit demonstration interface."""

import streamlit as st


def render_styles() -> None:
    """Inject the visual theme used by the demonstration interface."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,600&display=swap');
        :root { --ink: #1d1b2a; --muted: #777486; --violet: #6c4ce8; --gold: #f3b63f; --paper: #fbfaff; }
        #MainMenu, footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { visibility: hidden; }
        [data-testid="stAppViewContainer"] .main .block-container { max-width: 1220px; padding-top: 1.3rem; padding-bottom: 2.2rem; }
        .stApp { background: radial-gradient(circle at 82% 0%, #eee8ff 0, #fbfaff 36%, #ffffff 72%); color: var(--ink); min-height: 100vh; }
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
        .hero { padding: 1.9rem 0 1.25rem; }
        .eyebrow, .section-label { color: var(--violet); font-size: .72rem; font-weight: 700; letter-spacing: .19em; text-transform: uppercase; }
        .hero h1 { color: var(--ink); font-family: 'DM Sans', sans-serif; font-size: clamp(2rem, 4.5vw, 3.7rem); letter-spacing: -.06em; line-height: .98; margin: .5rem 0 .8rem; }
        .hero h1 em { color: var(--violet); font-family: 'Playfair Display', serif; font-weight: 600; letter-spacing: -.04em; }
        .hero p { color: var(--muted); font-size: 1.04rem; margin: 0; }
        .trust-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: .4rem 0 1.45rem; }
        .trust-card { align-items: center; background: rgba(255, 255, 255, .72); border: 1px solid #ebe6f7; border-radius: 16px; display: flex; gap: 11px; min-height: 68px; padding: 13px 15px; }
        .trust-icon { align-items: center; background: #f0ebff; border-radius: 11px; color: var(--violet); display: flex; font-size: 1.25rem; height: 36px; justify-content: center; width: 36px; }
        .trust-card b, .trust-card small { display: block; }
        .trust-card b { color: var(--ink) !important; font-size: .83rem; }
        .trust-card small { color: var(--muted) !important; font-size: .71rem; margin-top: 3px; }
        .section-label { margin: .7rem 0 .65rem; }
        .stButton > button { background: #fff; border: 1px solid #e7e2f3; border-radius: 13px; color: var(--ink) !important; font-weight: 600; min-height: 3.1rem; box-shadow: 0 5px 18px rgba(49, 36, 93, .05); -webkit-text-fill-color: var(--ink); }
        .stButton > button:hover { border-color: var(--violet); color: var(--violet) !important; -webkit-text-fill-color: var(--violet); }
        .conversation-heading { align-items: end; border-bottom: 1px solid #ebe6f7; display: flex; justify-content: space-between; margin-top: 1.4rem; padding: 0 2px .8rem; }
        .conversation-heading span, .conversation-heading small { color: var(--violet) !important; display: block; font-size: .66rem; font-weight: 700; letter-spacing: .17em; text-transform: uppercase; }
        .conversation-heading b { color: var(--ink) !important; display: block; font-size: 1.08rem; margin-top: 3px; }
        .conversation-heading small { color: #26a269 !important; letter-spacing: .08em; }
        .chat-item { align-items: flex-start; display: flex; gap: 10px; margin: 13px 6px; }
        .chat-item.user { flex-direction: row-reverse; }
        .chat-avatar { align-items: center; background: #201d2e; border-radius: 11px; color: var(--gold) !important; display: flex; flex: 0 0 34px; font-size: 1.1rem; height: 34px; justify-content: center; margin-top: 2px; }
        .chat-item.user .chat-avatar { background: var(--violet); color: #ffffff !important; font-size: .7rem; }
        .chat-bubble { background: rgba(255, 255, 255, .94); border: 1px solid #e9e4f5; border-radius: 5px 17px 17px 17px; box-shadow: 0 6px 20px rgba(48, 34, 92, .04); max-width: 88%; padding: 12px 16px 14px; }
        .chat-item.user .chat-bubble { background: var(--violet); border: 0; border-radius: 17px 5px 17px 17px; }
        .chat-meta { align-items: center; display: flex; gap: 9px; margin-bottom: 6px; }
        .chat-meta b { color: var(--ink) !important; font-size: .72rem; }
        .chat-meta span { color: var(--muted) !important; font-size: .58rem; font-weight: 700; letter-spacing: .1em; }
        .chat-item.user .chat-meta b, .chat-item.user .chat-meta span { color: #eee9ff !important; }
        .chat-copy { color: var(--ink) !important; font-size: .94rem; line-height: 1.62; white-space: pre-wrap; }
        .chat-item.user .chat-copy { color: #ffffff !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255, 255, 255, .35); border-radius: 18px; }
        [data-testid="stChatInput"] { background: #ffffff !important; border: 1px solid #d9d2ed; border-radius: 16px; box-shadow: 0 7px 24px rgba(49, 36, 93, .08); }
        [data-testid="stChatInput"] textarea { background: #ffffff !important; color: var(--ink) !important; caret-color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; }
        [data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; opacity: 1 !important; -webkit-text-fill-color: var(--muted) !important; }
        [data-testid="stSpinner"] * { color: var(--violet) !important; }
        @media (max-width: 800px) { .trust-grid { grid-template-columns: 1fr; } .chat-bubble { max-width: 82%; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
