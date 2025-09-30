from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class TableSchema:
    """Represents a database table schema"""
    name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]]
    indexes: List[Dict[str, Any]]

@dataclass
class DatabaseSchema:
    """Represents the complete database schema"""
    tables: List[TableSchema]
    relationships: List[Dict[str, str]]
    metadata: Dict[str, Any]

@dataclass
class DocumentMetadata:
    """Metadata for uploaded documents"""
    id: str
    filename: str
    content_type: str
    size: int
    upload_time: datetime
    processing_status: str
    extracted_text: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None

@dataclass
class QueryResult:
    """Result from a database query"""
    query: str
    results: List[Dict[str, Any]]
    execution_time: float
    row_count: int
    columns: List[str]
    error: Optional[str] = None

@dataclass
class ConnectionInfo:
    """Database connection information"""
    connection_string: str
    database_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    is_connected: bool = False

# Export all models
__all__ = [
    'TableSchema',
    'DatabaseSchema', 
    'DocumentMetadata',
    'QueryResult',
    'ConnectionInfo'
]
