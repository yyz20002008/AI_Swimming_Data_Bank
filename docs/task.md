# Swimming Database — Task Tracker

## Phase 1: Scraping & Download
- [x] Build meet list scraper for MD 2023-2024 (73 meets found)
- [x] Build ZIP file downloader with retry logic
- [x] Download & catalog all result files (73/73 meets, 146 CL2+HY3 files, 0 failures)

## Phase 2: Parsing
- [x] ~~Set up hytek-parser for HY3 files~~ (Python 3.8; building custom parser instead)
- [/] Build custom CL2 fixed-width parser (working — events, times, swimmers parsing correctly)
- [ ] Refine team parsing (C1 record) and cross-validate field positions
- [ ] Create Pydantic data models
- [ ] Build batch parser to process all 73 meets → JSON
- [ ] Spot-check 5 meets against PDF results

## Phase 3: Supabase Database & API
- [x] Design & create PostgreSQL schema (schema design approved)
- [x] Generate SQL migration file (`backend/schema.sql`)
- [x] Build data ingestion script (`backend/ingest.py`)
- [x] **USER ACTION**: Create Supabase project + run schema.sql
- [x] **USER ACTION**: Set SUPABASE_URL and SUPABASE_KEY env vars
- [/] Run ingestion: `python -m backend.ingest`
- [ ] Verify materialized views work via Supabase dashboard

## Phase 4: Frontend
- [ ] Set up Vite + React project
- [ ] Build Meet Browser page
- [ ] Build Swimmer Search + Profile pages
- [ ] Build Event Rankings page
- [ ] Add time progression charts
- [ ] Mobile responsive design

## Phase 5: Deploy & Verify
- [ ] Deploy backend to Railway/Render
- [ ] Deploy frontend to Vercel
- [ ] Run full verification suite
- [ ] Measure and optimize latency
