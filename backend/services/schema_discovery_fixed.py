import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from typing import Dict, Any, List
import difflib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaDiscovery:
    def __init__(self):
        self.engine: Engine = None
        self.schema_snapshot = {}

    def analyze_database(self, connection_string: str) -> Dict[str, Any]:
        """
        Connects and produces JSON with tables, columns, FKs, sample rows.
        """
        try:
            logger.info(f"Connecting to database: {connection_string}")
            self.engine = create_engine(connection_string, future=True)
            inspector = inspect(self.engine)
            
            # Get all table names
            table_names = inspector.get_table_names()
            logger.info(f"Found {len(table_names)} tables: {table_names}")
            
            if not table_names:
                logger.warning("No tables found in database")
                return {"tables": {}, "error": "No tables found in database"}
            
            tables = {}
            for table_name in table_names:
                logger.info(f"Analyzing table: {table_name}")
                
                # Get columns
                cols = []
                try:
                    columns = inspector.get_columns(table_name)
                    for col in columns:
                        cols.append({
                            "name": col["name"], 
                            "type": str(col["type"]),
                            "nullable": col.get("nullable", True),
                            "default": col.get("default")
                        })
                    logger.info(f"Found {len(cols)} columns in {table_name}")
                except Exception as e:
                    logger.error(f"Error getting columns for {table_name}: {e}")
                    cols = []
                
                # Get foreign keys
                fks = []
                try:
                    fks = inspector.get_foreign_keys(table_name)
                    logger.info(f"Found {len(fks)} foreign keys in {table_name}")
                except Exception as e:
                    logger.error(f"Error getting foreign keys for {table_name}: {e}")
                    fks = []
                
                # Get sample data
                sample = []
                try:
                    with self.engine.connect() as conn:
                        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                        sample = [dict(row._mapping) for row in result.fetchall()]
                        logger.info(f"Retrieved {len(sample)} sample rows from {table_name}")
                except Exception as e:
                    logger.error(f"Error getting sample data from {table_name}: {e}")
                    sample = []
                
                tables[table_name] = {
                    "columns": cols, 
                    "foreign_keys": fks, 
                    "sample": sample
                }
            
            self.schema_snapshot = {"tables": tables}
            logger.info(f"Schema analysis complete. Found {len(tables)} tables")
            return self.schema_snapshot
            
        except Exception as e:
            logger.error(f"Error in analyze_database: {e}")
            import traceback
            traceback.print_exc()
            return {"tables": {}, "error": str(e)}

    def map_natural_language_to_schema(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Naive mapping: find candidate tables/columns by fuzzy match.
        """
        try:
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
        except Exception as e:
            logger.error(f"Error in map_natural_language_to_schema: {e}")
            return {"tables": [], "columns": []}
