#!/usr/bin/env python3
"""
PostgreSQL Health Check
Simple script to verify PostgreSQL is running and accessible
"""

import subprocess
import sys
from pathlib import Path

def check_service():
    """Check if PostgreSQL service is running"""
    print("🔍 Checking PostgreSQL Service Status")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             "Get-Service postgresql-x64-18 | Select-Object Name, Status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "Running" in result.stdout:
            print("✅ PostgreSQL Service: RUNNING")
            return True
        else:
            print("❌ PostgreSQL Service: NOT RUNNING")
            print("\nTo start it, run:")
            print("  net start postgresql-x64-18")
            return False
    except Exception as e:
        print(f"⚠️  Could not check service: {e}")
        return False

def check_psql():
    """Check if psql command works"""
    print("\n🔍 Checking PostgreSQL Installation")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            [r"C:\Program Files\PostgreSQL\18\bin\psql.exe", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        version = result.stdout.strip()
        print(f"✅ PostgreSQL: {version}")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL not found: {e}")
        return False

def check_port():
    """Check if PostgreSQL is listening on port 5432"""
    print("\n🔍 Checking PostgreSQL Port")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if ":5432" in result.stdout:
            print("✅ PostgreSQL is listening on port 5432")
            return True
        else:
            print("⚠️  Port 5432 not found (PostgreSQL may not be listening)")
            return False
    except Exception as e:
        print(f"⚠️  Could not check port: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    print("POSTGRESQL HEALTH CHECK")
    print("=" * 50 + "\n")
    
    service_ok = check_service()
    psql_ok = check_psql()
    port_ok = check_port()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Service:     {'✅ OK' if service_ok else '❌ FAILED'}")
    print(f"Installation: {'✅ OK' if psql_ok else '❌ FAILED'}")
    print(f"Port:        {'✅ OK' if port_ok else '⚠️  CHECK'}")
    
    if service_ok and psql_ok:
        print("\n✅ PostgreSQL is running and ready!")
        print("\nNext steps:")
        print("1. Run: python setup_local_postgres.py")
        print("   (Needs postgres user password)")
        print("\n2. Or create .env and test:")
        print("   python test_postgres_quick.py")
        return 0
    else:
        print("\n❌ PostgreSQL has issues - see above for help")
        return 1

if __name__ == "__main__":
    sys.exit(main())
