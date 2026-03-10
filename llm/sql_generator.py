"""
llm/sql_generator.py
────────────────────
Handles all interaction with the local Ollama LLM:
  • builds system instructions and few-shot examples
  • constructs the generation prompt (first-attempt & error-correction)
  • post-processes the raw model output into clean, runnable SQL
"""

import ollama

from config.settings import MODEL_NAME
from database.connector import sanitize_mysql

# ── Static prompt parts (defined once, reused on every call) ──────────────────

_SYSTEM_INSTRUCTION = """
### ROLE
You are a strictly MySQL-compliant SQL expert.

### CRITICAL RULES (MUST FOLLOW)
1. **Dialect**: Use ONLY standard MySQL syntax.
2. **Case Insensitivity**: NEVER use `ILIKE`. Use `LIKE` instead.
3. **Quoting**: Use backticks (`) for table/column names if they are reserved words.
4. **Dates**: Use `DATE_FORMAT` or `NOW()`.
5. **Output**: Return ONLY the raw SQL code. No markdown, no explanation.
"""

_FEW_SHOT_EXAMPLES = """
### EXAMPLES
Q: Find customers whose names start with 'Al' (case insensitive).
-- GOOD (MySQL): SELECT * FROM customers WHERE name LIKE 'Al%';

Q: Show top 5 orders by date.
-- GOOD (MySQL): SELECT * FROM orders ORDER BY order_date IS NULL, order_date LIMIT 5;

Q: Show the employee who make highest sale?
-- GOOD (MySQL): SELECT e.firstName, e.lastName, SUM(od.priceEach * od.quantityOrdered) AS total_sales FROM orders o JOIN orderdetails od ON o.orderNumber = od.orderNumber JOIN customers c ON o.customerNumber = c.customerNumber JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber GROUP BY e.firstName, e.lastName ORDER BY total_sales DESC LIMIT 1

Q: List the employees and their managers. 
-- GOOD (MySQL): SELECT e.employeeNumber, e.firstName, e.lastName, e.reportsTo, m.firstName as ManagerFirstName, m.lastname as ManagerLastName FROM employees e JOIN employees m ON e.reportsTo = m.employeeNumber;
"""

_COLUMN_RULES = """
### Important Column Rules
- customers : customerNumber, customerName, contactLastName, contactFirstName, phone,
              addressLine1, addressLine2, city, state, postalCode, country,
              salesRepEmployeeNumber, creditLimit
- employees  : employeeNumber, lastName, firstName, extension, email, officeCode,
              reportsTo, jobTitle
- products   : productCode, productName, productLine, productScale, productVendor,
              productDescription, quantityInStock, buyPrice, MSRP
- orders     : orderNumber, orderDate, requiredDate, shippedDate, status,
              comments, customerNumber
"""

_LLM_OPTIONS = {
    "temperature": 0.0,
    "num_predict": 200,
    "stop": ["```", ";", "Q:"],
    "num_beams": 4,
    "do_sample": False,
}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_sql(
    question: str,
    relevant_schema_str: str,
    error_msg: str | None = None,
    previous_sql: str | None = None,
) -> str:
    """
    Call the LLM to produce a MySQL SELECT statement.

    Parameters
    ----------
    question : str
        The natural-language question from the user.
    relevant_schema_str : str
        DDL context retrieved by the RAG engine.
    error_msg : str | None
        If provided, the LLM is asked to *fix* a previously failed query.
    previous_sql : str | None
        The failed SQL, required when *error_msg* is set.

    Returns
    -------
    str
        Clean, sanitized SQL ready to execute.
    """
    if error_msg:
        prompt = _build_fix_prompt(question, previous_sql or "", error_msg)
    else:
        prompt = _build_generate_prompt(question, relevant_schema_str)

    response = ollama.generate(
        model=MODEL_NAME,
        prompt=prompt,
        options=_LLM_OPTIONS,
    )

    raw_sql: str = response["response"].strip()
    return _post_process(raw_sql)


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_generate_prompt(question: str, schema: str) -> str:
    return f"""
{_SYSTEM_INSTRUCTION}
{_FEW_SHOT_EXAMPLES}
### SCHEMA
{schema}
### QUESTION
{question}
{_COLUMN_RULES}
### MYSQL QUERY
"""


def _build_fix_prompt(question: str, failed_sql: str, error: str) -> str:
    return f"""
{_SYSTEM_INSTRUCTION}
### TASK: FIX THIS QUERY
**Question:** {question}
**Failed SQL:** {failed_sql}
**MySQL Error:** {error}
**Corrected MySQL Query:**
"""


def _post_process(raw_sql: str) -> str:
    """Strip Markdown fences, trailing semicolons, and dialect issues."""
    sql = raw_sql.replace("```sql", "").replace("```", "").replace(";", "")
    return sanitize_mysql(sql)