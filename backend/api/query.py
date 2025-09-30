from fastapi import APIRouter
from pydantic import BaseModel
from services.query_engine import QueryEngine

router = APIRouter()
# For demo: default to sqlite connection file db.sqlite (but can pass connection string)
DEFAULT_DB = "sqlite:///./demo_db.sqlite"
qe = QueryEngine(DEFAULT_DB)

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
async def process_query(req: QueryRequest):
    result = qe.process_query(req.query)
    return result

@router.get("/query/history")
async def history():
    return qe.get_history()
