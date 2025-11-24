#!/usr/bin/env python3
"""
Setup PostgreSQL database locally for Document Processor
Creates database, user, and tests connection
"""

import subprocess
import sys
from pathlib import Path
import os

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def run_psql_command(command, user="postgres", database=None, password=None):
    """Execute a psql command"""
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    
    if not Path(psql_path).exists():
        print(f"❌ PostgreSQL not found at {psql_path}")
        return False, "PostgreSQL not installed"
    
    cmd = [psql_path, "-U", user]
    
    if database:
        cmd.extend(["-d", database])
    
    cmd.extend(["-c", command])
    
    try:
        if password:
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timeout"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("POSTGRESQL LOCAL SETUP")
    print("=" * 70)
    
    # Step 1: Check PostgreSQL is installed
    print("\n[1] Checking PostgreSQL installation...", end=" ", flush=True)
    psql_path = r"C:\Program Files\PostgreSQL\18\bin\psql.exe"
    if Path(psql_path).exists():
        print("✓")
    else:
        print("✗")
        print("\n❌ PostgreSQL not found!")
        print("   Download from: https://www.postgresql.org/download/windows/")
        return False
    
    # Step 2: Check PostgreSQL service is running
    print("[2] Checking PostgreSQL service...", end=" ", flush=True)
    try:
        result = subprocess.run(
            ["Get-Service", "-Name", "postgresql-x64-18"],
            capture_output=True,
            text=True,
            shell=True
        )
        if "Running" in result.stdout:
            print("✓")
        else:
            print("✗ (not running)")
            print("    Starting service...")
            subprocess.run(["net", "start", "postgresql-x64-18"], shell=True)
    except:
        pass
    
    # Step 3: Test connection
    print("[3] Testing connection to PostgreSQL...", end=" ", flush=True)
    success, output = run_psql_command("SELECT version();", user="postgres")
    if success:
        print("✓")
        version_line = output.split('\n')[0]
        print(f"    PostgreSQL: {version_line[:50]}...")
    else:
        print("✗")
        print(f"\n❌ Connection failed: {output}")
        print("\nYou may need to provide the postgres password interactively.")
        print("Try running manually:")
        print("  psql -U postgres")
        print("\nThen run SQL commands from POSTGRESQL_LOCAL_SETUP.md")
        return False
    
    # Step 4: Check if database exists
    print("[4] Checking for document_processor database...", end=" ", flush=True)
    success, output = run_psql_command(
        "SELECT datname FROM pg_database WHERE datname='document_processor';",
        user="postgres"
    )
    
    if "document_processor" in output:
        print("✓ (already exists)")
        db_exists = True
    else:
        print("✗ (creating)")
        db_exists = False
    
    # Step 5: Create database if needed
    if not db_exists:
        print("[5] Creating database...", end=" ", flush=True)
        success, output = run_psql_command(
            "CREATE DATABASE document_processor;",
            user="postgres"
        )
        if success:
            print("✓")
        else:
            print("✗")
            print(f"    Error: {output}")
            return False
    else:
        print("[5] Database already exists - skipping creation")
    
    # Step 6: Check if docuser exists
    print("[6] Checking for docuser...", end=" ", flush=True)
    success, output = run_psql_command(
        "SELECT usename FROM pg_user WHERE usename='docuser';",
        user="postgres"
    )
    
    if "docuser" in output:
        print("✓ (already exists)")
        user_exists = True
    else:
        print("✗ (creating)")
        user_exists = False
    
    # Step 7: Create user if needed
    if not user_exists:
        print("[7] Creating docuser...", end=" ", flush=True)
        success, output = run_psql_command(
            "CREATE USER docuser WITH PASSWORD 'secure_password_123';",
            user="postgres"
        )
        if success:
            print("✓")
        else:
            print("✗")
            print(f"    Error: {output}")
            return False
    else:
        print("[7] User already exists - skipping creation")
    
    # Step 8: Grant privileges
    print("[8] Granting privileges...", end=" ", flush=True)
    success, output = run_psql_command(
        "GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;",
        user="postgres"
    )
    if success:
        print("✓")
    else:
        print("⚠️  (may already have privileges)")
    
    # Step 9: Test with docuser
    print("[9] Testing connection with docuser...", end=" ", flush=True)
    success, output = run_psql_command(
        "SELECT NOW();",
        user="docuser",
        database="document_processor",
        password="secure_password_123"
    )
    if success:
        print("✓")
    else:
        print("✗")
        print(f"    Error: {output}")
        print("    You may need to set password interactively")
    
    # Step 10: Create .env file
    print("[10] Creating .env file...", end=" ", flush=True)
    env_path = Path(__file__).parent / ".env"
    env_content = """DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_123
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
"""
    try:
        env_path.write_text(env_content)
        print("✓")
    except Exception as e:
        print("✗")
        print(f"    Error: {e}")
        print("    Please create .env manually")
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ SETUP COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Test connection: python test_postgres_quick.py")
    print("2. Run application: python app/main.py")
    print("3. Access API: http://localhost:5000/docs")
    print("\nDatabase created:")
    print("  Host: localhost")
    print("  Port: 5432")
    print("  User: docuser")
    print("  Password: secure_password_123")
    print("  Database: document_processor")
    
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
        sys.exit(1)
