# Project Roadmap: AnimeDashboard

This document tracks the 6-week plan, deliverables, and acceptance criteria. See the main README for directory mapping to roadmap phases.

## Week 1 — MVP: ETL + DB + Basic Dashboard

Goal: Get a working pipeline: ETL grabs Jikan data → store snapshots in Postgres → simple dashboard shows charts from DB.

### Day 1 — Scaffolding & Setup - COMPLETED

**Tasks Completed:**
- Initialized monorepo structure with clear service boundaries
- Created repo layout: `etl/`, `backend/`, `frontend/`, `infra/`, `tests/`, `docs/`, `.github/`
- Added comprehensive README.md with setup instructions
- Locked in stack choices:
  - ETL: Python + SQLAlchemy + Pydantic + tenacity (retry/backoff)
  - Backend: FastAPI with PostgreSQL + Redis connecti
  - Frontend: React + Recharts for visualizations
- Created docker-compose.yml with services: postgres, redis, etl, backend, frontend
- Added docker-compose.override.yml for local development hot reload
- Set up PostgreSQL schema with `anime_snapshots` table
- Created Dockerfiles for all services
- Added requirements.txt and package.json with pinned versions
- Configured .gitignore for Python, Node, Docker, and OS files

**Key Design Decisions:**
- Monorepo approach for easier CI/CD in Week 2
- JSONB columns for flexible Jikan API data storage
- Health checks in Docker Compose for reliable startup
- Environment variable support for Week 5 secrets management

### Day 2 — ETL Design COMPLETED

**Tasks Completed:**
- Defined data snapshot strategy using Jikan search endpoint (`GET /anime`):
  - Top Anime: `order_by=score&sort=desc&status=complete`
  - Seasonal Current: `order_by=popularity&sort=desc&status=airing` 
  - Upcoming: `order_by=popularity&sort=desc&status=upcoming`
  - Popular Movies: `type=movie&order_by=popularity&sort=desc`
- Updated database schema to match exact Jikan API response structure
- Added unique constraints: `(mal_id, snapshot_type, snapshot_date)` for upserts
- Created comprehensive ETL architecture:
  - **Extractor** (`etl/extractors/jikan_extractor.py`): Async API client with retry/backoff
  - **Transformer** (`etl/transformers/anime_transformer.py`): Pydantic validation & cleaning
  - **Loader** (`etl/loaders/postgres_loader.py`): Bulk inserts with upsert capability
  - **Orchestrator** (`etl/orchestrator.py`): Configurable job management
- Implemented retry/backoff patterns:
  - Exponential backoff with tenacity library
  - Rate limiting (1 second between requests)
  - 429 handling with `Retry-After` header respect
- Added Pydantic models for type safety and validation
- Created structured logging for observability preparation
- Built test script for ETL validation


**Unit Testing Framework Created:**
- Built complete test suite covering all ETL components with 98.82% code coverage
- Created test infrastructure: `tests/unit/` with pytest, async testing, mocking, and coverage reporting
- **test_config.py**: ETL settings validation, environment variable overrides, job configuration testing
- **test_extractor_jikan.py**: API extraction logic, rate limiting, retry/backoff, pagination, error handling
- **test_transformer_anime.py**: Data transformation, Pydantic validation, text cleaning, error recovery
- **test_loader_database.py**: DB operations, upsert logic, batch processing, SQL error handling
- Added comprehensive mock fixtures for Jikan API responses
- Implemented edge case testing: invalid data, network failures, validation errors
- Test coverage exceeds 70% requirement (99% code coverage achieved)
- All 64 unit tests passing with structured error handling validation

### Day 3 — Integration Testing & End-to-End Verification

**Tasks Completed:**
- Built focused integration test suite in `tests/integration/` directory with clear separation of concerns
- **Connection Testing** (`a_test_connections.py`): 
  - Database connectivity verification with schema validation
  - Jikan API connectivity testing with response structure validation
  - Standalone executable for quick health checks
- **ETL Pipeline Testing** (`b_test_jobs.py`):
  - End-to-end ETL job validation (Extract → Transform → Load)
  - Individual job testing with detailed progress reporting
  - Concurrent testing of all ETL jobs with proper rate limiting
  - Comprehensive error reporting with load statistics breakdown
- **Database Schema Verification** (`c_db_check.py`):
  - Streamlined database schema validation script
  - Data distribution analysis by snapshot type
  - Sample data verification with top-scoring anime display

**Rate Limiting Enhancement:**
- Implemented `JikanRateLimiter` class (`etl/src/extractors/rate_limiter.py`) for concurrent job safety
- Added async lock mechanism to prevent API rate limit violations during parallel job execution
- Configurable delay settings (1.5s default) to respect Jikan API limits
- Integrated rate limiter across all ETL components for consistent behavior

**Integration Test Results:**
- All connection tests pass: Database schema validation and API connectivity
- All ETL jobs execute successfully, checking for load with proper upsert tracking
- Concurrent job execution works reliably without rate limit violations
- Fixed database loader reporting to distinguish between new inserts vs. successful updates

**Key Debugging & Fixes:**
- Identified and resolved JSON serialization issues for JSONB database fields
- Fixed misleading load statistics reporting (successful_inserts vs. successful_updates). Debugged API response duplicates (25 requested → 23 unique records) - working as intended

### Day 4 — Backend API & Redis Caching Integration

**Tasks Completed:**
- Refactored backend to use FastAPI dependency injection for Redis, following production-ready patterns (lifecycle management, no global singletons)
- Implemented Redis caching for analytics endpoints (database stats, genre distribution, top-rated anime, seasonal trends)
- Configured per-endpoint cache TTLs for optimal freshness and performance
- All cache keys and TTLs are domain-specific and documented in code
- Startup/shutdown lifecycle for Redis connection managed via FastAPI lifespan
- AnalyticsService now receives Redis client via DI, enabling easier testing and future extensibility
- Verified API endpoints return correct data and cache hits/misses are logged
- All backend endpoints (analytics, health) are working and documented in Swagger UI

**Key Design Decisions:**
- Pure dependency injection for Redis (no global state)
- Async Redis client for non-blocking cache operations
- Caching logic is encapsulated in the analytics service, but Redis client is managed at the app level
- Maintained testability and production best practices for future scaling
