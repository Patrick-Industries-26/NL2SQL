import json

import streamlit as st
import mysql.connector
import ollama
import pandas as pd
import plotly.express as px
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime
import re
import os

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Jp^6",
    "database": "classicmodels",
}

MODEL_NAME = "sqlcoder-custom"

# --- HISTORY FILE PATH ---
HISTORY_FILE = "query_history.json"

# --- EXAMPLE QUESTIONS ---
EXAMPLE_QUESTIONS = [
    {"category": "Customers", "icon": "👥", "question": "List all customers from the USA"},
    {"category": "Customers", "icon": "👥", "question": "Which customers have a credit limit above 50000?"},
    {"category": "Customers", "icon": "👥", "question": "Show the top 10 customers by credit limit"},
    {"category": "Orders", "icon": "📦", "question": "How many orders were placed each month?"},
    {"category": "Orders", "icon": "📦", "question": "List all orders that are still in 'In Process' status"},
    {"category": "Orders", "icon": "📦", "question": "Show orders placed in 2003"},
    {"category": "Products", "icon": "🛒", "question": "Which products have less than 100 items in stock?"},
    {"category": "Products", "icon": "🛒", "question": "Show the top 5 most expensive products by MSRP"},
    {"category": "Products", "icon": "🛒", "question": "List all products in the Classic Cars product line"},
    {"category": "Employees", "icon": "🧑‍💼", "question": "Show all employees and their job titles"},
    {"category": "Employees", "icon": "🧑‍💼", "question": "Who are the sales representatives?"},
    {"category": "Analytics", "icon": "📊", "question": "How many customers in each country?"},
    {"category": "Analytics", "icon": "📊", "question": "List the average credit limit of customers for each country?"},
    {"category": "Analytics", "icon": "📊", "question": "Show the employee who make highest sale?"},
]

# --- PAGE CONFIG (must be first Streamlit call) ---
st.set_page_config(page_title="NL2SQL", layout="wide")

# --- THEME STATE INIT ---
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False


