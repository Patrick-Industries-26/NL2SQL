"""
app.py  ←  Entry point
──────────────────────
Thin orchestration layer.  All business logic lives in sub-packages;
this file is responsible only for:
  1. Streamlit page config & session-state initialization
  2. Rendering the top-level layout (header, input row, query execution)
  3. Delegating to UI components for sidebar, results, and history
"""

import streamlit as st

# ── Must be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(page_title="NL2SQL", layout="wide")

# ── Internal imports (after page config) ─────────────────────────────────────
from config.settings import MAX_RETRIES
from database.connector import run_query
from llm.sql_generator import generate_sql
from rag.schema_rag import SchemaRAG
from ui.components import render_sidebar, render_results, render_history, show_examples_modal
from ui.theme import inject_theme_css
from utils.history import save_to_history

# ── Session-state defaults ────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "rag_engine" not in st.session_state:
    st.session_state["rag_engine"] = SchemaRAG()
if "prefill_question" not in st.session_state:
    st.session_state["prefill_question"] = ""
if "last_results" not in st.session_state:
    st.session_state["last_results"] = None

# ── Theme injection ───────────────────────────────────────────────────────────
inject_theme_css(st.session_state["dark_mode"])

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar()

# ── Page header + theme toggle ────────────────────────────────────────────────
header_col, toggle_col = st.columns([5, 1])
with header_col:
    st.title("NL2SQL — Natural Language to SQL")
with toggle_col:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    theme_label = "☀️ Light" if st.session_state["dark_mode"] else "🌙 Dark"
    if st.button(theme_label, key="theme_toggle"):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

st.markdown("---")

# ── Question input ────────────────────────────────────────────────────────────
default_question = st.session_state.get("prefill_question") or "List customers from USA?"
question = st.text_input(
    "Ask a question about your database:",
    key="question_input",
    placeholder=default_question,
)

# Clear prefill after use
if st.session_state.get("prefill_question"):
    st.session_state["prefill_question"] = ""

btn_col1, btn_col2, _ = st.columns([1.6, 2, 6])
with btn_col1:
    run_clicked = st.button("▶ Generate & Run", use_container_width=True)
with btn_col2:
    if st.button("✨ Example Questions", use_container_width=True):
        show_examples_modal()

st.markdown("")

# ── Query execution ───────────────────────────────────────────────────────────
if run_clicked and question:
    with st.spinner("Finding relevant tables..."):
        rag: SchemaRAG = st.session_state["rag_engine"]
        relevant_schema, table_names = rag.retrieve_relevant_tables(question)

    current_sql = ""
    last_error = ""
    success = False
    df = None

    progress_bar = st.progress(0)
    status_text = st.empty()

    for attempt in range(MAX_RETRIES):
        status_text.text(f"Attempt {attempt + 1}/{MAX_RETRIES}...")

        if attempt == 0:
            current_sql = generate_sql(question, relevant_schema)
        else:
            st.warning(f"Attempt {attempt} failed. Auto-correcting...")
            current_sql = generate_sql(question, relevant_schema, last_error, current_sql)

        df, last_error = run_query(current_sql)

        if last_error is None:
            success = True
            progress_bar.progress(100)
            status_text.text("✅ Success!")
            break
        else:
            progress_bar.progress(int((attempt + 1) / MAX_RETRIES * 100))

    if success:
        try:
            save_to_history(question, current_sql)
        except RuntimeError as exc:
            st.warning(str(exc))

    st.session_state["last_results"] = {
        "question": question,
        "sql": current_sql,
        "df": df,
        "success": success,
        "error": last_error,
        "retries": MAX_RETRIES,
    }

# ── Results display ───────────────────────────────────────────────────────────
res = st.session_state.get("last_results")
if res:
    render_results(res)

# ── Query history ─────────────────────────────────────────────────────────────
render_history()