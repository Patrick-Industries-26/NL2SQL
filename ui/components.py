"""
ui/components.py
────────────────
Reusable Streamlit UI components (sidebar, results panel, history section,
example-questions dialog).  Each function renders exactly one logical
section of the page, keeping app.py thin and readable.
"""

import streamlit as st
import pandas as pd

from config.settings import EXAMPLE_QUESTIONS
from database.connector import get_all_table_schemas
from utils.history import clear_history, load_history
from ui.charts import build_bar_chart, build_line_chart, build_pie_chart


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Renders the schema browser and reload button in the sidebar."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        if st.button("🔄 Reload Schema"):
            with st.spinner("Indexing..."):
                schemas, summary, row_counts = get_all_table_schemas()
                st.session_state["schema_summary"] = summary
                st.session_state["table_row_counts"] = row_counts
                count = st.session_state["rag_engine"].index_schema(schemas)
            st.success(f"Indexed {count} tables.")

        st.markdown("---")
        st.header("📂 Database Schema")

        if st.session_state.get("schema_summary"):
            for table, cols in st.session_state["schema_summary"].items():
                row_count = st.session_state["table_row_counts"].get(table, 0)
                with st.expander(table):
                    st.info(f"Row count: {row_count}")
                    st.write("**Columns:**")
                    st.code("\n".join(cols))
        else:
            st.info("Click 'Reload Schema' to see tables.")


# ── Results ───────────────────────────────────────────────────────────────────

def render_results(res: dict) -> None:
    """Renders the generated SQL and query result visualisations."""
    st.subheader("🧾 Generated SQL")
    st.code(res["sql"], language="sql")

    if not res["success"]:
        st.error(f"Failed after {res['retries']} attempts.")
        st.error(f"Last Error: {res['error']}")
        return

    df: pd.DataFrame = res["df"]
    st.markdown("### Query Results")

    if df.empty:
        st.info("Query executed successfully but returned 0 rows.")
        return

    dark = st.session_state.get("dark_mode", False)
    numeric_cols = df.select_dtypes(include=["number"]).columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()

    # ── Metric cards ──
    if len(numeric_cols) > 0:
        m_col = numeric_cols[0]
        c1, c2, c3 = st.columns(3)
        c1.metric(label=f"Total {m_col}", value=f"{df[m_col].sum():,.0f}")
        c2.metric(label=f"Average {m_col}", value=f"{df[m_col].mean():,.2f}")
        c3.metric(label="Rows Returned", value=len(df))

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📄 Data Table", "📊 Bar Chart", "📈 Line Chart", "🥧 Pie Chart"]
    )

    with tab1:
        st.dataframe(df, use_container_width=True)

    can_visualise = len(numeric_cols) > 0 and (categorical_cols or date_cols)
    if can_visualise:
        x_axis = date_cols[0] if date_cols else categorical_cols[0]
        y_axis = numeric_cols[0]

        with tab2:
            st.plotly_chart(build_bar_chart(df, x_axis, y_axis, dark), use_container_width=True)
        with tab3:
            st.plotly_chart(build_line_chart(df, x_axis, y_axis, dark), use_container_width=True)
        with tab4:
            st.plotly_chart(build_pie_chart(df, x_axis, y_axis, dark), use_container_width=True)
    else:
        msg = "⚠️ Visualization requires at least one numeric and one category column."
        for tab in [tab2, tab3, tab4]:
            with tab:
                st.warning(msg)


# ── History ───────────────────────────────────────────────────────────────────

def render_history() -> None:
    """Renders the full query history section below the results."""
    st.markdown("---")
    st.subheader("📜 Query History")

    history = load_history()

    if not history:
        st.info("No query history yet. Run a query above to start tracking.")
        return

    h_col1, h_col2 = st.columns([5, 1])
    with h_col1:
        st.caption(f"{len(history)} saved queries — newest first")
    with h_col2:
        if st.button("🗑️ Clear All", key="clear_history_main"):
            clear_history()
            st.rerun()

    for col_idx, entry in enumerate(reversed(history)):
        st.markdown(
            f"""
            <div class="history-card">
                <div class="ts">🕒 {entry['timestamp']}</div>
                <div class="q">{entry['question']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("View SQL"):
            st.code(entry["sql"], language="sql")


# ── Example-questions dialog ──────────────────────────────────────────────────

@st.dialog("✨ Example Questions", width="large")
def show_examples_modal() -> None:
    """Modal dialog that lets users pick a pre-built example question."""
    st.markdown("Select any question to load it into the query box and run it automatically.")
    st.markdown("")

    categories: dict = {}
    for ex in EXAMPLE_QUESTIONS:
        categories.setdefault(ex["category"], []).append(ex)

    for cat, examples in categories.items():
        st.markdown(f"##### {examples[0]['icon']} {cat}")
        cols = st.columns(2)
        for j, ex in enumerate(examples):
            with cols[j % 2]:
                if st.button(ex["question"], key=f"ex_{cat}_{j}", use_container_width=True):
                    st.session_state["question_input"] = ex["question"]
                    st.session_state["auto_run"] = True
                    st.rerun()
        st.markdown("")