# ─────────────────────────────────────────────
# DYNAMIC CSS (Light / Dark)
# ─────────────────────────────────────────────
def inject_theme_css(dark: bool):
    if dark:
        bg = "#0f172a"
        surface = "#1e293b"
        surface2 = "#334155"
        text = "#e2e8f0"
        subtext = "#94a3b8"
        border = "#334155"
        accent = "#3b82f6"
        accent_hov = "#2563eb"
        metric_bg = "#1e293b"
        code_bg = "#0f172a"
        input_bg = "#1e293b"
        tab_active = "#3b82f6"
        expander_bg = "#1e293b"
        btn_ex_bg = "#334155"
        btn_ex_col = "#e2e8f0"
        shadow = "rgba(0,0,0,0.4)"
        btn_txt = "#64748b"
    else:
        bg = "#f8fafc"
        surface = "#ffffff"
        surface2 = "#f1f5f9"
        text = "#1e293b"
        subtext = "#64748b"
        border = "#e2e8f0"
        accent = "#2563eb"
        accent_hov = "#f2f8f0"
        metric_bg = "#f8fafc"
        code_bg = "#f1f5f9"
        input_bg = "#ffffff"
        tab_active = "#2563eb"
        expander_bg = "#f8fafc"
        btn_ex_bg = "#f1f5f9"
        btn_ex_col = "#1e293b"
        shadow = "rgba(0,0,0,0.06)"
        btn_txt = "#e2f8f0"

    st.markdown(f"""
    <style>
    /* ── Global ── */
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: {bg} !important;
        color: {text} !important;
    }}
    .stApp {{ background-color: {bg} !important; }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background-color: {surface} !important;
        border-right: 1px solid {border};
    }}
    section[data-testid="stSidebar"] * {{ color: {text} !important; }}

    /* ── Main area text ── */
    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6, p, label {{ color: {text} !important; }}

    /* ── Input box ── */
    .stTextInput > div > div > input {{
        background-color: {input_bg} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
    }}

    /* ── Primary Buttons ── */
    .stButton > button {{
        background-color: {btn_txt} !important;
        color: {btn_txt};
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.25s ease !important;
    }}
    .stButton > button:hover {{
        background-color: {accent_hov} !important;
        box-shadow: 0 4px 12px {shadow} !important;
    }}

    /* ── Example question buttons (secondary style) ── */
    .example-btn button {{
        background-color: {btn_ex_bg} !important;
        color: {btn_ex_col} !important;
        border: 1px solid {border} !important;
        font-weight: 400 !important;
        text-align: left !important;
    }}
    .example-btn button:hover {{
        border-color: {accent} !important;
        color: {accent} !important;
    }}

    /* ── Metric Cards ── */
    div[data-testid="metric-container"] {{
        background-color: {metric_bg} !important;
        border: 1px solid {border} !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 2px 8px {shadow} !important;
    }}
    div[data-testid="metric-container"] * {{ color: {text} !important; }}

    /* ── Code blocks ── */
    .stCode, pre, code {{
        background-color: {code_bg} !important;
        color: {text} !important;
        border-radius: 8px !important;
    }}

    /* ── Tabs ── */
    button[data-baseweb="tab"] {{
        color: {subtext} !important;
        font-weight: 500 !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {tab_active} !important;
        border-bottom: 2px solid {tab_active} !important;
    }}

    /* ── Expanders ── */
    details {{
        background-color: {expander_bg} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
    }}
    details summary {{ color: {text} !important; }}

    /* ── Dataframe ── */
    .stDataFrame {{
        background-color: {surface} !important;
        border-radius: 10px !important;
    }}

    /* ── History card ── */
    .history-card {{
        background-color: {surface} !important;
        border: 1px solid {border} !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px {shadow} !important;
    }}
    .history-card .ts {{ color: {subtext}; font-size: 0.8rem; }}
    .history-card .q  {{ color: {text}; font-weight: 600; margin: 4px 0; }}

    /* ── Theme toggle button (pill style) ── */
    div[data-testid="stHorizontalBlock"] .theme-toggle button {{
        background-color: {surface2} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.3rem 1rem !important;
    }}

    /* ── Alert / info boxes ── */
    .stAlert {{ background-color: {surface2} !important; border-radius: 8px !important; }}

    /* ── Progress bar ── */
    .stProgress > div > div {{ background-color: {accent} !important; }}

    /* ── Dialog / Modal ── */
    div[data-testid="stModal"] {{
        background-color: {surface} !important;
        color: {text} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


inject_theme_css(st.session_state['dark_mode'])


# --- QUERY HISTORY FUNCTIONS ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_to_history(question, sql):
    history = load_history()
    entry = {
        "question": question,
        "sql": sql,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if history and history[-1]["question"] == question:
        return
    history.append(entry)
    history = history[-50:]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        st.warning(f"Could not save history: {e}")


def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)


# --- MODULE 1: RAG ENGINE ---
class SchemaRAG:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="./models/all-MiniLM-L6-v2"
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="sql_schema",
            embedding_function=self.embed_fn
        )

    def index_schema(self, schema_list):
        if self.collection.count() > 0:
            existing_ids = self.collection.get()['ids']
            self.collection.delete(existing_ids)
        documents, metadatas, ids = [], [], []
        for i, table_def in enumerate(schema_list):
            table_name = table_def.split("TABLE")[1].split("(")[0].strip()
            documents.append(table_def)
            metadatas.append({"table_name": table_name})
            ids.append(f"table_{i}")
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return self.collection.count()

    def retrieve_relevant_tables(self, question, n_results=1, max_distance=1.2):
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=['distances', 'documents', 'metadatas']
        )
        final_ddl, retrieved_tables = [], []
        for i in range(len(results['documents'][0])):
            distance = results['distances'][0][i]
            table_name = results['metadatas'][0][i]['table_name']
            ddl = results['documents'][0][i]
            if distance < max_distance:
                final_ddl.append(ddl)
                retrieved_tables.append(table_name)
        return "\n".join(final_ddl), retrieved_tables


# --- MODULE 2: DATABASE HANDLER ---
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_all_table_schemas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    table_schemas, summary, row_counts = [], {}, {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SHOW CREATE TABLE {table_name}")
        create_statement = cursor.fetchone()[1]
        create_statement = re.sub(r' AUTO_INCREMENT=\d+', "", create_statement)
        create_statement = re.sub(r' NOT NULL', '', create_statement)
        create_statement = re.sub(r'DEFAULT NULL', '', create_statement)
        create_statement = re.sub(r' ENGINE=\w+', '', create_statement)
        create_statement = re.sub(r' DEFAULT CHARSET=\w+', '', create_statement)
        create_statement = re.sub(r' COLLATE=\w+', '', create_statement)
        create_statement = re.sub(r' COMMENT \'.*?\'', '', create_statement)
        # create_statement = re.sub(r' COMMENT=\'.*?\'', '', create_statement)
        table_schemas.append(create_statement)
        print(create_statement)
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        col_names = [f"{col[0]} ({col[1]})" for col in columns]
        summary[table_name] = col_names
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        row_counts[table_name] = count
    conn.close()
    return table_schemas, summary, row_counts


def sanitize_mysql(sql):
    sql = re.sub(r"\bILIKE\b", "LIKE", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bNULLS LAST\b", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bNULLS FIRST\b", "", sql, flags=re.IGNORECASE)
    if "to_char" in sql.lower():
        sql = re.sub(r"to_char\(([^,]+),\s*'YYYY-MM-DD'\)", r"DATE_FORMAT(\1, '%Y-%m-%d')", sql, flags=re.IGNORECASE)
    sql = re.sub(r"::text", "", sql)
    return sql.strip()


def run_query(sql):
    conn = get_db_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


# --- MODULE 3: LLM ORCHESTRATOR ---
def generate_sql(question, relevant_schema_str, error_msg=None, previous_sql=None):
    system_instruction = """
    ### ROLE
    You are a strictly MySQL-compliant SQL expert.

    ### CRITICAL RULES (MUST FOLLOW)
    1. **Dialect**: Use ONLY standard MySQL syntax.
    2. **Case Insensitivity**: NEVER use `ILIKE`. Use `LIKE` instead.
    3. **Quoting**: Use backticks (`) for table/column names if they are reserved words.
    4. **Dates**: Use `DATE_FORMAT` or `NOW()`.
    5. **Output**: Return ONLY the raw SQL code. No markdown, no explanation.
    """
    few_shot_examples = """
        ### EXAMPLES
        Q: Find customers whose names start with 'Al' (case insensitive).
        -- GOOD (MySQL): SELECT * FROM customers WHERE name LIKE 'Al%';

        Q: Show top 5 orders by date.
        -- GOOD (MySQL): SELECT * FROM orders ORDER BY order_date IS NULL, order_date LIMIT 5;

        Q: List the employees and their managers. 
        -- GOOD (MySQL): SELECT e.employeeNumber, e.firstName, e.lastName, e.reportsTo, m.firstName as ManagerFirstName, m.lastname as ManagerLastName FROM employees e JOIN employees m ON e.reportsTo = m.employeeNumber;
    """
    if error_msg:
        prompt = f"""
    {system_instruction}
    ### TASK: FIX THIS QUERY
    **Question:** {question}
    **Failed SQL:** {previous_sql}
    **MySQL Error:** {error_msg}
    **Corrected MySQL Query:**
    """
    else:
        prompt = f"""
    {system_instruction}
    {few_shot_examples}
    ### SCHEMA
    {relevant_schema_str}
    ### QUESTION
    {question}
    ### Important Column Rules
    - customers: customerNumber, customerName, contactLastName, contactFirstName, phone, addressLine1, addressLine2, city, state, postalCode, country, salesRepEmployeeNumber, creditLimit
    - employees: employeeNumber, lastName, firstName, extension, email, officeCode, reportsTo, jobTitle
    - products: productCode, productName, productLine, productScale, productVendor, productDescription, quantityInStock, buyPrice, MSRP
    - orders: orderNumber, orderDate, requiredDate, shippedDate, status, comments, customerNumber
    ### MYSQL QUERY
    """
    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options={
            'temperature': 0.0,
            'num_predict': 200,
            'stop': ["```", ";", "Q:"],
            'num_beams': 4,
            'do_sample': False,
        }
    )
    sql = response['response'].strip()
    sql = sql.replace("```sql", "").replace("```", "").replace(";", "")
    sql = sanitize_mysql(sql)
    return sql


