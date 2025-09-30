#!/usr/bin/env python3
"""
Start the FastAPI server with proper error handling
"""
import uvicorn
import sys
import os
from pathlib import Path

def check_database():
    """Check if database exists and has data"""
    db_path = Path("demo_db.sqlite")
    if not db_path.exists():
        print("❌ Database file not found. Creating it...")
        create_database()
    else:
        print("✅ Database file exists")

def create_database():
    """Create the demo database with sample data"""
    import sqlite3
    
    conn = sqlite3.connect("demo_db.sqlite")
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
    print("✅ Database created successfully!")

def start_server():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting FastAPI server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API docs will be available at: http://localhost:8000/docs")
        print("🔍 Health check: http://localhost:8000/health")
        print("\n" + "="*50)
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔧 NLP Query Engine - Backend Server")
    print("="*50)
    
    # Check database
    check_database()
    
    # Start server
    start_server()
