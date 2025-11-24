#!/usr/bin/env python3
"""
Docker Setup Helper for PostgreSQL
Guides through Docker installation and PostgreSQL setup
"""

import subprocess
import sys
import os
from pathlib import Path

def run_cmd(cmd, description=""):
    """Run a command and return success status"""
    if description:
        print(f"\n{description}...", end=" ", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            if description:
                print("✓")
            return True, result.stdout.strip()
        else:
            if description:
                print("✗")
            return False, result.stderr.strip()
    except Exception as e:
        if description:
            print(f"✗ ({e})")
        return False, str(e)

def check_docker():
    """Check if Docker is installed"""
    success, output = run_cmd("docker --version", "Checking Docker installation")
    if success:
        print(f"   {output}")
        return True
    return False

def check_docker_compose():
    """Check if Docker Compose is installed"""
    success, output = run_cmd("docker-compose --version", "Checking Docker Compose")
    if success:
        print(f"   {output}")
        return True
    return False

def start_postgres():
    """Start PostgreSQL container"""
    scripts_dir = Path(__file__).parent
    
    print("\n" + "=" * 70)
    print("STARTING POSTGRESQL IN DOCKER")
    print("=" * 70)
    
    # Check if Docker is running
    success, _ = run_cmd("docker ps", "Checking Docker daemon")
    if not success:
        print("\n❌ Docker is not running!")
        print("\nStart Docker Desktop and try again.")
        return False
    
    print("   ✓ Docker is running")
    
    # Start containers
    os.chdir(scripts_dir)
    print(f"\nStarting containers in: {scripts_dir}")
    
    success, output = run_cmd("docker-compose up -d", "Starting PostgreSQL container")
    if success:
        print("   ✓ PostgreSQL started")
        print("\nContainer output:")
        print(output)
        return True
    else:
        print("   ✗ Failed to start PostgreSQL")
        print(f"\nError: {output}")
        return False

def show_setup_guide():
    """Show Docker setup guide"""
    print("\n" + "=" * 70)
    print("DOCKER SETUP GUIDE")
    print("=" * 70)
    
    print("""
1. INSTALL DOCKER DESKTOP
   - Windows/Mac: https://www.docker.com/products/docker-desktop
   - Download and run installer
   - Follow setup wizard (keep defaults)
   - Restart computer
   - Start Docker Desktop app

2. VERIFY INSTALLATION
   - Open PowerShell
   - Run: docker --version
   - Should show: Docker version 24.x.x

3. CONFIGURE POSTGRESQL
   - Edit .env file in Scripts folder:
   
     DB_HOST=localhost
     DB_PORT=5432
     DB_USER=docuser
     DB_PASSWORD=secure_password_123
     DB_NAME=document_processor
   
   - Save file

4. START POSTGRESQL
   - Run this script again or:
     docker-compose up -d
   
   - Check status:
     docker ps
   
   - Should show: docgraph_postgres (running)

5. VERIFY CONNECTION
   - Run: python test_postgres_quick.py
   
   - Should show: ✓ POSTGRESQL IS READY!

6. PGADMIN (Optional - GUI for database)
   - Open: http://localhost:5050
   - Email: admin@docgraph.local
   - Password: admin
   - Create connection to PostgreSQL

USEFUL COMMANDS
   docker ps                    # List running containers
   docker logs docgraph_postgres # View PostgreSQL logs
   docker-compose down          # Stop containers
   docker-compose logs -f       # Follow container logs
   docker exec -it docgraph_postgres psql -U docuser # Connect to database
""")

def main():
    """Main setup flow"""
    print("=" * 70)
    print("POSTGRESQL DOCKER SETUP")
    print("=" * 70)
    
    # Step 1: Check Docker installation
    if not check_docker():
        print("\n❌ Docker is not installed!")
        show_setup_guide()
        return False
    
    # Step 2: Check Docker Compose
    if not check_docker_compose():
        print("\n⚠️  Docker Compose not found separately (usually included with Docker Desktop)")
        # Try to continue anyway - newer Docker includes compose
    
    # Step 3: Start PostgreSQL
    if not start_postgres():
        return False
    
    # Step 4: Wait for PostgreSQL to be ready
    print("\nWaiting for PostgreSQL to be ready...", end=" ", flush=True)
    import time
    for i in range(30):  # 30 second timeout
        success, _ = run_cmd("docker exec docgraph_postgres pg_isready -U docuser", "")
        if success:
            print("✓")
            print("\n✓ PostgreSQL is ready!")
            break
        time.sleep(1)
        print(".", end="", flush=True)
    else:
        print("\n⚠️  PostgreSQL startup timeout (may still be starting)")
    
    # Step 5: Test connection
    print("\nTesting connection...")
    success = False
    try:
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from app.core.config import get_settings
        from sqlalchemy import create_engine, text
        
        settings = get_settings()
        
        try:
            engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"\n✓ Connected to PostgreSQL!")
                print(f"   {version.split(',')[0]}")
                success = True
        except Exception as e:
            print(f"\n⚠️  Connection test failed (PostgreSQL still starting): {e}")
            print("\nWait 10 seconds and run: python test_postgres_quick.py")
    except Exception as e:
        print(f"\n⚠️  Could not test connection: {e}")
    
    # Show next steps
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. Verify connection:
   python test_postgres_quick.py

2. Check container status:
   docker ps

3. View logs if needed:
   docker logs docgraph_postgres

4. Access pgAdmin (optional):
   http://localhost:5050

5. Start the application:
   python app/main.py

6. Stop PostgreSQL when done:
   docker-compose down

TROUBLESHOOTING
   
   Container won't start?
   → Check logs: docker logs docgraph_postgres
   → Rebuild: docker-compose up -d --build
   
   Port already in use?
   → Change DB_PORT in .env file (5432 → 5433)
   → Update docker-compose.yml ports
   
   Permission denied?
   → On Mac/Linux: sudo docker-compose up -d
   
   Database operations slow?
   → PostgreSQL may still be initializing
   → Wait 30 seconds and try again
""")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)
