# AnimeDashboard
A anime analytics dashboard that fetches data from the Jikan API, stores it in PostgreSQL, and presents insights through a React frontend.

## Tech Stack

- **ETL**: Python + SQLAlchemy + Redis caching
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: React + Recharts
- **Infrastructure**: Docker Compose + PostgreSQL + Redis

## Project Structure & Roadmap Alignment

- **backend/** — FastAPI backend for API endpoints, analytics, and DB models. (Week 1, Days 3–4)
- **etl/** — ETL worker for fetching, transforming, and inserting Jikan data into Postgres. (Week 1, Days 2–3)
- **frontend/** — React dashboard for visualizing analytics. (Week 1, Day 5)
- **infra/** — Infrastructure as code, docker-compose, DB/Redis config. (Week 1, Day 1; Weeks 3–5)
- **tests/** — Unit and integration tests for ETL, backend, and frontend. (Week 2)
- **docs/** — Documentation, diagrams, SLOs, runbooks, postmortems. (Week 6)
- **.github/** — GitHub Actions workflows for CI/CD. (Week 2, Day 4)

## Quickstart

### Prerequisites
- Docker and Docker Compose
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd AnimeDashboard
   ```

2. **Start the full stack**
   ```bash
   # Start core services (PostgreSQL + Redis + Backend + Frontend)
   docker-compose up -d

   # Run ETL job (one-time or scheduled)
   docker-compose run --rm etl
   ```

3. **Access the application**
   - Frontend Dashboard: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Stop all services**
   ```bash
   docker-compose down
   ```

### Development Mode

For local development with hot reload:

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Or run individual services
docker-compose up postgres redis  # Start dependencies
# Then run backend/etl/frontend locally in separate terminals
```

---

See `docs/roadmap.md` for the full 6-week plan.
