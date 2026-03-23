import sqlglot
from sqlglot import exp


class SQLValidator:
    def __init__(self, schema_summary):
        """
        schema_summary: Dict structure like {'users': ['id', 'name'], 'orders': ['id', 'date']}
        """
        self.valid_tables = set(schema_summary.keys())

        # Flatten all columns for easier lookup (ignoring table scope for simplicity)
        self.valid_columns = set()
        for cols in schema_summary.values():
            self.valid_columns.update([c.lower() for c in cols])

    def validate(self, sql):
        """
        Returns (is_valid: bool, error_message: str)
        """
        try:
            # 1. Parse the SQL using MySQL dialect
            # sqlglot.parse returns a list of expressions (statements)
            parsed_statements = sqlglot.parse(sql, read="mysql")
        except Exception as e:
            return False, f"Syntax Error: {str(e)}"

        # CHECK 1: SQL INJECTION & MULTIPLE STATEMENTS
        # If the list has > 1 item, it means there are multiple queries (e.g. "SELECT ...; DROP ...")
        if len(parsed_statements) != 1:
            return False, "Security Alert: Multiple SQL statements detected. Only single queries are allowed."

        statement = parsed_statements[0]

        # CHECK 2: ONLY SELECT QUERIES
        # We explicitly ban DROP, DELETE, INSERT, UPDATE, ALTER, etc.
        if not isinstance(statement, exp.Select):
            return False, "Security Alert: Only SELECT queries are allowed."

        # Double check for dangerous commands hidden in subqueries
        if statement.find(exp.Delete) or statement.find(exp.Update) or \
                statement.find(exp.Drop) or statement.find(exp.Insert):
            return False, "Security Alert: DML/DDL commands (DROP, DELETE, etc.) are forbidden."

        # CHECK 3: SCHEMA VALIDATION (Tables & Columns)

        # A. Validate Tables
        for table in statement.find_all(exp.Table):
            table_name = table.name
            if table_name not in self.valid_tables:
                return False, f"Hallucination Alert: Table '{table_name}' does not exist in the schema."

        # B. Validate Columns
        for col in statement.find_all(exp.Column):
            col_name = col.name.lower()

            # Skip wildcard (*) and numeric literals
            if col_name == "*" or col_name.isdigit():
                continue

            if col_name not in self.valid_columns:
                return False, f"Hallucination Alert: Column '{col_name}' does not exist in the schema."

        # CHECK 4: SQL Injection
        is_injected, inj_msg = self.detect_sql_injection(statement, sql)
        if is_injected:
            return False, inj_msg

        return True, "Valid SQL"

    @staticmethod
    def detect_sql_injection(statement, raw_sql: str):

        # 1. COMMENT BASED INJECTION
        dangerous_comment_patterns = ["--", "/*", "*/", "#"]
        if any(pattern in raw_sql for pattern in dangerous_comment_patterns):
            return True, "SQL Injection Alert: Comment-based injection detected."

        # 2. UNION BASED INJECTION
        if statement.find(exp.Union):
            return True, "SQL Injection Alert: UNION-based injection detected."

        # 3. TAUTOLOGY BASED (1=1 , 'a'='a')
        for condition in statement.find_all(exp.EQ):
            left = condition.left
            right = condition.right

            if isinstance(left, exp.Literal) and isinstance(right, exp.Literal):
                if left.this == right.this:
                    return True, "SQL Injection Alert: Tautology condition detected."

        # 4. OR TRUE CONDITION
        for or_node in statement.find_all(exp.Or):
            for eq in or_node.find_all(exp.EQ):
                l = eq.left
                r = eq.right

                if isinstance(l, exp.Literal) and isinstance(r, exp.Literal):
                    if l.this == r.this:
                        return True, "SQL Injection Alert: OR-based always TRUE condition."

        # 5. TIME BASED INJECTION
        dangerous_functions = ["sleep", "benchmark"]

        for func in statement.find_all(exp.Anonymous):
            if func.name.lower() in dangerous_functions:
                return True, f"SQL Injection Alert: Dangerous function '{func.name}' detected."

        # 6. INFORMATION SCHEMA ACCESS
        for table in statement.find_all(exp.Table):
            if table.name.lower() == "information_schema":
                return True, "SQL Injection Alert: Metadata access detected."

        return False, None
