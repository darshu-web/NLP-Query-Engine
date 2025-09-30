from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import ingestion, query, schema
import sqlite3
import os
from contextlib import asynccontextmanager

# Global database connection
db_connection = None

def init_database():
    """Initialize the demo database with sample data"""
    global db_connection
    
    # Create demo database if it doesn't exist
    db_path = "demo_db.sqlite"
    
    if not os.path.exists(db_path):
        print("Creating demo database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL,
            hire_date TEXT
        )
        ''')
        
        # Create departments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            manager_id INTEGER,
            budget REAL
        )
        ''')
        
        # Insert sample data
        employees = [
            (1, 'John Doe', 'Engineering', 75000, '2020-01-15'),
            (2, 'Jane Smith', 'Engineering', 80000, '2019-03-20'),
            (3, 'Bob Johnson', 'Marketing', 65000, '2021-06-10'),
            (4, 'Alice Brown', 'Engineering', 85000, '2018-11-05'),
            (5, 'Charlie Wilson', 'Sales', 70000, '2020-09-12')
        ]
        
        cursor.executemany('INSERT OR REPLACE INTO employees (id, name, department, salary, hire_date) VALUES (?, ?, ?, ?, ?)', employees)
        
        departments = [
            (1, 'Engineering', 1, 500000),
            (2, 'Marketing', 3, 200000),
            (3, 'Sales', 5, 300000)
        ]
        
        cursor.executemany('INSERT OR REPLACE INTO departments (id, name, manager_id, budget) VALUES (?, ?, ?, ?)', departments)
        
        conn.commit()
        conn.close()
        print("Demo database created successfully!")
    else:
        print("Demo database already exists")

def get_database_connection():
    """Get database connection"""
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("demo_db.sqlite")
    return db_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    init_database()
    yield
    # Shutdown
    print("Shutting down...")
    if db_connection:
        db_connection.close()

app = FastAPI(title="NLP Query Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(schema.router, prefix="/api", tags=["schema"])

@app.get("/")
async def root():
    return {"message": "NLP Query Engine API — healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint that also tests database connection"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        return {
            "status": "healthy",
            "database": "connected",
            "employees_count": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }