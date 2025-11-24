# PostgreSQL Setup on Windows - Complete Guide

## Option 1: Direct PostgreSQL Installation (Recommended)

### Step 1: Download PostgreSQL Installer

1. Visit: https://www.postgresql.org/download/windows/
2. Download PostgreSQL 15 or 16 (Latest)
3. Run the installer (postgresql-16.1-1-windows-x64.exe)

### Step 2: Installation Configuration

During installation, set:
- **Installation Directory**: `C:\Program Files\PostgreSQL\16` (default is fine)
- **Data Directory**: Use default or `C:\Program Files\PostgreSQL\16\data`
- **Superuser Password**: Set a strong password (remember it!)
- **Port**: Keep default `5432`
- **Locale**: Default or English

### Step 3: Verify Installation

```powershell
# In PowerShell (after restart):
psql --version
```

Expected output: `psql (PostgreSQL) 16.1`

### Step 4: Create Database and User

```powershell
# Connect to PostgreSQL (will prompt for password)
psql -U postgres

# Then in psql prompt, run:
CREATE DATABASE document_processor;
CREATE USER docuser WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;
\q
```

### Step 5: Update .env File

Create `.env` file in Scripts folder:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_here
DB_NAME=document_processor
```

### Step 6: Test Connection

```bash
python test_postgres_connection.py
```

---

## Option 2: Docker Installation (Alternative)

If you prefer Docker, no local PostgreSQL installation needed.

### Step 1: Install Docker Desktop

- Download: https://www.docker.com/products/docker-desktop
- Follow installation wizard
- Restart computer

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: docgraph_postgres
    environment:
      POSTGRES_USER: docuser
      POSTGRES_PASSWORD: secure_password_here
      POSTGRES_DB: document_processor
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docuser"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Step 3: Start PostgreSQL Container

```bash
# In same folder as docker-compose.yml
docker-compose up -d

# View logs
docker-compose logs postgres

# Stop container
docker-compose down
```

### Step 4: Update .env File

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_here
DB_NAME=document_processor
```

### Step 5: Test Connection

```bash
python test_postgres_connection.py
```

---

## Option 3: Windows Subsystem for Linux (WSL2)

If you have WSL2 installed:

```bash
# In WSL terminal
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start

# Create user/database (same as Option 1)
sudo -u postgres psql

# Then in psql:
CREATE DATABASE document_processor;
CREATE USER docuser WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;
\q
```

Update `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_here
DB_NAME=document_processor
```

---

## Troubleshooting

### Issue: "psql: command not found"

**Solution**: PostgreSQL not in PATH
- Add to PATH: `C:\Program Files\PostgreSQL\16\bin`
- Restart PowerShell/terminal
- Try again: `psql --version`

### Issue: "Connection refused"

**Solution**: PostgreSQL service not running
- Windows: Open Services (services.msc), find "PostgreSQL", start it
- OR: `net start postgresql-x64-16`

### Issue: "FATAL: role 'postgres' does not exist"

**Solution**: Use existing superuser
```bash
# Check existing users
SELECT usename FROM pg_user;

# Use found username (e.g., 'postgres')
psql -U postgres
```

### Issue: "FATAL: password authentication failed"

**Solution**: Reset PostgreSQL password
```bash
# Windows:
# 1. Stop PostgreSQL service
# 2. Edit: C:\Program Files\PostgreSQL\16\data\pg_hba.conf
# 3. Change "md5" to "trust" on local connections
# 4. Restart PostgreSQL
# 5. Connect and reset password:

psql -U postgres
ALTER USER postgres WITH PASSWORD 'newpassword';
\q

# 6. Revert pg_hba.conf change back to "md5"
# 7. Restart PostgreSQL
```

### Issue: "Database already exists"

**Solution**: Drop and recreate
```sql
DROP DATABASE document_processor;
CREATE DATABASE document_processor;
```

Or connect to existing database (no recreation needed).

---

## Quick Verification Checklist

- [ ] PostgreSQL installed (`psql --version` works)
- [ ] PostgreSQL service running (check Windows Services)
- [ ] Database created (can connect: `psql -U postgres -d document_processor`)
- [ ] User created with password
- [ ] `.env` file configured
- [ ] `psycopg2-binary` installed (`pip list | grep psycopg2`)
- [ ] Test script passes: `python test_postgres_connection.py`

---

## Next Steps

Once verified:

```bash
# Install missing packages
pip install psycopg2-binary sqlalchemy

# Run test
python test_postgres_connection.py

# Start application
python app/main.py
```

Application will automatically create tables on first run using SQLAlchemy migrations.

---

## Recommended Passwords

For **development only**, you can use simple passwords like:
- `docuser123`
- `localdev_password`
- `postgres`

For **production**, use strong passwords:
- At least 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not based on dictionary words
- Generate with: `openssl rand -base64 32`
