# CCIP — Campus Career & Curriculum Intelligence Platform

An AI-powered intelligence platform that connects industry skill demand to college curriculum and student readiness.

## Project Structure

```
ccip/
├── backend/              # Python + FastAPI backend
│   ├── app/
│   │   ├── api/v1/       # REST API endpoints
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy ORM models (30 tables)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic services
│   │   ├── adapters/     # UMS integration adapters
│   │   ├── nlp/          # NLP pipeline (resume parsing, skill extraction)
│   │   └── ml/           # ML models (matching, gap analysis)
│   ├── alembic/          # Database migrations
│   ├── tests/            # pytest test suite
│   └── Dockerfile
├── frontend/             # React + Vite frontend
├── data/                 # Datasets and seeds
│   ├── seeds/            # Database seed scripts
│   ├── taxonomy/         # Skill taxonomy data
│   ├── jobs/             # Job description datasets
│   └── eval/             # Evaluation datasets
├── ml/                   # ML experiments and models
│   ├── experiments/      # Experiment scripts and results
│   └── models/           # Trained model artifacts
├── docs/                 # Documentation and diagrams
└── docker-compose.yml    # Full-stack deployment
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development without Docker)

### Run with Docker Compose

```bash
docker compose up
```

This starts:
- **Backend API**: http://localhost:8000 (Swagger docs at /docs)
- **Frontend**: http://localhost:5173
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Run Backend Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Database Migrations

```bash
cd backend
alembic upgrade head
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 16 + pgvector |
| Task Queue | Celery + Redis |
| NLP | spaCy, sentence-transformers |
| ML | scikit-learn, XGBoost |
| LLM | Gemini API / Ollama |
| Deployment | Docker Compose |

## License

Academic project — all rights reserved.
