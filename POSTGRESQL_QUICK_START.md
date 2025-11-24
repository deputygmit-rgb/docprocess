# PostgreSQL Setup Guide

## Quick Start (Choose One Option)

### Option A: Docker (Recommended - Easiest)
```bash
# 1. Install Docker Desktop (if not already installed)
# Download: https://www.docker.com/products/docker-desktop

# 2. Run setup script
python setup_docker_postgres.py

# 3. Verify connection
python test_postgres_quick.py

# Should show: ✓ POSTGRESQL IS READY!
```

### Option B: Local PostgreSQL Installation
```bash
# See: POSTGRESQL_SETUP_WINDOWS.md for detailed instructions

# Quick steps:
# 1. Download installer: https://www.postgresql.org/download/windows/
# 2. Install PostgreSQL (keep defaults)
# 3. Create database and user (SQL commands in setup guide)
# 4. Update .env file
# 5. Run: python test_postgres_quick.py
```

### Option C: WSL2 (Windows Subsystem for Linux)
```bash
# Only if you have WSL2 installed
wsl
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
# Then follow local setup instructions
```

---

## Understanding the Setup

### What Changed?

**Before (SQLite):**
```
App → SQLite (documents.db) - File on disk
```

**After (PostgreSQL):**
```
App → PostgreSQL - Full database server
        ↓
      Network Connection
        ↓
   PostgreSQL Server (local or Docker)
```

### Configuration

All settings are read from `.env` file:

```env
# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password
DB_NAME=document_processor
```

These map to PostgreSQL connection string:
```
postgresql://docuser:secure_password@localhost:5432/document_processor
```

---

## File Structure

```
Scripts/
├── .env                          # ← Configuration (create this!)
├── app/
│   ├── core/
│   │   ├── config.py            # ← Reads from .env
│   │   └── database.py          # ← Creates DB connection
│   └── models/
│       └── document.py          # ← Database schema
├── docker-compose.yml           # ← Docker PostgreSQL setup
├── setup_docker_postgres.py     # ← Automated Docker setup
├── test_postgres_quick.py       # ← Test connection
└── POSTGRESQL_SETUP_WINDOWS.md # ← Detailed local setup
```

---

## Step-by-Step Setup

### Step 1: Choose Installation Method

**Docker (Recommended):**
- ✓ Easiest to set up
- ✓ No conflicts with system PostgreSQL
- ✓ Easy to remove (delete container)
- ✓ Works on Windows, Mac, Linux
- ✗ Requires Docker Desktop

**Local PostgreSQL:**
- ✓ No Docker dependency
- ✓ Direct system access
- ✗ More installation steps
- ✗ Possible port conflicts
- ✗ System-dependent

### Step 2: Create .env File

Create file `Scripts/.env`:

```env
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=my_secure_password_123
DB_NAME=document_processor

# Other config (copy from .env.example if exists)
OPENROUTER_API_KEY=your_key_here
```

### Step 3: Start PostgreSQL

**If using Docker:**
```bash
# Run setup script (recommended)
python setup_docker_postgres.py

# OR manually
docker-compose up -d
```

**If using Local PostgreSQL:**
```bash
# Windows: Start from Services or
net start postgresql-x64-16

# Mac
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
```

### Step 4: Verify Connection

```bash
python test_postgres_quick.py
```

Expected output:
```
📋 Configuration:
   Host: localhost:5432
   Database: document_processor
   User: docuser

🔌 Connecting...

✓ Connected successfully!
   Version: PostgreSQL 16.1

✓ POSTGRESQL IS READY!
```

### Step 5: Run Application

```bash
python app/main.py
```

Application will:
- Connect to PostgreSQL
- Create tables automatically
- Be ready for document uploads

---

## Docker Commands

### Start PostgreSQL
```bash
docker-compose up -d
```

### Check if running
```bash
docker ps
```

### View logs
```bash
docker logs docgraph_postgres

# Or follow logs
docker logs -f docgraph_postgres
```

### Stop PostgreSQL
```bash
docker-compose down
```

### Stop and remove data
```bash
docker-compose down -v
```

### Connect to database
```bash
docker exec -it docgraph_postgres psql -U docuser -d document_processor
```

### Restart PostgreSQL
```bash
docker-compose restart
```

---

## Database Connection URLs

### PostgreSQL (Docker/Local)
```
postgresql://docuser:password@localhost:5432/document_processor
```

### With special characters in password
```
postgresql://docuser:pass%40word@localhost:5432/document_processor
# Note: @ becomes %40
```

### Different host
```
postgresql://docuser:password@192.168.1.100:5432/document_processor
```

---

## Troubleshooting

### Issue: "Connection refused"

**Docker:**
```bash
# Check if container is running
docker ps

# If not running, start it
docker-compose up -d

# Check logs
docker logs docgraph_postgres
```

**Local PostgreSQL:**
```bash
# Check if service is running
# Windows Services → look for "PostgreSQL"
# Or: psql -U postgres
```

### Issue: "Password authentication failed"

