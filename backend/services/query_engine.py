from services.schema_discovery import SchemaDiscovery
from services.document_processor import DocumentProcessor
from sqlalchemy import create_engine, text
from functools import lru_cache
import re
import time
from typing import Dict, List, Tuple, Any

class QueryEngine:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.schema_discovery = SchemaDiscovery()
        # analyze at init (for demo). In real use re-run on connect
        try:
            self.schema = self.schema_discovery.analyze_database(connection_string)
        except Exception:
            # fallback empty schema
            self.schema = {"tables": {}}
        self.doc_processor = DocumentProcessor()
        self.engine = create_engine(connection_string, future=True)
        self.history = []

    # ---------- Text → SQL helpers ----------
    def _choose_table(self, user_query: str) -> str:
        """
        Choose the most relevant table based on fuzzy column keyword overlap.
        """
        if not self.schema or not self.schema.get("tables"):
            return None
        q = user_query.lower()
        best_table = None
        best_score = -1
        for table, meta in self.schema["tables"].items():
            cols = [c["name"].lower() for c in meta.get("columns", [])]
            score = 0
            # reward presence of key business terms
            for term in ("employee", "employees", "name", "department", "salary", "hire"):
                if term in q and any(term in c for c in cols):
                    score += 2
            # lexical overlap with column names
            for w in re.findall(r"[a-zA-Z_]+", q):
                if any(w in c for c in cols):
                    score += 1
            if score > best_score:
                best_score = score
                best_table = table
        return best_table

    def _select_columns(self, table: str, user_query: str) -> List[str]:
        """
        Pick a concise projection instead of SELECT *.
        """
        if not table:
            return []
        cols = [c["name"] for c in self.schema["tables"][table]["columns"]]
        q = user_query.lower()
        picks: List[str] = []
        # common intents
        name_like = [c for c in cols if re.search(r"name|full_?name|first|last", c, re.I)]
        dept_like = [c for c in cols if re.search(r"dept|department", c, re.I)]
        sal_like = [c for c in cols if re.search(r"salary|pay|comp", c, re.I)]
        date_like = [c for c in cols if re.search(r"hire|date", c, re.I)]

        if "name" in q and name_like:
            picks.extend(name_like[:1])
        if any(k in q for k in ("department", "dept")) and dept_like:
            picks.extend(dept_like[:1])
        if any(k in q for k in ("salary", "pay", "compensation")) and sal_like:
            picks.extend(sal_like[:1])
        if any(k in q for k in ("hire", "hired", "date")) and date_like:
            picks.extend(date_like[:1])

        # Always include a stable id if present
        id_like = [c for c in cols if c.lower() in ("id", f"{table}_id")]
        if id_like:
            picks = id_like[:1] + [c for c in picks if c not in id_like]

        # Fallback minimal set
        if not picks:
            picks = (id_like[:1] or []) + name_like[:1] or cols[:3]
        # Dedupe while preserving order
        seen = set()
        unique = []
        for c in picks:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique[:6]

    def _build_filters(self, table: str, user_query: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Build parameterized WHERE clauses from simple patterns.
        """
        clauses: List[str] = []
        params: Dict[str, Any] = {}
        if not table:
            return clauses, params
        cols = [c["name"] for c in self.schema["tables"][table]["columns"]]
        lower_cols = [c.lower() for c in cols]
        q = user_query.lower()

        # numeric comparison: over/under N
        m_over = re.search(r"\b(over|greater than|above)\s+([0-9][0-9,]*)", q)
        m_under = re.search(r"\b(under|less than|below)\s+([0-9][0-9,]*)", q)
        salary_col = None
        for c in lower_cols:
            if re.search(r"salary|pay|comp", c):
                salary_col = cols[lower_cols.index(c)]
                break
        if salary_col and (m_over or m_under):
            if m_over:
                val = int(m_over.group(2).replace(",", ""))
                clauses.append(f"{salary_col} > :salary_min")
                params["salary_min"] = val
            if m_under:
                val = int(m_under.group(2).replace(",", ""))
                clauses.append(f"{salary_col} < :salary_max")
                params["salary_max"] = val

        # department equality if mentioned
        dept_col = None
        for c in lower_cols:
            if re.search(r"dept|department", c):
                dept_col = cols[lower_cols.index(c)]
                break
        m_dept = re.search(r"\b(department|dept)\s+(of|=)?\s*([a-zA-Z]+)", q)
        if dept_col and m_dept:
            dept = m_dept.group(3).capitalize()
            clauses.append(f"{dept_col} = :dept")
            params["dept"] = dept

        # simple LIKE search for skills/roles
        skill_col = None
        for c in lower_cols:
            if c in ("skills", "skill", "notes", "bio", "description", "role"):
                skill_col = cols[lower_cols.index(c)]
                break
        m_skill = re.search(r"\b(python|java|sql|c\+\+|c#|golang|react|node)\b", q)
        if skill_col and m_skill:
            clauses.append(f"{skill_col} LIKE :skill")
            params["skill"] = f"%{m_skill.group(1)}%"

        return clauses, params

    def _build_sql(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        table = self._choose_table(user_query)
        if not table:
            return None, {}
        cols = self._select_columns(table, user_query)
        where, params = self._build_filters(table, user_query)
        select_list = ", ".join(cols) if cols else "*"
        sql = f"SELECT {select_list} FROM {table}"
        if where:
            sql += " WHERE " + " AND ".join(where)
        if "limit" not in user_query.lower():
            sql += " LIMIT 200"
        return sql, params

    def classify_query(self, q: str):
        qlow = q.lower()
        # very simple rules:
        doc_keywords = ["resume", "cv", "document", "find", "mention", "search"]
        sql_keywords = ["how many", "count", "avg", "sum", "top", "highest", "lowest", "list", "where", "select", "employees", "salary", "hired"]
        if any(k in qlow for k in doc_keywords) and not any(k in qlow for k in sql_keywords):
            return "doc"
        if any(k in qlow for k in sql_keywords):
            # ambiguous: often both
            if any(k in qlow for k in doc_keywords):
                return "hybrid"
            return "sql"
        # fallback: hybrid
        return "hybrid"

    @lru_cache(maxsize=512)
    def _cached_sql_no_params(self, sql_text: str):
        with self.engine.connect() as conn:
            r = conn.execute(text(sql_text))
            rows = [dict(row) for row in r.fetchall()]
            return rows

    def _execute_sql(self, sql_text: str, params: Dict[str, Any]):
        with self.engine.connect() as conn:
            r = conn.execute(text(sql_text), params)
            return [dict(row) for row in r.fetchall()]

    def process_query(self, user_query: str):
        start = time.time()
        qtype = self.classify_query(user_query)
        out = {"query": user_query, "type": qtype, "results": None, "docs": None, "metrics": {}}
        try:
            if qtype in ("sql", "hybrid"):
                sql_text, params = self._build_sql(user_query)
                if sql_text:
                    if params:
                        rows = self._execute_sql(sql_text, params)
                    else:
                        rows = self._cached_sql_no_params(sql_text)
                    out["results"] = rows
                else:
                    out["results"] = []
            if qtype in ("doc", "hybrid"):
                docs = self.doc_processor.search(user_query, top_k=6)
                out["docs"] = docs
            elapsed = time.time() - start
            out["metrics"]["time_seconds"] = round(elapsed, 3)
            out["metrics"]["cache_hit"] = False  # for MVP
            # history
            self.history.append({"q": user_query, "type": qtype, "time": elapsed})
            return out
        except Exception as e:
            return {"error": str(e)}

    def optimize_sql_query(self, sql: str) -> str:
        # minimal optimizations: add LIMIT if missing
        if "limit" not in sql.lower():
            sql = sql.strip() + " LIMIT 200"
        return sql

    def get_history(self):
        return self.history[-50:]
