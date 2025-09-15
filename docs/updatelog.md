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

## Week 2 — Testing & Quality Assurance

### Day 1 — Repository Restructure & Comprehensive Linting Infrastructure - COMPLETED

**Repository Modernization:**
- **Complete directory restructure** from flat organization for moreproduction-ready service boundaries:
  - Moved `etl/`, `backend/`, `frontend/` into organized `services/` directory
  - Created `tools/` directory with `linting/` and `scripts/` subdirectories for development tooling
  - Maintained `infrastructure/`, `config/`, `tests/`, `docs/` as top-level directories
  - Created mock Docker Compose paths and import statements to work with new structure
- **Preserved development workflow** by carefully testing each step to ensure no breaking changes
- **Updated all relative import paths** in backend files to maintain functionality with new directory structure

**Comprehensive Linting Infrastructure Setup:**
- **Python Linting Tools** configured with strict settings:
  - **flake8**: Code style enforcement with E501 line length exceptions for readability
  - **mypy**: Strict type checking with `--strict` mode for maximum type safety
  - **black**: Automated code formatting with 120-character line length
  - **isort**: Import statement organization and sorting
- **JavaScript Linting Tools** with modern ESLint 9 configuration:
  - **ESLint**: Updated from legacy `.eslintrc.js` to modern `eslint.config.js` format
  - **Prettier**: Consistent code formatting across all JavaScript/React files
  - Configured React and React Hooks plugins for component best practices
- **Isolated Development Environment**:
  - Created dedicated `anime-linting` micromamba environment with all linting dependencies
  - Isolated from main application environments to prevent version conflicts
  - Reproducible across development machines with locked dependency versions

**Configuration Files Created:**
- **`.flake8`** in `tools/linting/`: Python style guide enforcement with project-specific rules
- **`pyproject.toml`** in `tools/linting/`: Combined configuration for mypy, black, and isort with consistent settings
- **`eslint.config.js`** in `tools/linting/`: Modern ESLint 9 configuration with React plugin integration
- **`.prettierrc`** in `tools/linting/`: JavaScript code formatting rules matching project style

**Automated Development Scripts:**
- **`lint.sh`** in `tools/scripts/`: Comprehensive linting runner executing all checks in sequence
  - Python: flake8 → mypy → black (check-only mode)
  - JavaScript: eslint → prettier (check-only mode)
  - Clear success/failure reporting with colored output
- **`format.sh`** in `tools/scripts/`: Automated code formatting and auto-fixing
  - Python: isort (import sorting) → black (code formatting)
  - JavaScript: prettier (formatting) → eslint (auto-fixable issues)
  - Batch processing of all project files with progress reporting

**Major Code Quality Improvements:**
- **Fixed hundreds of linting violations** through systematic automated formatting and manual corrections
- **Enhanced type safety** by adding explicit type annotations throughout the codebase:
  - Added `cast()` functions for dictionary operations that were causing `object has no attribute` errors
  - Fixed lambda function type inference issues in sorting operations with proper type casting
  - Added type hints to critical functions and variables
  - Resolved all mypy strict type checking errors without compromising functionality
- **Improved code consistency** with automated import organization and formatting standards
- **Eliminated dangerous type errors** that could cause runtime bugs in production

**Type Safety Enhancements:**
- **Analytics Service**: Fixed genre sorting function with explicit type casting for `x.get("anime_count", 0)` operations
- **ETL Main Pipeline**: Added proper type annotations for `ETL_JOBS` dictionary operations using `cast(Dict[str, Any], ...)` 
- **Import Organization**: Consolidated type imports (`cast`, `Dict`, `Any`) for cleaner code structure
- **Lambda Functions**: Resolved mypy type inference issues in sorting operations with explicit casting

**Final Results:**
- **Zero linting errors** across entire Python codebase (23 files checked)
- **Zero linting errors** across entire JavaScript/React codebase
- **All formatting checks pass** with consistent code style enforcement
- **Comprehensive type safety** with mypy strict mode compliance
- **Automated tooling** ready for CI/CD integration in future weeks
- **Professional development workflow** with easy-to-use scripts for consistent code quality

**Development Workflow Enhancement:**
- Simple commands for developers: `./tools/scripts/lint.sh` for checking, `./tools/scripts/format.sh` for auto-fixing
- Pre-commit ready infrastructure for automated quality gates
- Isolated linting environment prevents conflicts with application dependencies
- Clear error reporting and success indicators for rapid feedback during development

### Day 2 — Comprehensive Backend API Unit Testing Infrastructure

**FastAPI Testing Architecture:**
- **Resolved Critical TestClient API Compatibility Issue**: Fixed `AsyncClient.__init__() unexpected 'app' argument` error by implementing proper `ASGITransport` pattern:
  ```python
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as client:
  ```
**Complete Test Suite Implementation (72/72 Tests Passing - 100% Success Rate):**

**1. Analytics API Testing (`test_api_analytics.py` - 9/9 tests):**
- **Database Statistics Endpoint**: Tests `/api/v1/analytics/stats/overview` with mock data validation
- **Top Anime Ranking**: Tests `/api/v1/analytics/anime/top-rated` with filtering (limit, min_score, snapshot_type)
- **Genre Distribution**: Tests `/api/v1/analytics/anime/genre-distribution` with snapshot type filtering
- **Seasonal Trends**: Tests `/api/v1/analytics/trends/seasonal` with year range and metric selection
- **Error Handling**: Proper validation of service errors, invalid parameters, and graceful degradation
- **Mock Integration**: Comprehensive dependency injection with proper service mocking using FastAPI's override system

**2. Health Check Testing (`test_api_health.py` - 11/11 tests):**
- **Basic Health Check**: Tests `/health` endpoint for simple uptime verification
- **Detailed Health Status**: Tests `/health/detailed` with database and Redis connectivity validation
- **Response Format Validation**: Corrected expectations from `data["services"]` to `data["checks"]` structure
- **CORS Headers**: Verification of proper Cross-Origin Resource Sharing configuration
- **Performance Testing**: Response time validation and concurrent request handling
- **Error Scenarios**: Proper handling of database/Redis connection failures with appropriate status codes

**3. Dependency Injection Testing (`test_dependency_injection.py` - 10/10 tests):**
- **Service Creation**: Tests FastAPI dependency system creates `AnalyticsService` instances correctly
- **Dependency Override System**: Validates mock service injection with proper cleanup
- **Service Lifecycle**: Tests singleton behavior and request scope isolation
- **Nested Dependencies**: Tests complex dependency chains (analytics service → Redis client)
- **Error Handling**: Proper exception handling for failed dependency initialization
- **Isolation Testing**: Validates different override values between requests work correctly

**4. Redis Caching Testing (`test_redis_caching.py` - 18/18 tests):**
- **Cache Operations**: Tests `_get_cached_data()` and `_set_cached_data()` with TTL management
- **Cache Hit/Miss Behavior**: Validates proper cache key generation and retrieval logic
- **TTL Management**: Tests `setex` command usage (not separate `set`/`expire` calls)
- **Error Fallback**: Proper handling when Redis is unavailable (graceful degradation)
- **Connection Management**: Tests Redis client lifecycle and connection failure handling
- **Analytics Integration**: Tests caching behavior in actual service methods (`get_database_stats`)
- **Cache Key Collisions**: Validates different methods/parameters generate unique cache keys

**5. Response Models Validation (`test_response_models.py` - 24/24 tests):**
- **Pydantic Model Validation**: Comprehensive testing of all API response models
- **Data Serialization**: Tests JSON serialization/deserialization with proper type conversion
- **Nested Models**: Validates nested structures (DatabaseOverview, GenreDistributionItem, etc.)
- **Field Validation**: Tests required fields, optional fields, and default values
- **Type Safety**: Ensures proper typing for integers, floats, strings, dates, and lists

**Key Technical Solutions Implemented:**

**FastAPI Testing Best Practices:**
- **AsyncClient Pattern**: Async test client setup with transport-based configuration
- **Dependency Override**: Clean dependency injection testing with proper cleanup
- **Mock Strategy**: Isolated service mocking without affecting application state
- **Error Boundaries**: Error scenario testing with expected status codes

**Redis Caching Architecture:**
- **Cache Method Testing**: Direct testing of `_get_cached_data()` and `_set_cached_data()` private methods
- **TTL Validation**: Confirmed `setex` usage pattern in actual implementation vs test expectations
- **Connection Error Handling**: Tests graceful Redis connection failure handling
- **Integration Testing**: Cache behavior testing within actual service methods

**Mock Data Accuracy:**
- **Pydantic Validation**: Ensured all mock data passes actual Pydantic model validation
- **Environment Isolation**: Used `anime-backend` micromamba environment with pytest 8.4.2
- **Testing Dependencies**: httpx, AsyncClient, pytest-asyncio, pytest-mock, pytest-cov
- **Async Testing**: `@pytest.mark.asyncio` usage for FastAPI endpoint testing