```bash
# 1. Check password in .env matches setup
# 2. If Docker, restart container
docker-compose down
docker-compose up -d

# 3. If local, reset password in psql
psql -U postgres
ALTER USER docuser WITH PASSWORD 'new_password';
\q
```

### Issue: "Database does not exist"

```bash
# Docker: Create database
docker exec -it docgraph_postgres psql -U postgres
CREATE DATABASE document_processor OWNER docuser;
\q

# Local: Create database
psql -U postgres
CREATE DATABASE document_processor;
```

### Issue: "Port 5432 already in use"

```bash
# Docker: Change port in docker-compose.yml
# ports:
#   - "5433:5432"  # Use 5433 instead

# Then update .env
DB_PORT=5433

# Local: Change port in PostgreSQL.conf
# (Windows) C:\Program Files\PostgreSQL\16\data\postgresql.conf
# Change: port = 5432 → port = 5433
```

### Issue: "Module psycopg2 not found"

```bash
pip install psycopg2-binary sqlalchemy
```

### Issue: Docker daemon not running

```bash
# Start Docker Desktop app
# Or on Linux:
sudo systemctl start docker
```

---

## Accessing PostgreSQL Directly

### With Docker

```bash
# Connect to PostgreSQL inside container
docker exec -it docgraph_postgres psql -U docuser -d document_processor

# List tables
\dt

# Query documents
SELECT id, filename, status FROM documents LIMIT 10;

# Exit
\q
```

### With pgAdmin (Web GUI)

```bash
# Access at: http://localhost:5050
# Email: admin@docgraph.local
# Password: admin

# 1. Add new server
# 2. Host: postgres
# 3. Username: docuser
# 4. Password: (from .env)
# 5. Database: document_processor
```

### With Local PostgreSQL

```bash
# Direct connection
psql -U docuser -d document_processor -h localhost

# Or with password prompt
psql -U docuser -d document_processor -h localhost -W
```

---

## Data Persistence

### Docker

Data is stored in Docker volume `postgres_data`:
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect scripts_postgres_data

# Backup data
docker run --rm -v scripts_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Local PostgreSQL

Data is stored in PostgreSQL data directory:
- **Windows**: `C:\Program Files\PostgreSQL\16\data`
- **Mac**: `/usr/local/var/postgres`
- **Linux**: `/var/lib/postgresql/16/main`

---

## Backup & Restore

### Backup (Docker)

```bash
docker exec docgraph_postgres pg_dump -U docuser document_processor > backup.sql
```

### Restore (Docker)

```bash
docker exec -i docgraph_postgres psql -U docuser document_processor < backup.sql
```

### Backup (Local)

```bash
pg_dump -U docuser document_processor > backup.sql
```

### Restore (Local)

```bash
psql -U docuser document_processor < backup.sql
```

---

## Performance Tips

### Docker

```bash
# Increase memory allocation
# Docker Desktop → Settings → Resources → Memory: 4GB or more

# Check performance
docker stats docgraph_postgres
```

### Local PostgreSQL

```bash
# Edit postgresql.conf
# (Windows) C:\Program Files\PostgreSQL\16\data\postgresql.conf

# Increase settings:
shared_buffers = 256MB        # Usually 25% of RAM
effective_cache_size = 1GB    # Usually 50-75% of RAM
maintenance_work_mem = 64MB
work_mem = 16MB
```

---

## Environment Variables

### Required
- `DB_HOST` - PostgreSQL server address
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_USER` - Database user
- `DB_PASSWORD` - User password
- `DB_NAME` - Database name

### Optional (with defaults)
```env
OPENROUTER_API_KEY=           # For vision API
LANGFUSE_PUBLIC_KEY=          # For tracing
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## Next Steps

1. ✓ Database is running
2. ✓ Connection verified
3. → Run application: `python app/main.py`
4. → Test endpoints: http://localhost:5000/docs
5. → Upload documents and test

---

## Support

If you encounter issues:

1. **Docker not starting**
   - Check Docker Desktop is running
   - Review logs: `docker logs docgraph_postgres`

2. **Connection errors**
   - Verify .env file is correct
   - Run: `python test_postgres_quick.py`
   - Check PostgreSQL is accessible

3. **Database errors**
   - Check table creation: `\dt` in psql
   - Review application logs
   - Check disk space

4. **Slow queries**
   - Check indexes: `\d documents` in psql
   - Monitor with pgAdmin
   - Increase memory allocation

---

## Quick Reference

```bash
# Setup and verify
python setup_docker_postgres.py       # Auto Docker setup
python test_postgres_quick.py         # Test connection

# Docker commands
docker-compose up -d                  # Start
docker-compose down                   # Stop
docker logs docgraph_postgres         # View logs
docker ps                             # List containers

# Database access
docker exec -it docgraph_postgres psql -U docuser -d document_processor
psql -U docuser -d document_processor # (if local)

# Application
python app/main.py                    # Start app
http://localhost:5000/docs           # API docs

# Cleanup
docker-compose down -v                # Remove everything
rm -r postgres_data                   # Delete data
```
