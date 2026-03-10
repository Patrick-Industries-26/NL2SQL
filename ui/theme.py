"""
ui/theme.py
───────────
Generates and injects the dynamic light / dark CSS theme into the
Streamlit app.  All colour tokens live here; no other module needs to
know about raw hex values.
"""

import streamlit as st


# ── Colour palettes ───────────────────────────────────────────────────────────

def _dark_palette() -> dict:
    return dict(
        bg="#0f172a", surface="#1e293b", surface2="#334155",
        text="#e2e8f0", subtext="#94a3b8", border="#334155",
        accent="#3b82f6", accent_hov="#2563eb",
        metric_bg="#1e293b", code_bg="#0f172a", input_bg="#1e293b",
        tab_active="#3b82f6", expander_bg="#1e293b",
        btn_ex_bg="#334155", btn_ex_col="#e2e8f0",
        shadow="rgba(0,0,0,0.4)", btn_txt="#64748b",
    )


def _light_palette() -> dict:
    return dict(
        bg="#f8fafc", surface="#ffffff", surface2="#f1f5f9",
        text="#1e293b", subtext="#64748b", border="#e2e8f0",
        accent="#2563eb", accent_hov="#f2f8f0",
        metric_bg="#f8fafc", code_bg="#f1f5f9", input_bg="#ffffff",
        tab_active="#2563eb", expander_bg="#f8fafc",
        btn_ex_bg="#f1f5f9", btn_ex_col="#1e293b",
        shadow="rgba(0,0,0,0.06)", btn_txt="#e2f8f0",
    )


# ── CSS template ──────────────────────────────────────────────────────────────

def _build_css(p: dict) -> str:
    return f"""
    <style>
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: {p['bg']} !important;
        color: {p['text']} !important;
    }}
    .stApp {{ background-color: {p['bg']} !important; }}

    section[data-testid="stSidebar"] {{
        background-color: {p['surface']} !important;
        border-right: 1px solid {p['border']};
    }}
    section[data-testid="stSidebar"] * {{ color: {p['text']} !important; }}

    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label {{
        color: {p['text']} !important;
    }}

    .stTextInput > div > div > input {{
        background-color: {p['input_bg']} !important;
        color: {p['text']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 8px !important;
    }}

    .stButton > button {{
        background-color: {p['btn_txt']} !important;
        color: {p['btn_txt']};
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.25s ease !important;
    }}
    .stButton > button:hover {{
        background-color: {p['accent_hov']} !important;
        box-shadow: 0 4px 12px {p['shadow']} !important;
    }}

    .example-btn button {{
        background-color: {p['btn_ex_bg']} !important;
        color: {p['btn_ex_col']} !important;
        border: 1px solid {p['border']} !important;
        font-weight: 400 !important;
        text-align: left !important;
    }}
    .example-btn button:hover {{
        border-color: {p['accent']} !important;
        color: {p['accent']} !important;
    }}

    div[data-testid="metric-container"] {{
        background-color: {p['metric_bg']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 2px 8px {p['shadow']} !important;
    }}
    div[data-testid="metric-container"] * {{ color: {p['text']} !important; }}

    .stCode, pre, code {{
        background-color: {p['code_bg']} !important;
        color: {p['text']} !important;
        border-radius: 8px !important;
    }}

    button[data-baseweb="tab"] {{
        color: {p['subtext']} !important;
        font-weight: 500 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {p['tab_active']} !important;
        border-bottom: 2px solid {p['tab_active']} !important;
    }}

    details {{
        background-color: {p['expander_bg']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
    }}
    details summary {{ color: {p['text']} !important; }}

    .stDataFrame {{
        background-color: {p['surface']} !important;
        border-radius: 10px !important;
    }}

    .history-card {{
        background-color: {p['surface']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px {p['shadow']} !important;
    }}
    .history-card .ts {{ color: {p['subtext']}; font-size: 0.8rem; }}
    .history-card .q  {{ color: {p['text']}; font-weight: 600; margin: 4px 0; }}

    div[data-testid="stHorizontalBlock"] .theme-toggle button {{
        background-color: {p['surface2']} !important;
        color: {p['text']} !important;
        border: 1px solid {p['border']} !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.3rem 1rem !important;
    }}

    .stAlert {{ background-color: {p['surface2']} !important; border-radius: 8px !important; }}
    .stProgress > div > div {{ background-color: {p['accent']} !important; }}

    div[data-testid="stModal"] {{
        background-color: {p['surface']} !important;
        color: {p['text']} !important;
    }}
    </style>
    """


# ── Public API ────────────────────────────────────────────────────────────────

def inject_theme_css(dark: bool) -> None:
    """Inject theme CSS into the current Streamlit page."""
    palette = _dark_palette() if dark else _light_palette()
    st.markdown(_build_css(palette), unsafe_allow_html=True)


def get_chart_colors(dark: bool) -> dict:
    """Return chart colour tokens for use in plotly figures."""
    if dark:
        return dict(
            text="#e2e8f0", subtext="#94a3b8",
            grid="#334155", line="#334155",
        )
    return dict(
        text="#1e293b", subtext="#64748b",
        grid="#f1f5f9", line="#e2e8f0",
    )
