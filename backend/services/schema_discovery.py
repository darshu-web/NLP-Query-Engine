import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from typing import Dict, Any, List
import difflib

class SchemaDiscovery:
    def __init__(self):
        self.engine: Engine = None
        self.schema_snapshot = {}

    def analyze_database(self, connection_string: str) -> Dict[str, Any]:
        """
        Connects and produces JSON with tables, columns, FKs, sample rows.
        """
        try:
            self.engine = create_engine(connection_string, future=True)
            inspector = inspect(self.engine)
            tables = {}
            
            table_names = inspector.get_table_names()
            if not table_names:
                return {"tables": {}, "error": "No tables found in database"}
            
            for table_name in table_names:
                cols = []
                for col in inspector.get_columns(table_name):
                    cols.append({"name": col["name"], "type": str(col["type"])})
                fks = inspector.get_foreign_keys(table_name)
                
                # sample rows
                sample = []
                with self.engine.connect() as conn:
                    try:
                        r = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                        sample = [dict(row._mapping) for row in r.fetchall()]
                    except Exception as e:
                        print(f"Error getting sample data from {table_name}: {e}")
                        sample = []
                
                tables[table_name] = {"columns": cols, "foreign_keys": fks, "sample": sample}
            
            self.schema_snapshot = {"tables": tables}
            return self.schema_snapshot
            
        except Exception as e:
            print(f"Error in analyze_database: {e}")
            return {"tables": {}, "error": str(e)}

    def map_natural_language_to_schema(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Naive mapping: find candidate tables/columns by fuzzy match.
        """
        words = [w.strip(",.()\"'").lower() for w in query.split()]
        candidates = {"tables": [], "columns": []}
        all_tables = list(schema.get("tables", {}).keys())
        all_cols = []
        for t, meta in schema.get("tables", {}).items():
            for c in meta["columns"]:
                all_cols.append((t, c["name"]))
        # table matches
        for w in words:
            tmatches = difflib.get_close_matches(w, all_tables, n=3, cutoff=0.6)
            for tm in tmatches:
                if tm not in candidates["tables"]:
                    candidates["tables"].append(tm)
        # column matches
        colnames = [c[1] for c in all_cols]
        for w in words:
            cmatches = difflib.get_close_matches(w, colnames, n=5, cutoff=0.6)
            for cm in cmatches:
                # find table(s) for this column
                for t, col in all_cols:
                    if col == cm and {"table": t, "column": col} not in candidates["columns"]:
                        candidates["columns"].append({"table": t, "column": col})
        return candidates
