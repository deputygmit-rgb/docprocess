# PostgreSQL Setup - Local Windows Installation (No Docker)

Since Docker virtualization isn't available on your system, we'll install PostgreSQL locally.

## Quick Setup (15 minutes)

### Step 1: Download PostgreSQL Installer
1. Go to: https://www.postgresql.org/download/windows/
2. Click "Download the installer" under "Interactive installer by EDB"
3. Download PostgreSQL 16 (or latest stable version)
4. File will be named like: `postgresql-16.x-x-windows-x64.exe`

### Step 2: Run Installer
1. Double-click the downloaded .exe file
2. Click "Next" through setup
3. **Important settings:**
   - Port: Keep **5432** (default)
   - Password: Set a password (e.g., `postgres`)
   - Superuser: Keep as **postgres**
4. Click "Finish"

### Step 3: Verify Installation
Open PowerShell and check:
```powershell
psql --version
```

Should show: `psql (PostgreSQL) 16.x`

If error "psql not found", restart PowerShell or restart computer.

### Step 4: Create Database
Open PowerShell and connect to PostgreSQL:
```powershell
psql -U postgres
```

It will ask for password - enter the password you set during installation.

Then run these SQL commands:
```sql
CREATE DATABASE document_processor;
CREATE USER docuser WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;
\q
```

### Step 5: Create .env File
In Scripts folder, create `.env` file with:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_123
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
```

### Step 6: Test Connection
```powershell
python test_postgres_quick.py
```

Should show:
```
✓ Connected successfully!
✓ POSTGRESQL IS READY!
```

### Step 7: Run Application
```powershell
python app/main.py
```

Application will create tables automatically and be ready at `http://localhost:5000`

## Troubleshooting

### "psql: command not found"
1. Restart PowerShell
2. Or restart computer
3. Or add to PATH:
   - Search "Environment Variables"
   - Add: `C:\Program Files\PostgreSQL\16\bin`

### "Port 5432 already in use"
```powershell
# Find what's using port 5432
netstat -ano | findstr :5432

# Or change port in .env to 5433
DB_PORT=5433
```

### "Password authentication failed"
1. Check password in .env matches what you set
2. Or reset password in psql:
```powershell
psql -U postgres
ALTER USER docuser WITH PASSWORD 'new_password';
\q
```

### "Database already exists"
```powershell
psql -U postgres
DROP DATABASE document_processor;
CREATE DATABASE document_processor;
```

## Verify Everything Works

1. Check PostgreSQL is running:
```powershell
psql -U postgres -c "SELECT version();"
```

2. Check database was created:
```powershell
psql -U postgres -l
```

3. Test application connection:
```powershell
python test_postgres_quick.py
```

4. Start application:
```powershell
python app/main.py
```

5. Open browser: http://localhost:5000/docs

## Quick Reference

```powershell
# Connect to PostgreSQL
psql -U postgres

# Connect to specific database
psql -U docuser -d document_processor

# List databases
psql -U postgres -c "\l"

# List users
psql -U postgres -c "\du"

# Test connection (from Scripts folder)
python test_postgres_quick.py

# View PostgreSQL version
psql --version
```

## Start/Stop PostgreSQL

PostgreSQL starts automatically after installation.

To start/stop manually:
```powershell
# Windows Services - search "Services" in Start menu
# Find "PostgreSQL" and click Start/Stop

# Or via command line:
# Start
net start postgresql-x64-16

# Stop
net stop postgresql-x64-16
```

## Performance Notes

For development, default PostgreSQL settings are fine. For production, you can optimize:
```
C:\Program Files\PostgreSQL\16\data\postgresql.conf
```

Key settings:
- `shared_buffers = 256MB` (25% of RAM)
- `effective_cache_size = 1GB` (50-75% of RAM)
- `work_mem = 16MB`

## What's Different From Docker

| Aspect | Docker | Local |
|--------|--------|-------|
| Installation | Easy (docker-compose) | Manual installer |
| Virtualization | Required | Not required |
| Starting/Stopping | docker-compose up/down | Services or net start/stop |
| Data Location | Docker volume | C:\Program Files\PostgreSQL\16\data |
| GUI Management | pgAdmin on 5050 | Use pgAdmin standalone |
| Removal | Delete container | Uninstall from Control Panel |

Everything else in the application is exactly the same!

## Done!

Once PostgreSQL is installed and running:
1. Create .env file (from Step 5 above)
2. Run: `python test_postgres_quick.py`
3. Start app: `python app/main.py`

You're all set! 🚀
