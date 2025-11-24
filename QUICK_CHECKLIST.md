# PostgreSQL Setup Checklist

## ✅ Complete These Steps

### Step 1: Start Docker (2 minutes)
- [ ] Click Start menu
- [ ] Type "Docker Desktop"
- [ ] Click to open
- [ ] Wait 2-3 minutes (watch system tray)
- [ ] Docker icon should appear (animated whale)
- [ ] Animation stops = Ready!

### Step 2: Create .env File (1 minute)
- [ ] Open PowerShell or text editor
- [ ] Navigate to `Scripts` folder
- [ ] Create file `.env`
- [ ] Copy this into it:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=docuser
DB_PASSWORD=secure_password_123
DB_NAME=document_processor
OPENROUTER_API_KEY=your_key_here
```

- [ ] Save file

### Step 3: Setup PostgreSQL (3 minutes)
Choose ONE option:

**Option A - Automatic (Recommended):**
```bash
python setup_docker_postgres.py
```

**Option B - Manual:**
```bash
docker-compose up -d
```

### Step 4: Verify Setup (1 minute)
```bash
python test_postgres_quick.py
```

Expected output:
```
✓ Connected successfully!
✓ POSTGRESQL IS READY!
```

### Step 5: Run Application (1 minute)
```bash
python app/main.py
```

Expected output:
```
Uvicorn running on http://127.0.0.1:5000
```

### Step 6: Test It Works
- [ ] Open browser
- [ ] Go to: http://localhost:5000/docs
- [ ] Try uploading a document
- [ ] Check that it processes

## ⏱️ Total Time: ~10 minutes

## 🆘 Something Not Working?

### "Docker is not running"
1. Start Docker Desktop (see Step 1)
2. Wait 2-3 minutes
3. Run setup script again

### "Connection refused"
1. Check Docker is running: `docker ps`
2. Check container started: `docker-compose ps`
3. View logs: `docker logs docgraph_postgres`

### "Port already in use"
1. Change port in `.env`: `DB_PORT=5433`
2. Update `docker-compose.yml` ports section
3. Restart: `docker-compose restart`

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### "Still stuck?"
1. Read: `POSTGRESQL_QUICK_START.md`
2. Read: `DOCKER_STATUS.md`
3. Check logs: `docker logs docgraph_postgres`

## 📁 Important Files

```
SETUP_STATUS.md                 ← Full status report
POSTGRESQL_QUICK_START.md       ← Detailed guide
DOCKER_STATUS.md                ← Docker issues
setup_docker_postgres.py        ← Auto setup
test_postgres_quick.py          ← Test connection
docker-compose.yml              ← Docker config
.env                            ← Create this!
```

## 🎯 Quick Commands

```bash
# Start Docker (manual)
docker-compose up -d

# Check if running
docker ps

# View logs
docker logs docgraph_postgres

# Stop
docker-compose down

# Test connection
python test_postgres_quick.py

# Run application
python app/main.py

# Access database GUI
# Browser: http://localhost:5050
# Email: admin@docgraph.local
# Password: admin
```

## ✨ You're All Set!

Once you complete all steps above:
- ✓ PostgreSQL is running
- ✓ Application connected to database
- ✓ Ready to upload documents
- ✓ Data persists across restarts

## 🚀 What to Do Next

1. Upload some documents
2. Check they're processing correctly
3. View database via pgAdmin
4. Read full documentation for advanced features

---

**Status**: Ready to deploy ✅
**Next**: Start Docker Desktop (Step 1)
