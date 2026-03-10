"""
ui/charts.py
────────────
Chart-building helpers.  Each function takes a DataFrame and returns a
fully-styled Plotly figure.  No Streamlit calls here — only figure
construction, keeping it testable and reusable.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.theme import get_chart_colors


# ── Shared layout ─────────────────────────────────────────────────────────────

def apply_modern_style(fig: go.Figure, title: str, dark: bool) -> go.Figure:
    """Apply a consistent, theme-aware layout to any Plotly figure."""
    c = get_chart_colors(dark)

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color=c["text"], family="Segoe UI, sans-serif"),
            x=0, xanchor="left",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["subtext"]),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.2,
            xanchor="center", x=0.5, font=dict(size=12),
        ),
        margin=dict(l=20, r=20, t=60, b=80),
        hovermode="x unified",
    )
    fig.update_xaxes(
        showgrid=False, showline=True,
        linecolor=c["line"], tickfont=dict(color=c["subtext"]),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=c["grid"],
        zeroline=False, tickfont=dict(color=c["subtext"]),
    )
    return fig


# ── Chart builders ────────────────────────────────────────────────────────────

def build_bar_chart(df: pd.DataFrame, x: str, y: str, dark: bool) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=["#2563eb"], text_auto=".2s")
    fig.update_traces(marker_line_width=0, opacity=0.9)
    return apply_modern_style(fig, f"{y} by {x}", dark)


def build_line_chart(df: pd.DataFrame, x: str, y: str, dark: bool) -> go.Figure:
    fig = px.area(
        df, x=x, y=y,
        line_shape="spline", markers=True,
        color_discrete_sequence=["#8b5cf6"],
    )
    fig.update_traces(fill="none")
    return apply_modern_style(fig, f"Trend of {y}", dark)


def build_pie_chart(df: pd.DataFrame, names: str, values: str, dark: bool) -> go.Figure:
    fig = px.pie(
        df, names=names, values=values, hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Prism,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return apply_modern_style(fig, f"Distribution of {values}", dark)
