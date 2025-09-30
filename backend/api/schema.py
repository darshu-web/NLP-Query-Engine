from fastapi import APIRouter
from services.schema_discovery import SchemaDiscovery
from pydantic import BaseModel

router = APIRouter()
sd = SchemaDiscovery()

class ConnectRequest(BaseModel):
    connection_string: str

@router.get("/schema/test")
async def test_schema():
    """
    Test endpoint to verify schema discovery is working
    """
    try:
        connection_string = "sqlite:///./demo_db.sqlite"
        print(f"🔍 Testing schema discovery with: {connection_string}")
        schema = sd.analyze_database(connection_string)
        print(f"✅ Test successful: {len(schema.get('tables', {}))} tables found")
        return {"ok": True, "schema": schema}
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e), "schema": None}

@router.post("/schema/database")
async def connect_database(payload: ConnectRequest):
    """
    Connect to database and return discovered schema JSON
    """
    try:
        print(f"🔍 Connecting to database: {payload.connection_string}")
        schema = sd.analyze_database(payload.connection_string)
        print(f"✅ Schema discovery successful: {len(schema.get('tables', {}))} tables found")
        return {"ok": True, "schema": schema}
    except Exception as e:
        print(f"❌ Schema discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e), "schema": None}
