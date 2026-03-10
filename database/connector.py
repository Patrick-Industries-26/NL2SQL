"""
database/connector.py
---------------------
Owns everything related to MySQL connectivity:
    - opening / closing connections
    - fetching table schemas & row counts
    - running arbitrary SELECT queries
    - sanitizing SQL to MySQL dialect
"""

import re

import mysql.connector
import pandas as pd

from config.settings import DB_CONFIG


# --- Connection ---
def get_db_connection():
    """Return a new MySQL connection using settings from config file."""
    return mysql.connector.connect(**DB_CONFIG)


# --- schema introspection ---
def get_all_table_schemas() -> tuple[list[str], dict, dict]:
    """
    Returns
    -------
    table_schemas : List[str]
        cleaned CREATE TABLE DDL strings (one per table).
    summary : dict
        { table_name: [col_name (type), ...] }
    row_counts: dict
        { table_name: int }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SHOW TABLES')
    tables = cursor.fetchall()

    table_schemas: list[str] = []
    summary: dict = {}
    row_counts: dict = {}

    for (table_name,) in tables:
        # Cleaned DDL
        cursor.execute(f"SHOW CREATE TABLE {table_name}")
        create_stmt = cursor.fetchone()[1]
        create_stmt = _clean_ddl(create_stmt)
        table_schemas.append(create_stmt)

        # Column summary
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        summary[table_name] = [f"{col[0]} ({col[1]})" for col in columns]

        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_counts[table_name] = cursor.fetchone()[0]

    conn.close()
    return table_schemas, summary, row_counts


def _clean_ddl(sql: str) -> str:
    """Strip noisy MySQL DDL clauses that add no semantic value for the LLM."""
    patterns = [
        r" AUTO_INCREMENT=\d+",
        r" NOT NULL",
        r"DEFAULT NULL",
        r" ENGINE=\w+",
        r" DEFAULT CHARSET=\w+",
        r" COLLATE=\w+",
        r" COMMENT \'.*?\'",
        r" COMMENT=\'.*?\'",
    ]
    for pattern in patterns:
        sql = re.sub(pattern, "", sql)
    return sql


# --- SQL sanitization ---
def sanitize_mysql(sql: str) -> str:
    """
    Translate common PostgresSQL / generic-SQL idioms into MySQL equivalents
    so that LLM-generated queries run without modification.
    """
    sql = re.sub(r"\bILIKE\b", "LIKE", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bNULLS LAST\b", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bNULLS FIRST\b", "", sql, flags=re.IGNORECASE)
    if "to_char" in sql.lower():
        sql = re.sub(
            r"to_char\(([^,]+),\s*'YYYY-MM-DD'\)",
            r"DATE_FORMAT(\1, '%Y-%m-%d')",
            sql,
            flags=re.IGNORECASE,
        )
    sql = re.sub(r"::text", "", sql)
    return sql.strip()

# --- Query Execution ---
def run_query(sql: str) -> tuple[pd.DataFrame | None, str | None]:
    """
    Execute *sql* and return (DataFrame, None) on success,
    or (None, error_message) on failure.
    """
    conn = get_db_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df, None
    except Exception as exc:
        return None, str(exc)
    finally:
        conn.close()
