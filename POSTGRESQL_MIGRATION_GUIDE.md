# PostgreSQL Migration Guide

## What Changed

The application now uses **PostgreSQL** instead of SQLite for all metadata storage.

### Old Configuration
```python
DATABASE_URL: str = "sqlite:///./documents.db"
```

### New Configuration
```python
DB_HOST: str = "localhost"
DB_PORT: int = 5432
DB_USER: str = "postgres"
DB_PASSWORD: str = "postgres"
DB_NAME: str = "document_processor"
```

**Constructed URL:** `postgresql://postgres:postgres@localhost:5432/document_processor`

---

## Setup Instructions

### Step 1: Install PostgreSQL

#### Windows
```bash
# Download from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

#### macOS
```bash
brew install postgresql@15
brew services start postgresql@15
```

#### Linux (Ubuntu)
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2: Create Database and User

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create user
CREATE USER postgres WITH PASSWORD 'postgres';

-- Alter user privileges
ALTER USER postgres CREATEDB;

-- Create database
CREATE DATABASE document_processor OWNER postgres;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE document_processor TO postgres;

-- Exit psql
\q
```

### Step 3: Update Configuration

**Option A: Environment Variables (.env file)**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=document_processor
```

**Option B: Direct in config (app/core/config.py)**
```python
DB_HOST: str = "localhost"
DB_PORT: int = 5432
DB_USER: str = "postgres"
DB_PASSWORD: str = "your_secure_password"
DB_NAME: str = "document_processor"
```

### Step 4: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

### Step 5: Run Application

```bash
python app/main.py
```

The database tables will be created automatically on first run.

---

## Environment Variables

Set these in your `.env` file or system environment:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=document_processor

# API Keys
OPENROUTER_API_KEY=your_api_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key

# Other
QDRANT_COLLECTION=documents
REDIS_URL=redis://localhost:6379/0
```

---

## Migrating from SQLite to PostgreSQL

If you have existing SQLite data, use this process:

### Option 1: Using pgLoader (Recommended)

```bash
# Install pgLoader
# Windows: Download from https://pgloader.io/
# Linux: apt-get install pgloader
# macOS: brew install pgloader

# Migrate
pgloader sqlite:///./documents.db postgresql://postgres:postgres@localhost/document_processor
```

### Option 2: Manual Export/Import

```bash
# Export from SQLite
sqlite3 documents.db ".mode insert documents" ".output documents.sql" "SELECT * FROM documents;"

# Import to PostgreSQL
psql -U postgres -d document_processor -f documents.sql
```

### Option 3: Fresh Start (Recommended for new projects)

```bash
# Delete old SQLite file
rm documents.db

# Restart application - tables will be created automatically
python app/main.py
```

---

## Database Schema

The PostgreSQL schema is identical to SQLite:

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    layout_data JSONB,
    graph_data JSONB,
    processed_json JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

---

## Performance Improvements with PostgreSQL

### Advantages over SQLite
✅ **Better for concurrent access** - Multiple users/requests
✅ **JSONB support** - More efficient JSON queries
✅ **Automatic indexing** - Can index JSON fields
✅ **Better full-text search** - If needed
✅ **Replication** - Can replicate data
✅ **Large datasets** - Handles millions of documents efficiently
✅ **Connection pooling** - Built-in connection management

### Potential Bottlenecks
- Network latency (if using remote server)
- Database server resource limits
- Connection pool limits

---

## Backup and Restore

### Backup PostgreSQL Database

```bash
# Full backup
pg_dump -U postgres -d document_processor > backup.sql

# Or binary format (faster for large DBs)
pg_dump -U postgres -d document_processor -Fc > backup.dump
```

### Restore PostgreSQL Database

```bash
# From SQL file
psql -U postgres -d document_processor < backup.sql

# From binary dump
pg_restore -U postgres -d document_processor backup.dump
```

### Automated Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
mkdir -p $BACKUP_DIR

pg_dump -U postgres -d document_processor -Fc > "$BACKUP_DIR/backup_$DATE.dump"

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.dump" -mtime +30 -delete
```

---

## Connection Issues Troubleshooting

### "Connection refused"
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1;"

# On Windows:
pg_isready -h localhost -p 5432

# Start PostgreSQL service (Windows):
net start postgresql-x64-15
```

### "Authentication failed"
```bash
# Check credentials in config
# Verify DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Reset PostgreSQL password:
psql -U postgres
ALTER USER postgres PASSWORD 'new_password';
```

### "Database does not exist"
```bash
# The database will be created automatically if it doesn't exist
# But you can manually create it:
createdb -U postgres document_processor
```

---

## Configuration Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|-----------|
| **File** | documents.db | Network database |
| **Concurrency** | Limited | Excellent |
| **Max Size** | ~140 TB (theoretical) | Unlimited |
| **JSON Support** | JSON only | JSONB (faster) |
| **Indexing** | Basic | Advanced (including JSON) |
| **Replication** | None | Yes |
| **Backup** | File copy | pg_dump |
| **Setup** | Automatic | Requires server |

---

## Environment Example

Create a `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=document_processor

# API Configuration
OPENROUTER_API_KEY=sk-xxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Vision Models
VISION_MODEL=qwen/qwen2.5-vl-72b-instruct
PROCESSOR_MODEL=qwen/qwen-2.5-72b-instruct

# Langfuse Tracing
LANGFUSE_PUBLIC_KEY=pk_xxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk_xxxxxxxxxxxxx
LANGFUSE_HOST=https://cloud.langfuse.com

# Cache
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# Celery
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=cache+memory://

# Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=52428800
```

---

## Testing PostgreSQL Connection

```python
# test_postgres_connection.py
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✓ PostgreSQL connection successful")
        print(f"  URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"✗ PostgreSQL connection failed: {e}")
```

Run it:
```bash
python test_postgres_connection.py
```

---

## What Was Changed in Code

### app/core/config.py
- Replaced `DATABASE_URL` string with `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- Added property `DATABASE_URL` that constructs PostgreSQL connection string
- Still compatible with all existing code

### app/core/database.py
- No changes needed - already uses `settings.DATABASE_URL`
- Will automatically work with PostgreSQL

### app/models/document.py
- No changes needed - SQLAlchemy is database-agnostic

---

## Verification

After setup, verify everything works:

```bash
# 1. Check database connection
python test_postgres_connection.py

# 2. Start application
python app/main.py

# 3. Check database tables created
psql -U postgres -d document_processor -c "\dt"

# 4. Test API
curl http://localhost:5000/health
```

---

## Next Steps

1. **Install PostgreSQL** - Choose your OS version from Step 1
2. **Create database** - Run the SQL commands from Step 2
3. **Set environment variables** - Create .env file from Environment Example
4. **Verify connection** - Run test_postgres_connection.py
5. **Start application** - `python app/main.py`

---

**Status:** PostgreSQL migration complete ✅
**Database:** Persistent storage
**Backup:** Use pg_dump
**Performance:** Better for scale
