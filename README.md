# moments4u

> **A secure photo capture and sharing platform for playgroups.**
> Caregivers capture children's learning moments. Parents view them securely, grouped by their child's face.

## Overview
moments4u leverages facial recognition to process photos uploaded by teachers and automatically groups them into timelines for each parent.

### Features
* **Face Recognition Pipeline:** RetinaFace for facial detection + ArcFace for 512-dim face embeddings.
* **Vector Search:** Highly accurate and blazing fast matching using PostgreSQL + `pgvector`.
* **Privacy by Design:** Photos are encrypted, temporarily cached in an S3 store (MinIO), and auto-deleted via Celery workers after 7 days.
* **Responsive Portals:** Custom portals for both Parents (Timelines & Walkthroughs) and Teachers (Drag & drop batch upload portals).

## Architecture Stack
The application is built using a strict 3-layer modular architecture to enforce deterministic workflows:

* **Frontend:** Next.js 14, React 18, Tailwind-inspired Vanilla CSS Design System, PWA ready.
* **Backend:** FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic, Uvicorn.
* **Task Queue:** Celery with Redis broker.
* **Database:** PostgreSQL (with `pgvector` and `uuid-ossp` extensions).
* **Storage:** MinIO or AWS S3.

## Quick Start (Local Setup)

### 1. Boot up Infrastructure
Make sure Docker Desktop is running, then start the core infrastructure:
```bash
docker-compose -f infra/docker-compose.yml up -d
```

### 2. Start the Backend
Requires Python 3.12+
```bash
cd backend
python -m venv .venv
source .venv/scripts/activate  # (or simply '.venv/scripts/activate' on Windows)
pip install -e ".[dev]"

# Create tables and generate seed data
python ../execution/setup_db.py
python ../execution/seed_data.py

# Run the API
fastapi dev app/main.py
```

### 3. Open the Frontend
Requires Node 20+
```bash
cd frontend
npm install
npm run dev
```

Visit the app at `http://localhost:3000`.

## Testing Credentials
Once seeded, test accounts are available:
* **Admin:** `admin@moments4u.test` / `admin123`
* **Teacher:** `teacher1@moments4u.test` / `teacher123`
* **Parent:** `parent.smith@moments4u.test` / `parent123`
