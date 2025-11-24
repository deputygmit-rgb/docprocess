"""Quick PostgreSQL Connection Test with Docker suggestions"""

import sys
from pathlib import Path
import shutil

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def check_postgres_installed():
    """Check if PostgreSQL is installed"""
    return shutil.which('psql') is not None

def suggest_docker_setup():
    """Suggest Docker as alternative"""
    docker_yml = '''version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    container_name: docgraph_postgres
    environment:
      POSTGRES_USER: docuser
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: document_processor
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:'''
    
    print("\n" + "=" * 70)
    print("DOCKER SETUP (Recommended if PostgreSQL not installed)")
    print("=" * 70)
    print("\n1. Install Docker Desktop: https://www.docker.com/products/docker-desktop")
    print("\n2. Save docker-compose.yml in Scripts folder:")
    print("\n" + docker_yml)
    print("\n\n3. Start PostgreSQL:")
    print("   docker-compose up -d")
    print("\n4. Check it's running:")
    print("   docker ps")
    print("\n5. Then run this test again")
    print("=" * 70)

def test_connection():
    """Test PostgreSQL connection"""
    from sqlalchemy import create_engine, text
    from app.core.config import get_settings
    
    settings = get_settings()
    
    print("\n" + "=" * 70)
    print("POSTGRESQL CONNECTION TEST")
    print("=" * 70)
    
    print("\n📋 Configuration:")
    print(f"   Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"   Database: {settings.DB_NAME}")
    print(f"   User: {settings.DB_USER}")
    
    # Check if PostgreSQL is installed
    if not check_postgres_installed():
        print("\n⚠️  PostgreSQL CLI (psql) not found on system")
        suggest_docker_setup()
        return False
    
    print("\n🔌 Connecting...")
    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Test query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            print(f"\n✓ Connected successfully!")
            print(f"   Version: {version.split(',')[0]}")
            print("\n✓ POSTGRESQL IS READY!")
            return True
            
    except ImportError as e:
        print(f"\n❌ Missing: {e}")
        print("\nFix with:")
        print("   pip install psycopg2-binary sqlalchemy")
        return False
        
    except Exception as e:
        error = str(e).lower()
        print(f"\n❌ Connection failed: {e}")
        
        if "could not translate" in error or "nodename" in error:
            print("\n   → Check DB_HOST in .env or config.py")
            print("   → For Docker: docker ps (verify container running)")
        elif "refused" in error:
            print(f"\n   → PostgreSQL not running on {settings.DB_HOST}:{settings.DB_PORT}")
            print("   → Start PostgreSQL or Docker container")
        elif "does not exist" in error and "role" in error:
            print(f"\n   → User '{settings.DB_USER}' doesn't exist")
            print("   → Create user or check credentials")
        elif "password" in error or "authentication" in error:
            print(f"\n   → Password incorrect for user '{settings.DB_USER}'")
            print("   → Check DB_PASSWORD in .env")
        elif "does not exist" in error and "database" in error:
            print(f"\n   → Database '{settings.DB_NAME}' doesn't exist")
            print("   → See setup guide below")
        
        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
