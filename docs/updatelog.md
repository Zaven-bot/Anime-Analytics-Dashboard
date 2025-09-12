# Project Log: AnimeDashboard

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

### Day 5 - Frontend and Full-Stack Deployment Established
<!-- Add this to the end of updatelog.md -->

**Frontend Dashboard Implementation:**
- Built comprehensive React dashboard using Tailwind CSS, shadcn/ui components, and Recharts for data visualization
- Created **AnimeDashboard** with anime-inspired styling (gradients, vibrant colors, micro-interactions, hover animations)
- Implemented **OverviewCards** component displaying key database statistics with real-time API data
- Developed **GenreChart** component with sophisticated data visualization options:
  - Three data view modes: Raw Counts (number of anime), Coverage % (percentage of anime with genre), Frequency % (percentage of all genre mentions)
  - Multiple chart types: Bar charts and pie charts with dynamic color coding
  - Snapshot type filtering: Top Rated, Airing, Upcoming, Movies with real-time data switching
  - Smart tooltips and legends with contextual data explanations
- Built **TrendsChart** component for seasonal anime analytics:
  - Time-series visualization of seasonal trends (winter/spring/summer/fall by year)
  - Multiple metrics: Quality Score, Release Volume, Audience Size, Visibility Rank, Total Favorites
  - Dynamic time range filtering with smart year selection (Last 1-5 years, auto-excludes non-existent data)
  - Multiple chart types: Line charts, area charts, combined bar/line charts with dual Y-axes
- Created **TopAnimeTable** component with sortable rankings and detailed anime information
- Implemented comprehensive API integration (`lib/api.js`) with proper error handling, loading states, and retry logic
- Added shadcn/ui component library (Button, Card, Skeleton, Table) with custom anime-themed styling
- Built responsive layouts with mobile-friendly design patterns and accessibility considerations

**Enhanced Backend Analytics:**
- Updated seasonal trends endpoint to provide comprehensive seasonal analytics with resolved season/year mapping
- Enhanced genre distribution with dual percentage calculations (coverage vs frequency percentages)
- Improved data handling with smart NULL value processing and statistical accuracy
- Added comprehensive response models matching frontend data requirements
- Maintained Redis caching for all expensive analytics queries with appropriate TTLs

**Development Workflow Established:**
- **Frontend**: `npm start` in frontend directory (React dev server on port 3000)
- **Backend**: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` in backend directory
- **ETL**: `python b_test_jobs.py` from tests/integration directory for data pipeline execution
- All services communicate effectively with proper CORS configuration and error handling
- Real-time data updates from backend to frontend with loading states and error boundaries
- **Postgres & Reds**: `docker compose up -d postgres redis` in AnimeDashboard directory

**Technical Achievements:**
- Complete elimination of mock data - all visualizations use real anime data from Jikan API
- Type-safe API integration with comprehensive error handling and user feedback
- Production-ready component architecture with reusable UI elements and consistent styling
- Advanced data visualization with multiple chart types, interactive filtering, and contextual tooltips

The frontend successfully demonstrates a complete anime analytics platform with professional-grade data visualizations, responsive design, and seamless real-time data integration from the ETL pipeline.