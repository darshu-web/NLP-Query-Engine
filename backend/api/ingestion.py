import uuid
import os
import tempfile
from fastapi import APIRouter, UploadFile, HTTPException
from typing import List
from services.document_processor import DocumentProcessor
from pydantic import BaseModel
import aiofiles
import csv
import re
import sqlite3

router = APIRouter()
processor = DocumentProcessor()

class UploadResponse(BaseModel):
    job_id: str
    files_processed: int

@router.post("/documents", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile]):
    """
    Accept multiple files, save them temporarily, and process synchronously (MVP).
    Returns a job ID that can be polled for status.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    job_id = str(uuid.uuid4())
    paths: List[str] = []

    # Save uploaded files to a temp directory
    for f in files:
        temp_dir = tempfile.gettempdir()
        out_path = os.path.join(temp_dir, f"{job_id}_{f.filename}")

        async with aiofiles.open(out_path, "wb") as wf:
            content = await f.read()
            await wf.write(content)

        paths.append(out_path)

    # Process documents synchronously for now
    processor.process_documents(paths, job_id=job_id)

    # Additionally, load any CSVs into the SQLite demo database for SQL querying
    for p in paths:
        if p.lower().endswith(".csv"):
            try:
                _load_csv_into_sqlite(p)
            except Exception as e:
                # Keep vector processing status independent of DB ingest
                pass

    # Refresh query engine schema snapshot if available (best-effort)
    try:
        # Lazy import to avoid circular router imports
        from api.query import qe, DEFAULT_DB  # type: ignore
        qe.schema = qe.schema_discovery.analyze_database(DEFAULT_DB)
    except Exception:
        pass

    return UploadResponse(job_id=job_id, files_processed=len(paths))

@router.get("/status/{job_id}")
async def status(job_id: str):
    """
    Get the processing status of a given job_id.
    """
    stat = processor.get_status(job_id)
    return {"job_id": job_id, "status": stat}


# -------------------- Helpers --------------------
def _sanitize_identifier(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower()).strip("_")
    return base or "col"


def _infer_types(sample_rows: List[List[str]]) -> List[str]:
    types: List[str] = []
    cols = len(sample_rows[0]) if sample_rows else 0
    for c in range(cols):
        col_values = [r[c] for r in sample_rows if c < len(r)]
        def is_int(v: str) -> bool:
            try:
                int(v)
                return True
            except Exception:
                return False
        def is_float(v: str) -> bool:
            try:
                float(v)
                # Exclude ints already handled
                return not is_int(v)
            except Exception:
                return False
        if col_values and all(is_int(v) for v in col_values if v != ""):
            types.append("INTEGER")
        elif col_values and all(is_float(v) for v in col_values if v != ""):
            types.append("REAL")
        else:
            types.append("TEXT")
    return types


def _load_csv_into_sqlite(csv_path: str):
    db_path = os.path.abspath("./project/backend/demo_db.sqlite")
    # If relative path above does not exist, fallback to local working dir file
    if not os.path.exists(db_path):
        db_path = os.path.abspath("./demo_db.sqlite")

    table_name = _sanitize_identifier(os.path.splitext(os.path.basename(csv_path))[0])
    with open(csv_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return
    headers = [_sanitize_identifier(h or f"col_{i}") for i, h in enumerate(rows[0])]
    # ensure unique column names
    seen = {}
    unique_headers = []
    for h in headers:
        if h not in seen:
            seen[h] = 0
            unique_headers.append(h)
        else:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")
    data_rows = rows[1:]
    sample = data_rows[:100]
    types = _infer_types(sample or [[""] * len(unique_headers)])

    cols_def = ", ".join([f"{col} {typ}" for col, typ in zip(unique_headers, types)])
    placeholders = ", ".join(["?" for _ in unique_headers])

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        cur.execute(f"CREATE TABLE {table_name} ({cols_def})")
        if data_rows:
            cur.executemany(
                f"INSERT INTO {table_name} ({', '.join(unique_headers)}) VALUES ({placeholders})",
                [row + [None] * (len(unique_headers) - len(row)) for row in data_rows]
            )
        conn.commit()
    finally:
        conn.close()