**CI/CD Pipeline Readiness:**
- **Coverage**: 72 tests covering all critical API endpoints and service logic
- **Mock Strategy**: Isolated testing without external dependencies (database/Redis)
- **Error Scenarios**: Coverage of connection failures, service errors, and edge cases
- **Performance Validation**: Response time testing and concurrent access patterns
- **Integration Ready**: Tests validate actual API contracts and response formats

**Final Results:**
- **Success**: 72/72 tests passing across all 5 test suites
- **Zero Flaky Tests**: Consistent test execution with proper mock isolation
- **Production Ready**: Tests validate actual API behavior with realistic scenarios  
- **Maintainable**: Clear test structure with comprehensive documentation and examples
- **CI/CD Compatible**: Fast execution, no external dependencies, clear failure reporting

### Day 3 — Docker Compose Infrastructure & Deployment Orchestration

**Complete Docker Containerization:**
- **Multi-Service Docker Architecture**: Successfully containerized all services with proper networking and dependency management
- **Cross-Service Dependencies Resolved**: Fixed backend service imports of ETL components using shared volume mounts:
  ```yaml
  volumes:
    - ../../services/etl:/shared/etl  # Mount ETL code for backend to import
  ```
- **Environment Variable Management**: Configured proper timezone (`TZ=UTC`) and database URLs across all services
- **Health Check Integration**: All services use health checks for reliable startup orchestration
- **Volume Persistence**: External volumes for PostgreSQL and Redis data persistence

**Docker Compose Service Profiles:**
- **Core Services** (no profile): `postgres`, `redis`, `backend`, `frontend`
- **ETL Profile**: Manual ETL job execution capability
- **Scheduler Profile**: Automated daily ETL scheduling service
- **Development Overrides**: Hot reload and debug configurations (currently disabled)

**Frontend-Backend Integration:**
- **Network Configuration**: Fixed Docker networking for React frontend to backend API communication
- **Environment Variables**: Proper `REACT_APP_API_URL` configuration for container vs. browser context
- **API Integration**: Frontend successfully connects to backend through Docker port mapping (`localhost:8000`)

**Docker Compose Execution Commands:**

**1. Core Development Stack (Default):**
```bash
cd infrastructure/docker-compose
docker compose up -d
# Runs: postgres, redis, backend, frontend
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

**2. With Automated ETL Scheduling:**
```bash
cd infrastructure/docker-compose
docker compose --profile scheduler up -d
# Runs: core services + etl-scheduler (automated daily ETL at 8 AM UTC)
```

**3. With Manual ETL Capability:**
```bash
cd infrastructure/docker-compose
docker compose --profile etl up -d
# Runs: core services + etl container for manual job execution
# Execute ETL: docker compose exec etl python main.py
```

**4. Full Stack (All Services):**
```bash
cd infrastructure/docker-compose
docker compose --profile etl --profile scheduler up -d
# This can break as locking logic for JikanAPI requests are not
# prepared for multiple instances of schedulers
# Runs: core services + manual ETL + automated scheduler
```

**5. Individual Service Management:**
```bash
# Start only database services
docker compose up -d postgres redis

# View logs for specific service
docker compose logs -f backend

# Execute commands in running containers
docker compose exec etl python main.py
docker compose exec backend python -m pytest

# Stop all services
docker compose down

