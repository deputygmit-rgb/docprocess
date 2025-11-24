"""Test PostgreSQL connection and database setup."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import get_settings

def test_postgres_connection():
    """Test PostgreSQL connection and database status."""
    
    settings = get_settings()
    
    print("=" * 80)
    print("POSTGRESQL CONNECTION TEST")
    print("=" * 80)
    
    print("\n[DATABASE CONFIGURATION]")
    print(f"  Host: {settings.DB_HOST}")
    print(f"  Port: {settings.DB_PORT}")
    print(f"  User: {settings.DB_USER}")
    print(f"  Database: {settings.DB_NAME}")
    print(f"  URL: postgresql://[user]:[pass]@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    print("\n[CONNECTION TEST]")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("  ✓ Connection successful")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Verify DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
        print("  3. Create the database: createdb -U postgres document_processor")
        print("  4. Install driver: pip install psycopg2-binary")
        return False
    
    print("\n[DATABASE CHECK]")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"  ✓ Found {len(tables)} table(s):")
            for table in tables:
                print(f"    - {table}")
        else:
            print("  ⚠ No tables found (will be created on first run)")
            
        # Check if documents table exists
        if 'documents' in tables:
            print("  ✓ 'documents' table exists")
            
            # Check columns
            columns = [col['name'] for col in inspector.get_columns('documents')]
            print(f"  ✓ Table has {len(columns)} columns")
            
            # Count records
            with engine.connect() as connection:
                result = connection.execute(text("SELECT COUNT(*) FROM documents"))
                count = result.scalar()
                print(f"  ✓ Table contains {count} records")
        
    except Exception as e:
        print(f"  ✗ Database check failed: {e}")
        return False
    
    print("\n[DATABASE VERSION]")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  ✓ {version}")
    except Exception as e:
        print(f"  ✗ Could not get version: {e}")
    
    print("\n" + "=" * 80)
    print("✓ POSTGRESQL IS READY")
    print("=" * 80)
    print("\nYou can now start the application:")
    print("  python app/main.py")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_postgres_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
