"""
config/settings.py
-------------------
Central place for all hard-coded constants and environment-level settings.
Nothing else in the project should hard-code these values.
"""

import os

# --- Offline mode (set before any HuggingFace imports ---
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# --- Database ---
DB_CONFIG: dict = {
    "host": "localhost",
    "user": "root",
    "password": "Jp^6",
    "database": "classicmodels",
}

# --- LLM ---
MODEL_NAME: str = "llama3.2:3b"

# --- RAG / Embeddings ---
EMBEDDING_MODEL_PATH: str = "./models/all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME: str = "sql_schema"
RAG_N_RESULTS: int = 4
RAG_MAX_DISTANCE: float = 1.2

# --- History ---
HISTORY_FILE: str = "./query_history.json"
HISTORY_MAX_ENTRIES: int = 50

# --- Query retry ---
MAX_RETRIES: int = 3

# ── Example questions ─────────────────────────────────────────────────────────
EXAMPLE_QUESTIONS: list[dict] = [
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
    {"category": "Employees", "icon": "🧑‍💼", "question": "List employees whose job title is Sales Rep?"},
    {"category": "Analytics", "icon": "📊", "question": "How many customers in each country?"},
    {"category": "Analytics", "icon": "📊", "question": "List the average credit limit of customers for each country?"},
    {"category": "Analytics", "icon": "📊", "question": "Show the employee who make highest sale?"},
    {"category": "Analytics", "icon": "📊", "question": "List customers who ordered in the Classic Cars product line?"},
]