# Stop and remove volumes (full cleanup)
docker compose down -v
```

**6. Development Overrides (Optional):**
```bash
# Enable hot reload and debug mode (rename docker-compose.override.disabled.yml)
mv docker-compose.override.disabled.yml docker-compose.override.yml
docker compose up -d
```

**Service Port Mapping:**
- **Frontend**: `localhost:3000` (React development server)
- **Backend**: `localhost:8000` (FastAPI with automatic reload)
- **PostgreSQL**: `localhost:5433` (mapped from container port 5432)
- **Redis**: `localhost:6379` (direct mapping)

**Key Docker Architecture Decisions:**
- **Shared Volumes**: ETL code mounted to backend container for cross-service imports
- **Service Dependencies**: Proper `depends_on` with health check conditions
- **Timezone Consistency**: UTC timezone across all services for reliable scheduling
- **Network Isolation**: Services communicate via Docker Compose internal network
- **External Volumes**: Data persistence across container restarts

**Dockerfile Verification:**
- **Backend Dockerfile**: Correct Python environment with FastAPI and uvicorn
- **ETL Dockerfile**: Fixed main.py path (not src/main.py) with proper dependencies
- **Frontend Dockerfile**: Node.js 18 with npm development server
- **All Dockerfiles**: Optimized layer caching with requirements/package.json copied first

**Production-Ready Features:**
- **Health Checks**: All services have proper health check configurations
- **Restart Policies**: ETL scheduler has `unless-stopped` restart policy
- **Volume Management**: External named volumes for data persistence
- **Environment Variables**: Proper secrets and configuration management
- **Service Profiles**: Flexible deployment configurations for different environments

The Docker Compose infrastructure provides a complete development and deployment environment with reliable service orchestration, proper networking, and flexible execution models for different use cases.

---

## CI/CD Pipeline with Environment-Aware Integration Testing

**Implementation:** GitHub Actions workflow (`.github/workflows/ci.yml`) with automatic environment detection and real service integration testing.

### Key Features

**Local Environment (Docker Compose):**
- PostgreSQL on port 5433, database `anime_dashboard`
- Redis on port 6379, database 0
- Full dataset limits, 1.5s API rate limiting

**GitHub Actions (Service Containers):**
- PostgreSQL on port 5432, database `test_db` 
- Redis on port 6379, database 1
- Conservative limits, 2.0s API rate limiting

**Environment-Aware Configuration:**
```python
# services/etl/src/config.py - Automatic detection
if os.getenv('GITHUB_ACTIONS'):
    database_url = "postgresql://test_user:test_password@localhost:5432/test_db"
    redis_url = "redis://localhost:6379/1"
    jikan_rate_limit_delay = 2.0  # Conservative for CI
```

### Pipeline Jobs

1. **Code Quality** (non-blocking): flake8, black, mypy
2. **Unit Tests**: 136+ tests with mocks, coverage reporting
3. **Integration Tests**: Real PostgreSQL + Redis testing in both environments
4. **Docker Builds**: All three services with health validation

### Testing Commands

```bash
# Run all tests locally (needs Docker Compose running)
python -m pytest tests/unit/ -v                    # Unit tests (work anywhere)
python -m pytest tests/integration/ -v             # Integration tests (ETL pipeline)
python tests/integration/test_api_db_integration.py # API endpoint tests
python tests/integration/test_redis_cache_integration_simple.py # Redis cache tests

# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/analytics/database-stats
```
### Integration Test Coverage

- **ETL Pipeline**: Complete data flow from Jikan API → PostgreSQL (6 tests)
- **API Endpoints**: FastAPI health and analytics validation  
- **Redis Caching**: Cache operations, expiration, concurrency
- **Database Operations**: Schema validation, upserts, data persistence
- **Cross-Service Communication**: Backend ↔ Database ↔ Redis

**Result:** CI/CD with real integration testing that automatically adapts to local development vs GitHub Actions environments. Every push validates the complete system integration with actual PostgreSQL and Redis services, not just mocks.

## Week 3 — Observability & Monitoring

Goal: Transform the AnimeDashboard from a functional application into a production-ready system with comprehensive observability, enabling proactive monitoring, performance optimization, and operational insights.

### Day 1 — Backend & ETL Metrics Instrumentation - COMPLETED

**Objective**: Implement comprehensive Prometheus metrics collection across all services to establish foundational observability for performance monitoring and operational insights.

#### Technical Implementation

**1. Backend Metrics Infrastructure (`services/backend/app/metrics.py`):**
```python
class MetricsCollector:
    def __init__(self):
        # HTTP request tracking
        self.http_requests_total = Counter(
            'http_requests_total', 'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        # Cache performance monitoring  
        self.redis_cache_operations_total = Counter(
            'redis_cache_operations_total', 'Redis cache operations',
            ['operation', 'cache_type']
        )
        
        # Database query performance
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds', 'Database query duration',
            ['operation_type', 'table_name']
        )
