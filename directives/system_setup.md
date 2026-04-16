# Directive: System Setup

## Goal
Set up the complete moments4u development environment from scratch.

## Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop (for local stack)

## Steps

### 1. Clone and configure
```bash
cp .env.example .env
# Fill in secrets in .env
```

### 2. Start infrastructure (Docker)
```bash
docker compose -f infra/docker-compose.yml up -d db redis minio
```

### 3. Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head       # Run migrations
python -m app.seed         # Seed dev data (optional)
```

### 4. Frontend setup
```bash
cd frontend
npm install
cp .env.example .env.local
```

### 5. Run everything
```bash
# Option A: Docker Compose (recommended)
docker compose up

# Option B: Manual
# Terminal 1: uvicorn app.main:app --reload
# Terminal 2: celery -A app.tasks.celery_app worker -l info
# Terminal 3: celery -A app.tasks.celery_app beat -l info
# Terminal 4: cd frontend && npm run dev
```

## Verification
- FastAPI docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MinIO console: http://localhost:9001
- PostgreSQL: localhost:5432

## Tools/Scripts
- `execution/setup_db.py` — Initialize database and extensions
- `execution/seed_data.py` — Create test users, playgroups, children

## Edge Cases
- **pgvector not available**: The `pgvector/pgvector:pg16` Docker image includes it. If using a managed DB, enable the extension manually: `CREATE EXTENSION vector;`
- **insightface model download**: First run downloads ~300MB model. Ensure network access.
- **GPU support**: For CPU-only, insightface works but is slower (~2s/image vs ~200ms with GPU).
