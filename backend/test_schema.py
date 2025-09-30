#!/usr/bin/env python3
"""
Test script to debug schema discovery issues
"""
import sqlite3
import sys
from services.schema_discovery import SchemaDiscovery

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        conn = sqlite3.connect("demo_db.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✅ Database connection successful")
        print(f"📋 Found tables: {[table[0] for table in tables]}")
        
        # Test each table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table_name}: {count} rows")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_schema_discovery():
    """Test the schema discovery service"""
    try:
        sd = SchemaDiscovery()
        connection_string = "sqlite:///./demo_db.sqlite"
        print(f"🔍 Testing schema discovery with: {connection_string}")
        
        schema = sd.analyze_database(connection_string)
        print(f"✅ Schema discovery successful")
        print(f"📋 Schema keys: {list(schema.keys())}")
        
        if "tables" in schema:
            print(f"📊 Tables found: {list(schema['tables'].keys())}")
            for table_name, table_info in schema["tables"].items():
                print(f"   📋 {table_name}:")
                print(f"      Columns: {[col['name'] for col in table_info['columns']]}")
                print(f"      Sample rows: {len(table_info.get('sample', []))}")
        
        return schema
    except Exception as e:
        print(f"❌ Schema discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_sample_data():
    """Create sample data if database is empty"""
    try:
        conn = sqlite3.connect("demo_db.sqlite")
        cursor = conn.cursor()
        
        # Check if tables exist and have data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("📝 Creating sample tables and data...")
            
            # Create employees table
            cursor.execute('''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL,
                hire_date TEXT
            )
            ''')
            
            # Create departments table
            cursor.execute('''
            CREATE TABLE departments (
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
            
            cursor.executemany('INSERT INTO employees (id, name, department, salary, hire_date) VALUES (?, ?, ?, ?, ?)', employees)
            
            departments = [
                (1, 'Engineering', 1, 500000),
                (2, 'Marketing', 3, 200000),
                (3, 'Sales', 5, 300000)
            ]
            
            cursor.executemany('INSERT INTO departments (id, name, manager_id, budget) VALUES (?, ?, ?, ?)', departments)
            
            conn.commit()
            print("✅ Sample data created successfully!")
        else:
            print("📋 Database already has tables")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Database Schema Discovery")
    print("=" * 50)
    
    # Step 1: Create sample data
    print("\n1️⃣ Creating sample data...")
    create_sample_data()
    
    # Step 2: Test database connection
    print("\n2️⃣ Testing database connection...")
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Step 3: Test schema discovery
    print("\n3️⃣ Testing schema discovery...")
    schema = test_schema_discovery()
    
    if schema:
        print("\n✅ All tests passed! Schema discovery is working.")
        print(f"📊 Final schema: {schema}")
    else:
        print("\n❌ Schema discovery failed. Check the error messages above.")
        sys.exit(1)

