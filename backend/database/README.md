# 🗄️ EcoGreen Database Management Hub

This directory contains database schemas, initialization scripts, and local database storage for the EcoGreen Farmer-to-Consumer platform.

---

## 🐘 1. PostgreSQL Integration (Recommended for Production)

EcoGreen supports **PostgreSQL** natively via `psycopg2-binary` and `Flask-SQLAlchemy`.

### Step 1: Set Environment Variable in `.env`
Open your `.env` file in the project root and add your PostgreSQL connection string:

```env
# Local PostgreSQL Connection
SQLALCHEMY_DATABASE_URI=postgresql://postgres:your_password@localhost:5432/ecogreen_db

# Or Cloud Hosted PostgreSQL (Supabase / Neon / Render / AWS RDS)
SQLALCHEMY_DATABASE_URI=postgresql://user:password@ep-sample-123.region.postgres.database.azure.com/ecogreen_db
```

### Step 2: Initialize PostgreSQL Tables & Seed Demo Data
Run the automated initialization script from your project root:

```powershell
python backend/database/init_db.py
```

*Or execute the raw SQL schema script directly in `psql`:*
```bash
psql -U postgres -d ecogreen_db -f backend/database/schema.sql
```

---

## 📁 2. SQLite Fallback (Zero-Config Development)

If no `SQLALCHEMY_DATABASE_URI` is specified in `.env`, EcoGreen automatically defaults to the local SQLite database file:

- **Location**: `backend/database/app.db` (or `instance/app.db`)

To re-seed or reset the SQLite database at any time, run:
```powershell
python backend/database/init_db.py
```

---

## 📄 File Index in `backend/database/`

- [`schema.sql`](file:///c:/Users/kv035/Downloads/Farmer-to-Consumer-App-main/Farmer-to-Consumer-App-main/backend/database/schema.sql): Pure PostgreSQL DDL schema with foreign keys and performance indexes.
- [`init_db.py`](file:///c:/Users/kv035/Downloads/Farmer-to-Consumer-App-main/Farmer-to-Consumer-App-main/backend/database/init_db.py): Automated database table creator and Indian demo data seeder.
- [`app.db`](file:///c:/Users/kv035/Downloads/Farmer-to-Consumer-App-main/Farmer-to-Consumer-App-main/backend/database/app.db): Local SQLite database file for offline/fallback development.
