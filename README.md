# 🏊 Swimming Data Bank — Quick Start Guide

## Current Status

| Phase | Status | Details |
|-------|--------|---------|
| 1. Scraping | ✅ Done | 73 meets, 146 files downloaded |
| 2. Parsing | ✅ Done | 143,706 results in `data/parsed/all_meets_2023_2024.json` |
| 3. Database | 🔧 Ready | Schema + ingest script built, needs Supabase project |
| 4. Frontend | ⬜ Next | After DB is populated |
| 5. Deploy | ⬜ | After frontend |

---

## Phase 3: Supabase Setup (10 minutes)

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com) → Sign in with GitHub
2. Click **"New Project"**
3. Settings:
   - Name: `swimming-data-bank`
   - Database Password: (save this somewhere!)
   - Region: `US East (N. Virginia)` (closest to MD)
4. Wait ~2 minutes for the project to initialize

### Step 2: Run Schema SQL
1. In your Supabase dashboard → **SQL Editor** (left sidebar)
2. Click **"New Query"**
3. Open `backend/schema.sql` from this project, copy ALL contents
4. Paste into the SQL Editor and click **"Run"**
5. You should see: "Success. No rows returned" (that's correct!)
6. Verify: Go to **Table Editor** → you should see 6 tables + 3 views

### Step 3: Get API Keys
1. Go to **Settings** → **API** (left sidebar)
2. Copy these two values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **service_role key** (under "Project API keys" → the `service_role` one, NOT the `anon` one)

### Step 4: Set Environment Variables
```powershell
# In PowerShell:
$env:SUPABASE_URL = "https://xxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Step 5: Run Data Ingestion
```powershell
cd d:\Backup-STUDY-7-22-2018\AI_Swimming_Data_Bank
python -m backend.ingest
```

This will load all 143,706 results into Supabase. Takes ~5-10 minutes.

### Step 6: Verify
1. Go to Supabase **Table Editor** → `individual_results` → should have ~143K rows
2. Try the auto-generated API:
   ```
   https://xxxxx.supabase.co/rest/v1/swimmers?last_name=eq.Adams&select=*
   ```
   (Add header: `apikey: your-anon-key`)

---

## Project Structure

```
AI_Swimming_Data_Bank/
├── scraper/                    # Phase 1: Data scraping
│   ├── config.py               #   Configuration & URLs
│   ├── meet_list_scraper.py    #   Scrapes meet list from GoMotion
│   └── file_downloader.py      #   Downloads & extracts ZIP files
│
├── swim_parser/                # Phase 2: CL2/HY3 parsing
│   ├── cl2_parser.py           #   CL2 fixed-width format parser
│   ├── time_utils.py           #   Time conversion & event normalization
│   └── batch_parse.py          #   Batch process all meets → JSON
│
├── backend/                    # Phase 3: Database & API
│   ├── schema.sql              #   PostgreSQL schema for Supabase
│   └── ingest.py               #   Data ingestion script
│
├── data/
│   ├── raw/2023_2024/          #   73 meet folders with CL2+HY3 files
│   ├── parsed/
│   │   └── all_meets_2023_2024.json  # 143,706 parsed results
│   └── manifests/
│       └── meet_manifest_2023-2024.json
│
├── docs/                       #   Documentation
│   ├── implementation_plan.md
│   ├── task.md
│   └── database_schema_design.md
│
└── requirements.txt
```

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Swimmer identity | USS ID (USA Swimming registration #) | Unique across teams, ages, name changes |
| Database | Supabase (PostgreSQL) | Free tier, auto REST API, built-in auth |
| Parser | Custom CL2 parser (not OCR) | 100% accuracy on structured data |
| Normalization | 3NF + materialized views | Clean writes + fast reads |
| Frontend | Next.js + Vercel | SSR for SEO, great DX |
| CDN | Cloudflare | Free DNS + caching |
| Analytics | PostHog | Free tier 1M events/mo |