# --- HELPER: CHART STYLING ---
def apply_modern_style(fig, title):
    dark = st.session_state.get('dark_mode', False)
    text_color = "#e2e8f0" if dark else "#1e293b"
    sub_color = "#94a3b8" if dark else "#64748b"
    grid_color = "#334155" if dark else "#f1f5f9"
    line_color = "#334155" if dark else "#e2e8f0"
    paper_bg = "rgba(0,0,0,0)"

    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color=text_color, family="Segoe UI, sans-serif"), x=0,
                   xanchor='left'),
        plot_bgcolor=paper_bg,
        paper_bgcolor=paper_bg,
        font=dict(color=sub_color),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=12)),
        margin=dict(l=20, r=20, t=60, b=80),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=line_color, tickfont=dict(color=sub_color))
    fig.update_yaxes(showgrid=True, gridcolor=grid_color, zeroline=False, tickfont=dict(color=sub_color))
    return fig


# ─────────────────────────────────────────────
# SAMPLE QUESTIONS DIALOG
# ─────────────────────────────────────────────
@st.dialog("✨ Example Questions", width="large")
def show_examples_modal():
    st.markdown("Select any question to load it into the query box and run it automatically.")
    st.markdown("")
    categories = {}
    for ex in EXAMPLE_QUESTIONS:
        categories.setdefault(ex["category"], []).append(ex)
    for cat, examples in categories.items():
        st.markdown(f"##### {examples[0]['icon']} {cat}")
        cols = st.columns(2)
        for j, ex in enumerate(examples):
            with cols[j % 2]:
                if st.button(ex["question"], key=f"ex_{cat}_{j}", use_container_width=True):
                    st.session_state['question_input'] = ex["question"]
                    st.session_state['auto_run'] = True
                    st.rerun()
        st.markdown("")


