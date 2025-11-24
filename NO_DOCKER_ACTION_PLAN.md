# PostgreSQL Setup - Action Plan (No Docker Needed)

## Good News! 🎉

PostgreSQL 18 is already installed and running on your system!

```
✓ PostgreSQL 18 installed
✓ PostgreSQL service running
✓ psql.exe available
⏳ Database not yet created
⏳ Application user not yet created
```

## What We Need to Do (2 steps)

### Step 1: Get the PostgreSQL Password

During PostgreSQL installation, you would have set a password for the `postgres` superuser.

**Do you remember this password?**

- **Yes** → Go to Step 2 below
- **No** → See "Forgot Password?" section

### Step 2: Create Database and User

Once you have the postgres password:

#### Option A: Use Setup Script (Easiest)
```powershell
python setup_local_postgres.py
```

The script will:
- Connect to PostgreSQL with your password
- Create `document_processor` database
- Create `docuser` user
- Create .env file
- Test the connection
- Done!

#### Option B: Manual Setup
1. Open PowerShell
2. Connect: `psql -U postgres`
3. Enter password when prompted
4. Run these SQL commands:

```sql
CREATE DATABASE document_processor;
CREATE USER docuser WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE document_processor TO docuser;
\q
```

5. Create .env file in Scripts folder with:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_123
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
```

## Quick Verification

Once setup is complete:

```powershell
# Test connection
python test_postgres_quick.py

# Should show:
# ✓ Connected successfully!
# ✓ POSTGRESQL IS READY!
```

## Forgot Password?

If you forgot the postgres password:

### Method 1: Windows Services (Easiest if using local account)

1. Stop PostgreSQL:
   ```powershell
   net stop postgresql-x64-18
   ```

2. Edit PostgreSQL config:
   - File: `C:\Program Files\PostgreSQL\18\data\pg_hba.conf`
   - Find line with "local" and "md5"
   - Change "md5" to "trust"

3. Start PostgreSQL:
   ```powershell
   net start postgresql-x64-18
   ```

4. Connect without password:
   ```powershell
   psql -U postgres
   ```

5. Set new password:
   ```sql
   ALTER USER postgres WITH PASSWORD 'postgres';
   \q
   ```

6. Stop PostgreSQL and revert pg_hba.conf

7. Start PostgreSQL again

### Method 2: Contact IT/Check Installation Files

If you don't have local admin access, contact your IT department to reset the postgres password.

## Files Ready to Use

```
POSTGRESQL_LOCAL_SETUP.md         ← Detailed local setup guide
POSTGRESQL_PASSWORD_HELP.md       ← Password reset instructions
setup_local_postgres.py           ← Automated setup script
test_postgres_quick.py            ← Test connection script
.env.example                      ← Configuration template
```

## The Next 5 Minutes

1. Check if you remember postgres password (1 min)
2. Run setup script or manual SQL commands (2 min)
3. Create .env file (1 min)
4. Test: `python test_postgres_quick.py` (1 min)

## Then You're Done!

```powershell
python app/main.py
```

Open browser: http://localhost:5000/docs

## Summary

| What | Status |
|------|--------|
| PostgreSQL | ✅ Installed & Running |
| Configuration | ✅ Ready |
| Setup Scripts | ✅ Ready |
| Database | ⏳ Needs postgres password |
| .env file | ⏳ Ready to create |
| Application | ⏳ Ready to run |

## Your Move

**What's the postgres password?** (Or would you like password reset instructions?)

Once you have it, we can complete setup in 5 minutes! 🚀
