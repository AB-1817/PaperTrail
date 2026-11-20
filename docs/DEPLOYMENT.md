# PaperTrail Deployment Guide

## 1. Local Stack Setup
```bash
# 1. Start Vector DB & Cache
docker compose up -d qdrant redis

# 2. Start Supabase (Local DB + Auth)
supabase start
supabase db reset

# 3. Launch Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 4. Launch Frontend
cd frontend
npm install
npm run dev
```

## 2. Security Checklist
- Confirm `SUPABASE_SERVICE_ROLE_KEY` is not exposed in frontend environment variables.
- Ensure SSRF guard domain allowlist is active.
- Verify RLS policies on Supabase tables.