# ─────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────

# Initialize state
if 'rag_engine' not in st.session_state: st.session_state['rag_engine'] = SchemaRAG()
if 'prefill_question' not in st.session_state: st.session_state['prefill_question'] = ""
if 'last_results' not in st.session_state: st.session_state['last_results'] = None  # stores (sql, df, success, error)

# ── SIDEBAR ──
with st.sidebar:
    st.header("⚙️ Configuration")
    if st.button("🔄 Reload Schema"):
        with st.spinner("Indexing..."):
            schemas, summary, row_counts = get_all_table_schemas()
            st.session_state['schema_summary'] = summary
            st.session_state['table_row_counts'] = row_counts
            count = st.session_state['rag_engine'].index_schema(schemas)
        st.success(f"Indexed {count} tables.")

    st.markdown("---")
    st.header("📂 Database Schema")
    if st.session_state.get('schema_summary'):
        for table, cols in st.session_state['schema_summary'].items():
            row_count = st.session_state['table_row_counts'].get(table, 0)
            with st.expander(f"{table}"):
                st.info(f"Row count: {row_count}")
                st.write("**Columns:**")
                st.code("\n".join(cols))
    else:
        st.info("Click 'Reload Schema' to see tables.")

# ── HEADER ROW ──
header_col, toggle_col = st.columns([5, 1])
with header_col:
    st.title("NL2SQL — Natural Language to SQL")
with toggle_col:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    theme_label = "☀️ Light" if st.session_state['dark_mode'] else "🌙 Dark"
    if st.button(theme_label, key="theme_toggle"):
        st.session_state['dark_mode'] = not st.session_state['dark_mode']
        st.rerun()

st.markdown("---")

# ── INPUT ROW ──
default_question = st.session_state.get('prefill_question') or "List customers from USA?"
question = st.text_input("Ask a question about your database:", key="question_input", placeholder=default_question)

# Clear prefill after use
if st.session_state.get('prefill_question'):
    st.session_state['prefill_question'] = ""

btn_col1, btn_col2, _ = st.columns([1.6, 2, 6])
with btn_col1:
    run_clicked = st.button("▶ Generate & Run", use_container_width=True)
with btn_col2:
    if st.button("✨ Example Questions", use_container_width=True):
        show_examples_modal()

st.markdown("")

# ── QUERY EXECUTION ──
if run_clicked and question:
    with st.spinner("Finding relevant tables..."):
        rag = st.session_state['rag_engine']
        relevant_schema, table_names = rag.retrieve_relevant_tables(question, n_results=4)

    max_retries = 3
    current_sql = ""
    last_error = ""
    success = False
    df = None

    progress_bar = st.progress(0)
    status_text = st.empty()

    for attempt in range(max_retries):
        status_text.text(f"Attempt {attempt + 1}/{max_retries}...")
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
            progress_bar.progress(int((attempt + 1) / max_retries * 100))

    if success:
        save_to_history(question, current_sql)

    # Persist results in session state so they survive reruns
    st.session_state['last_results'] = {
        "question": question,
        "sql": current_sql,
        "df": df,
        "success": success,
        "error": last_error,
        "retries": max_retries,
    }