```

**Key Architectural Decision**: Centralized metrics collection with method-specific tracking enables granular performance analysis while maintaining clean separation of concerns.

**2. ETL Metrics Server (`services/etl/src/metrics_server.py`):**
- **Standalone metrics server on port 9090** to prevent metric namespace pollution
- **Job execution tracking** with duration, success/failure rates, and record processing counts
- **Jikan API monitoring** with response time tracking and rate limit handling
- **Database operation metrics** for ETL pipeline performance analysis

**Interview Talking Point**: *"This is like having separate dashboards for different workers - each service has its own metrics endpoint, so ETL pipeline monitoring doesn't interfere with user-facing API metrics."*

**3. Cross-Service Integration Challenges Solved:**

**Problem**: ETL metrics were appearing on the backend `/metrics` endpoint due to Prometheus's global registry pattern, and backend service was tightly coupled to ETL components through shared volume mounts.

**Solution**: **Microservice Decoupling with Environment-Based Configuration**
- **Removed ETL dependency entirely** from backend service - no more `/shared/etl` volume mount
- **Direct SQLAlchemy integration** using standard `DATABASE_URL` and `REDIS_URL` environment variables
- **Clean service boundaries**: Backend handles API logic, ETL handles data pipeline, both share database independently
- **Eliminated metric namespace pollution**: Each service manages its own Prometheus metrics without cross-contamination

```python
# Before: Backend importing ETL components
from src.config import get_settings
from src.loaders.database import DatabaseLoader

# After: Direct environment variable configuration
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
```

**Architectural Insight**: This demonstrates true microservice architecture - services communicate via shared persistence layer (database) rather than code imports.

#### Connection Pool Monitoring Deep-Dive

**Challenge**: Database connection pool metrics were showing 0.0 values despite active connections.

**Technical Investigation**: 
```python
def _update_connection_metrics(self, db_engine, redis_client):
    """Enhanced connection pool introspection with fallback strategies"""
    try:
        # SQLAlchemy pool introspection
        pool = db_engine.pool
        if hasattr(pool, 'size'):
            self.connection_pool_size.set(pool.size())
        if hasattr(pool, 'checkedin'):
            self.connection_pool_checked_in.set(pool.checkedin())
    except Exception as e:
        # Graceful degradation with reasonable defaults
        logger.warning("Connection pool metrics unavailable", error=str(e))
```

**Interview Insight**: *"This taught me that library APIs can vary between versions, so production monitoring code needs defensive programming with graceful fallbacks."*

#### Code Quality & Maintainability Improvements

**Refactoring Achievement**: Eliminated code duplication between `analytics.py` and `health.py` by centralizing connection metrics logic:

```python
# Before: Duplicated logic in multiple files
# After: Single source of truth in metrics.py
def update_connection_metrics(self, db_engine=None, redis_client=None):
    """Centralized connection pool monitoring"""
```

**Technical Leadership Moment**: *"I noticed we were copying the same connection monitoring logic across files. Instead of technical debt accumulating, I refactored it into a reusable function. Then I realized we had a deeper architectural issue - our backend service was importing ETL pipeline code, violating microservice principles. I decoupled the services entirely, using environment variables and direct database connections instead of shared code imports."*

#### Production-Ready Architecture Patterns

**1. True Microservice Isolation**: Backend and ETL services operate independently with no code dependencies
**2. Environment-Driven Configuration**: Standard `DATABASE_URL`/`REDIS_URL` pattern for cloud deployment
**3. Namespace Isolation**: ETL metrics on port 9090, backend metrics on port 8000
**4. Graceful Degradation**: Metrics collection failures don't break application functionality  
**5. Observability-Driven Development**: Every database query, cache operation, and HTTP request is instrumented
**6. Independent Deployment**: Services can be deployed, scaled, and updated separately

#### Interview Storytelling Framework

**Situation**: "We had a working AnimeDashboard, but no visibility into performance bottlenecks or system health."

**Task**: "I needed to implement comprehensive metrics without disrupting existing functionality - like adding gauges to a car while it's driving."

**Action**: "I designed a two-tier metrics architecture: backend service metrics on port 8000 for user-facing performance, and ETL pipeline metrics on port 9090 for data processing insights. The key challenge was preventing metric namespace pollution between services, which led me to backtrack to our backend importing ETL code - a microservice anti-pattern. I decoupled the services entirely using environment variables and direct database connections."

**Result**: "Now we can monitor database query performance, cache hit rates, HTTP response times, and ETL job success rates. Most importantly, the metrics collection is robust - if monitoring fails, the application keeps running."

**Technical Deep-Dive Questions You Can Handle**:
- "How do you prevent metric namespace collisions in a microservices architecture?"
- "What's your approach to instrumenting existing code without breaking functionality?"  
- "How do you balance comprehensive monitoring with performance overhead?"
- "Describe a time you had to debug cross-service dependency issues."
- "How do you design services for independent deployment and scaling?"
- "What's your approach to service decoupling when you discover tight coupling?"

**Key Takeaway**: This day demonstrates both technical depth (Prometheus internals, Python import mechanics) and systems thinking (service isolation, graceful degradation, operational maintainability). Perfect foundation for discussing production observability in SRE interviews.
