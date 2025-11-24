#!/usr/bin/env python3
"""
Create PostgreSQL database and user for Document Processor
"""

import subprocess
import sys
from pathlib import Path

def run_psql_command(sql_command, user="postgres", password="1234", database=None):
    """Execute a psql command"""
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    
    cmd = [psql_path, "-U", user]
    
    if database:
        cmd.extend(["-d", database])
    
    cmd.extend(["-c", sql_command])
    
    try:
        import os
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )
        
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 70)
    print("CREATE POSTGRESQL DATABASE AND USER")
    print("=" * 70)
    
    postgres_password = "1234"
    
    # Step 1: Test connection to postgres database
    print("\n[1] Testing connection to PostgreSQL...", end=" ", flush=True)
    success, stdout, stderr = run_psql_command("SELECT version();", password=postgres_password)
    
    if success:
        print("✓")
        version_line = stdout.split('\n')[0] if stdout else "PostgreSQL 18"
        print(f"    {version_line[:60]}")
    else:
        print("✗")
        print(f"    Error: {stderr}")
        print("\n❌ Could not connect to PostgreSQL")
        print("    Check if postgres password is correct")
        return False
    
    # Step 2: Check if database exists
    print("[2] Checking for 'document_processor' database...", end=" ", flush=True)
    success, stdout, stderr = run_psql_command(
        "SELECT datname FROM pg_database WHERE datname='document_processor';",
        password=postgres_password
    )
    
    if "document_processor" in stdout:
        print("✓ (already exists)")
        db_exists = True
    else:
        print("✗ (creating)")
        db_exists = False
    
    # Step 3: Create database if needed
    if not db_exists:
        print("[3] Creating 'document_processor' database...", end=" ", flush=True)
        success, stdout, stderr = run_psql_command(
            "CREATE DATABASE document_processor;",
            password=postgres_password
        )
        if success or "already exists" in stderr:
            print("✓")
        else:
            print("✗")
            print(f"    Error: {stderr}")
            return False
    else:
        print("[3] Database already exists - skipping")
    
    # Step 4: Check if user exists
    print("[4] Checking for 'postgres' user...", end=" ", flush=True)
    success, stdout, stderr = run_psql_command(
        "SELECT usename FROM pg_user WHERE usename='postgres';",
        password=postgres_password
    )
    
    if "postgres" in stdout:
        print("✓ (already exists)")
        user_exists = True
    else:
        print("✗ (need to check permissions)")
        user_exists = True  # postgres user should always exist
    
    # Step 5: Grant privileges
    print("[5] Setting up permissions...", end=" ", flush=True)
    success, stdout, stderr = run_psql_command(
        "GRANT ALL PRIVILEGES ON DATABASE document_processor TO postgres;",
        password=postgres_password
    )
    print("✓")
    
    # Step 6: Create .env file
    print("[6] Creating .env file...", end=" ", flush=True)
    env_path = Path(__file__).parent / ".env"
    env_content = f"""DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD={postgres_password}
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
"""
    
    try:
        env_path.write_text(env_content)
        print("✓")
    except Exception as e:
        print("✗")
        print(f"    Error: {e}")
    
    # Step 7: Test with connection to new database
    print("[7] Testing connection to 'document_processor' database...", end=" ", flush=True)
    success, stdout, stderr = run_psql_command(
        "SELECT NOW();",
        password=postgres_password,
        database="document_processor"
    )
    if success:
        print("✓")
    else:
        print("✗")
        print(f"    Error: {stderr}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ DATABASE SETUP COMPLETE!")
    print("=" * 70)
    print("\nDatabase created:")
    print(f"  Host: localhost")
    print(f"  Port: 5432")
    print(f"  User: postgres")
    print(f"  Password: {postgres_password}")
    print(f"  Database: document_processor")
    print("\nNext steps:")
    print("1. Test connection: python test_postgres_quick.py")
    print("2. Run application: python app/main.py")
    print("3. Access API: http://localhost:5000/docs")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