# ── RESULTS DISPLAY ──
res = st.session_state.get('last_results')
if res:
    st.subheader("🧾 Generated SQL")
    st.code(res['sql'], language="sql")

    if res['success']:
        df = res['df']
        st.markdown("### Query Results")

        if not df.empty:
            numeric_cols = df.select_dtypes(include=['number']).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            date_cols = df.select_dtypes(include=['datetime']).columns.tolist()

            if len(numeric_cols) > 0:
                cols = st.columns(3)
                main_metric = numeric_cols[0]
                cols[0].metric(label=f"Total {main_metric}", value=f"{df[main_metric].sum():,.0f}")
                cols[1].metric(label=f"Average {main_metric}", value=f"{df[main_metric].mean():,.2f}")
                cols[2].metric(label="Rows Returned", value=len(df))

            st.markdown("<br>", unsafe_allow_html=True)
            tab1, tab2, tab3, tab4 = st.tabs(["📄 Data Table", "📊 Bar Chart", "📈 Line Chart", "🥧 Pie Chart"])

            with tab1:
                st.dataframe(df, use_container_width=True)

            if len(numeric_cols) > 0 and (len(categorical_cols) > 0 or len(date_cols) > 0):
                x_axis = date_cols[0] if date_cols else categorical_cols[0]
                y_axis = numeric_cols[0]

                with tab2:
                    fig_bar = px.bar(df, x=x_axis, y=y_axis, color_discrete_sequence=['#2563eb'], text_auto='.2s')
                    fig_bar = apply_modern_style(fig_bar, f"{y_axis} by {x_axis}")
                    fig_bar.update_traces(marker_line_width=0, opacity=0.9)
                    st.plotly_chart(fig_bar, use_container_width=True)

                with tab3:
                    fig_line = px.area(df, x=x_axis, y=y_axis, line_shape='spline', markers=True,
                                       color_discrete_sequence=['#8b5cf6'])
                    fig_line = apply_modern_style(fig_line, f"Trend of {y_axis}")
                    fig_line.update_traces(fill="none")
                    st.plotly_chart(fig_line, use_container_width=True)

                with tab4:
                    fig_pie = px.pie(df, names=x_axis, values=y_axis, hole=0.5,
                                     color_discrete_sequence=px.colors.qualitative.Prism)
                    fig_pie = apply_modern_style(fig_pie, f"Distribution of {y_axis}")
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                msg = "⚠️ Visualization requires at least one numeric and one category column."
                for tab in [tab2, tab3, tab4]:
                    with tab:
                        st.warning(msg)
        else:
            st.info("Query executed successfully but returned 0 rows.")
    else:
        st.error(f"Failed after {res['retries']} attempts.")
        st.error(f"Last Error: {res['error']}")

# ─────────────────────────────────────────────
# QUERY HISTORY SECTION (main area, below results)
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Query History")

history = load_history()

if history:
    h_col1, h_col2 = st.columns([5, 1])
    with h_col1:
        st.caption(f"{len(history)} saved queries — newest first")
    with h_col2:
        if st.button("🗑️ Clear All", key="clear_history_main"):
            clear_history()
            st.rerun()

    # Show newest first — 3 per row
    reversed_history = list(reversed(history))
    for col_idx, entry in enumerate(reversed_history):
        real_idx = len(history) - 1 - col_idx
        # Card container
        st.markdown(
            f"""
                <div class="history-card">
                    <div class="ts">🕒 {entry['timestamp']}</div>
                    <div class="q">{entry['question']}</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
        # Expand SQL + re-run
        with st.expander("View SQL"):
            st.code(entry['sql'], language="sql")
        # if st.button("▶ Re-run", key=f"rerun_main_{real_idx}", use_container_width=True):
        #     st.session_state['prefill_question'] = entry['question']
        #     st.rerun()
else:
    st.info("No query history yet. Run a query above to start tracking.")
