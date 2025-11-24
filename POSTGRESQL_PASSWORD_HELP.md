# PostgreSQL Local Setup - Password Reset Needed

PostgreSQL 18 is installed and running, but we need to set up the database and user.

## The Issue
PostgreSQL requires authentication. We need to either:
1. Know the postgres user password (set during installation)
2. Reset it

## Solution: Reset PostgreSQL Password

### Step 1: Stop PostgreSQL Service
Open PowerShell as Administrator and run:
```powershell
net stop postgresql-x64-18
```

### Step 2: Start PostgreSQL in Recovery Mode
```powershell
cd "C:\Program Files\PostgreSQL\18\bin"
pg_ctl.exe -D "C:\Program Files\PostgreSQL\18\data" -c -l "C:\postgresql.log" start
```

### Step 3: Connect Without Password
```powershell
cd "C:\Program Files\PostgreSQL\18\bin"
psql.exe -U postgres -d postgres -h localhost
```

This should connect without password in recovery mode.

### Step 4: Reset Password
In psql prompt, run:
```sql
ALTER USER postgres WITH PASSWORD 'postgres';
\q
```

### Step 5: Restart PostgreSQL Normally
```powershell
net stop postgresql-x64-18
net start postgresql-x64-18
```

### Step 6: Create Database User
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

Enter password: `postgres`

Then run:
```sql
CREATE DATABASE document_processor;
CREATE USER docuser WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;
\q
```

### Step 7: Create .env File
In Scripts folder, create `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_123
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
```

### Step 8: Test
```powershell
python test_postgres_quick.py
```

## Alternative: Use postgres User Directly

If you remember the postgres password from installation, just create .env:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<password_from_installation>
DB_NAME=postgres
OPENROUTER_API_KEY=your_key_here
```

And run:
```powershell
python test_postgres_quick.py
```

## Quick Commands

```powershell
# Connect to PostgreSQL
psql -U postgres

# View databases
psql -U postgres -c "\l"

# Reset password
psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'newpassword';"

# Create database
psql -U postgres -c "CREATE DATABASE document_processor;"

# Check PostgreSQL version
psql --version

# Check PostgreSQL service
Get-Service postgresql-x64-18
```

## Need Help?

1. What's your postgres password? (from PostgreSQL installation)
   - If you remember it: Use it in .env file
   - If you forgot it: Follow "Step 1-5" above to reset

2. Once password is set:
   - Create .env file with credentials
   - Run: `python test_postgres_quick.py`

Let me know the postgres password and I can help you complete the setup!
