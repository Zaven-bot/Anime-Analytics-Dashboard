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

#### CI/CD Pipeline with Environment-Aware Integration Testing

**Implementation:** GitHub Actions workflow (`.github/workflows/ci.yml`) with automatic environment detection and real service integration testing.

##### Key Features

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

##### Pipeline Jobs

1. **Code Quality** (non-blocking): flake8, black, mypy
2. **Unit Tests**: 136+ tests with mocks, coverage reporting
3. **Integration Tests**: Real PostgreSQL + Redis testing in both environments
4. **Docker Builds**: All three services with health validation

##### Testing Commands

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
##### Integration Test Coverage

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

### Completed Tasks
- Removed non-functional infrastructure metrics:
  - `database_connections_active`
  - `redis_connection_pool_size`
  - `redis_connection_pool_available`
  - `update_connection_metrics()` method

### Retained Application Metrics
- `redis_cache_operations_total` – cache hit/miss tracking  
- `http_requests_total` – HTTP request monitoring  
- `database_queries_total` – database query tracking  
- `analytics_queries_duration_seconds` – query performance monitoring  

### Architecture Adjustments
- Separated application metrics from infrastructure metrics  
- Delegated infrastructure metrics to exporters:
  - Redis: `redis-exporter`
  - PostgreSQL: `postgres-exporter`  
- Application now focuses solely on business logic and performance indicators

### Next Step
- Begin testing observability stack with clean metric boundaries

## Week 3 Day 2 — Prometheus Setup & Infrastructure Exporters - COMPLETED

**Goal**: Deploy complete observability stack with Prometheus, infrastructure exporters, and comprehensive metrics collection.

### Tasks Completed

**Prometheus Configuration**
- Created `infrastructure/observability/prometheus/prometheus.yml` with optimized scrape targets
- Configured scrape intervals: 15s for applications, 30s for infrastructure
- Set up service discovery using Docker service names

**Infrastructure Exporters Integration** 
- Added `postgres-exporter:9187` for comprehensive PostgreSQL metrics
- Added `redis-exporter:9121` for Redis server monitoring
- Using official community images for reliability and maintenance

**Docker Compose Orchestration**
- Integrated observability services with profiles for flexible deployment
- Resolved port conflicts (ETL scheduler internal-only on 9090)
- Fixed network configuration syntax across all services
- Added `anime-network` bridge for proper service communication

**Full Stack Deployment & Validation**
- Successfully deployed 8 services: backend, frontend, ETL, databases, Prometheus, exporters
- All Prometheus targets reporting `"health":"up"` with no errors
- Validated metrics collection across all service endpoints

### Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Applications  │    │   Infrastructure │    │   Prometheus    │
│                 │    │    Exporters     │    │                 │
│ • Backend:8000  │───▶│ • postgres-exp   │───▶│ • Collection    │
│ • ETL:9090      │    │   :9187          │    │ • Storage       │
│                 │    │ • redis-exp      │    │ • Query Engine  │
│                 │    │   :9121          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Service Access Points

- **Prometheus Dashboard**: http://localhost:9090
- **Backend Metrics**: `http://backend:8000/metrics` (internal)
- **ETL Metrics**: `http://etl-scheduler:9090/metrics` (internal)
- **PostgreSQL Metrics**: `http://postgres-exporter:9187/metrics`
- **Redis Metrics**: `http://redis-exporter:9121/metrics`

### Metrics Collection Results

**Application Metrics (Backend)**:
- `anime_dashboard_http_requests_total` - HTTP request tracking
- `redis_cache_operations_total` - Cache performance metrics

**Infrastructure Metrics**:
- **PostgreSQL**: 100+ metrics including `pg_stat_database_*`, `pg_settings_*`, `pg_stat_user_tables_*`
- **Redis**: 100+ metrics including `redis_memory_used_*`, `redis_commands_*`, `redis_connected_clients`

### Deployment Commands

```bash
# Start full observability + application stack
docker compose --profile observability --profile scheduler up -d --build

# Validate all targets are healthy
curl -s 'http://localhost:9090/api/v1/targets' | grep '"health"'

# Check service status
docker compose ps
```

### Problem Resolution

**Issues Encountered & Solved**:
1. Port 9090 conflict between Prometheus and ETL → made ETL internal-only
2. Network syntax errors → fixed `network:` vs `networks:` configuration
3. Broken infrastructure metrics → removed from application, used external exporters

### Configuration Highlights

**Prometheus Scrape Configuration**:
```yaml
scrape_configs:
  - job_name: 'anime-backend'
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 15s

  - job_name: 'anime-etl'  
    static_configs:
      - targets: ['etl-scheduler:9090']
    scrape_interval: 15s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121'] 
    scrape_interval: 30s
```

### Interview Storytelling Framework

**Situation**: "After instrumenting application metrics, we needed a centralized monitoring system to collect, store, and query metrics across our distributed services."

**Task**: "Deploy a production-ready Prometheus stack with infrastructure exporters while avoiding service disruption and resolving port conflicts in our Docker environment."

**Action**: "I designed a multi-tier approach: Prometheus as the central collector, dedicated exporters for infrastructure metrics (PostgreSQL, Redis), and proper network isolation. The key challenge was port conflict resolution - Prometheus needed 9090, but our ETL service was already using it. I reconfigured ETL to be internal-only and exposed Prometheus externally."

**Result**: "Achieved 100% target health across 5 scrape endpoints collecting 200+ metrics. The observability stack now provides real-time insights into application performance, database health, and cache utilization with zero application downtime during deployment."

**Technical Deep-Dive Topics**:
- Service discovery in containerized environments
- Infrastructure monitoring vs application monitoring separation
- Docker networking and port management strategies  
- Prometheus configuration and target management
- Metrics cardinality and storage considerations
- Graceful service deployment with health checks

### Next Steps
- **Week 3 Day 3**: Grafana integration for visual dashboards
- Set up alerting rules for critical thresholds
- Create business-specific monitoring views
- Integrate structured logging with Loki

## Week 3 Day 3 — Grafana Setup & Dashboard Infrastructure - COMPLETED

**Goal**: Deploy comprehensive Grafana visualization stack with rich application metrics integration and dashboard-as-code infrastructure.

### Tasks Completed

**✅ Grafana Deployment with Persistence**
- Successfully deployed Grafana container with proper data persistence using Docker Compose
- Configured volume mounting for `/var/lib/grafana` to ensure dashboard and configuration persistence
- Integrated with existing observability stack using profile-based deployment

**✅ Grafana Provisioning Infrastructure**
- Created automated provisioning structure for reproducible deployments:
  - `infrastructure/observability/grafana/provisioning/datasources/prometheus.yml`: Prometheus datasource configuration
  - `infrastructure/observability/grafana/provisioning/dashboards/dashboard.yml`: Dashboard provider configuration
  - `infrastructure/observability/grafana/dashboards/`: JSON dashboard files for automatic loading
- Implemented dashboard-as-code approach for version control and automated deployment

**✅ Datasource Configuration Resolution**
- **Fixed critical datasource provisioning issue**: Resolved "Datasource prometheus was not found" errors
- **Root cause**: Datasource UID mismatch between provisioning config and dashboard expectations
- **Solution**: Standardized datasource UID to `prometheus` with simplified configuration:
  ```yaml
  datasources:
    - name: Prometheus
      type: prometheus
      uid: prometheus
      access: proxy
      url: http://prometheus:9090
      isDefault: true
  ```
- **Result**: Clean container restart with proper datasource provisioning and dashboard connectivity

**Comprehensive Application Performance Dashboard**
Created advanced dashboard leveraging all available application metrics:

**HTTP Performance Monitoring:**
- **Request Rate**: `rate(anime_dashboard_http_requests_total[5m])` by endpoint, method, and status code
- **Response Time Analysis**: 95th/50th percentile and average using histogram quantiles:
  ```promql
  histogram_quantile(0.95, rate(anime_dashboard_http_request_duration_seconds_bucket[5m]))
  ```
- **Request Volume Statistics**: Total HTTP requests counter with real-time tracking

**Cache Performance Analytics:**
- **Hit Rate Visualization**: Pie chart showing cache effectiveness across all operations
- **Cache Operations by Type**: Detailed tracking of hits/misses by cache key type (top_rated, seasonal_trends, genre_distribution, database_stats)
- **Overall Cache Hit Rate**: Single-value stat with color-coded thresholds (red <80%, yellow 80-90%, green >90%)

**Database Query Performance:**
- **Query Rate by Type**: Real-time database query rate showing top_rated, seasonal_trends, genre_distribution, etc.
- **Query Duration Analysis**: 95th percentile and average query execution time using analytics histogram:
  ```promql
  histogram_quantile(0.95, rate(anime_dashboard_analytics_queries_duration_seconds_bucket[5m]))
  ```

**Key Performance Indicators:**
- **Total HTTP Requests**: Lifetime request counter
- **Total Database Queries**: Cumulative query execution count
- **95th Percentile Response Time**: Real-time API performance indicator
- **Overall Cache Hit Rate**: Application-wide caching effectiveness

### Infrastructure Architecture

**Grafana Service Configuration:**
- **Port**: `localhost:3001` (avoiding frontend conflict on 3000)
- **Authentication**: Admin/admin123 for development access
- **Data Persistence**: Named volume `grafana_data` for configuration retention
- **Network**: Connected to `anime-network` for service discovery

**Dashboard Features:**
- **30-second refresh rate** for near real-time monitoring
- **1-hour time range** with customizable time picker
- **Dark theme** optimized for monitoring environments
- **Tagged organization**: application, performance, http, cache, database tags
- **Color-coded thresholds** for immediate visual status indication

### Metrics Integration Success

**Application Metrics Successfully Integrated:**
- `anime_dashboard_http_requests_total` - Request counting and rate calculation
- `anime_dashboard_http_request_duration_seconds_bucket` - Response time percentiles
- `anime_dashboard_redis_cache_operations_total` - Cache hit/miss tracking
- `anime_dashboard_database_queries_total` - Database query rate monitoring
- `anime_dashboard_analytics_queries_duration_seconds_bucket` - Query performance analysis

**Dashboard Visualization Types:**
- **Time Series Charts**: Request rates, response times, cache operations, query performance
- **Pie Charts**: Cache hit rate visualization with percentage breakdowns
- **Stat Panels**: KPI displays with thresholds and color coding
- **Multi-Query Panels**: Combined metrics showing hits vs misses, percentiles vs averages

### Deployment & Access

**Service Access Points:**
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics Source**: http://localhost:9090 (internal to Grafana)
- **Application Metrics**: All endpoints automatically scraped and visualized

**Docker Compose Integration:**
```bash
# Start observability + scheduler stack
docker compose --profile observability --profile scheduler up -d

# Services running:
# - anime_grafana (port 3001)
# - anime_prometheus (port 9090)  
# - anime_postgres_exporter (port 9187)
# - anime_redis_exporter (port 9121)
# - anime_backend (port 8000) 
# - anime_etl_scheduler (port 9090 internal)
# - anime_frontend (port 3000)
# - anime_postgres (port 5433)
# - anime_redis (port 6379)
```

### Problem Resolution & Technical Learning

**Datasource Provisioning Challenge:**
- **Issue**: Dashboard showing "Datasource prometheus was not found" 
- **Investigation**: Found UID mismatch between dashboard JSON (`uid: prometheus`) and auto-generated UIDs in provisioning
- **Solution**: Explicit UID assignment in datasource configuration
- **Lesson**: Dashboard-as-code requires consistent UID management for reliable automation

**Container Persistence:**
- **Challenge**: Configuration loss on container restarts
- **Solution**: Proper volume mapping and clean container restart workflow
- **Result**: Dashboards and datasource configurations persist across deployments

### Interview Storytelling Framework

**Situation**: "We had comprehensive metrics collection but needed visual dashboards for operational insights and performance monitoring."

**Task**: "Deploy Grafana with automated provisioning to create production-ready dashboards while solving datasource connectivity issues that were preventing dashboard functionality."

**Action**: "I implemented dashboard-as-code using Grafana provisioning with JSON-based dashboards stored in version control. The key challenge was resolving datasource UID mismatches that were preventing dashboard operation. I debugged the provisioning process by examining container logs and fixed it with explicit UID configuration."

**Result**: "Deployed a comprehensive monitoring dashboard displaying real-time HTTP performance, cache analytics, and database query performance. The dashboard uses advanced Prometheus queries like histogram quantiles for response time analysis and rate calculations for throughput monitoring."

**Technical Deep-Dive Topics**:
- Grafana provisioning architecture and dashboard-as-code implementation
- Advanced PromQL queries: histogram quantiles, rate calculations, aggregation functions
- Container orchestration with persistent volumes and service discovery
- Metrics visualization best practices: thresholds, color coding, panel types
- Observability stack integration: Prometheus + Grafana + exporters
- Dashboard performance optimization and refresh rate configuration

...existing content...

## Week 3 Day 5 — Structured Logging & Loki Integration - COMPLETED

**Goal**: Deploy Loki for log aggregation, enhance structured logging with correlation IDs, create log analysis dashboards, and establish SLI/SLO baselines.

### Tasks Completed

**Loki & Promtail Deployment**
- Added Loki (port 3100) and Promtail to Docker Compose observability profile
- Configured Promtail to collect logs from all Docker containers
- Created comprehensive Promtail configuration for service-specific log parsing
- Integrated Loki as Grafana datasource with proper provisioning

**Enhanced Structured Logging**
- ~~Already implemented structured JSON logging across all services using `setup_logging()`~~
- **Added correlation ID middleware** for request tracing in FastAPI
- Enhanced middleware with consistent contextual fields (method, path, status, duration)
- Fixed SQLAlchemy import issue introduced during logging refactor

**Log Analysis Infrastructure**
- Created comprehensive log analysis dashboard in Grafana
- Implemented log volume monitoring by service and log level
- Added error log exploration with filtering capabilities  
- Created correlation views between metrics and logs
- ETL job execution log analysis with structured queries

**SLI/SLO Baseline Documentation**
- Documented current performance baselines from Week 3 metrics
- Established API SLIs: availability (99.5%), latency (p95 < 500ms), error rate (<5%)
- Defined ETL SLIs: success rate (95%), job duration monitoring
- Created infrastructure SLIs: cache hit rate (>70%), database performance
- Prepared alerting threshold proposals for Week 4 implementation

### Technical Implementation

**Correlation ID Implementation:**
```python
# Enhanced middleware with request tracing
@app.middleware("http")  
async def add_correlation_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    # Bind to structlog context for automatic inclusion
    structlog.contextvars.bind_contextvars(request_id=request_id)
```

**Log Pipeline Architecture:**
- **Application logs**: Structured JSON via structlog → stdout
- **Container logs**: Docker log driver → Promtail
- **Log aggregation**: Promtail → Loki → Grafana
- **Service isolation**: Separate log streams per service with consistent labeling

**SLI/SLO Framework:**
```yaml
api_availability_slo:
  objective: 99.5%
  window: 30d
  error_budget: 3.6_hours
  burn_rate_alerts: [2x, 5x, 10x]
```

### Architecture Achievements

**Production-Ready Observability Stack:**
1. **Three-pillar observability**: Metrics (Prometheus), Logs (Loki), Traces (correlation IDs)
2. **Unified Grafana interface**: Single pane of glass for metrics and logs
3. **Service correlation**: Request IDs enable cross-service debugging
4. **Structured data**: All logs are JSON with consistent schema

**Operational Excellence:**
- Comprehensive monitoring covering all system layers
- Error budget methodology for deployment safety
- Automated alerting strategy (critical vs warning)
- Historical trending for capacity planning

### Interview Storytelling

**Challenge**: "How do you implement comprehensive observability in a microservices architecture?"

**Approach**: "I implemented the three pillars of observability—metrics, logs, and traces—using industry-standard tools integrated into a cohesive monitoring strategy."

**Implementation**: 
- Prometheus for real-time metrics collection across all services
- Loki for centralized log aggregation with structured JSON format  
- Correlation IDs for request tracing across service boundaries
- Grafana dashboards unifying metrics and logs for comprehensive system visibility

**Outcome**: Complete observability stack enabling proactive monitoring, faster incident resolution, and data-driven SLO management.

**Technical Deep-Dive Topics:**
- Log aggregation patterns in containerized environments
- Correlation ID propagation across service boundaries  
- SLI/SLO framework design and error budget management
- Structured logging schema design for operational queries

### Next Steps: Week 4 — Resilience & Alerting

With comprehensive observability in place, Week 4 will focus on:
- Implementing alerting rules based on established SLIs
- Circuit breaker patterns for API resilience
- Chaos engineering for failure mode validation
- Performance optimization based on observability insights

**Current Status**: Full observability stack operational with metrics, logs, and traces integrated into Grafana dashboards. SLI baselines established for SLO implementation.

---

## Week 5 — Infrastructure & Security Hardening (IaC, Secrets, Deployment Strategies) - IN PROGRESS

Goal: Move infra to IaC, add secrets management, and implement safer deployment patterns.

### Security Hardening - Day 1 — Container Security

**Progress Update - September 18, 2025**

**✅ Action Item 1: Non-Root User Implementation**
- **Modified** `services/backend/Dockerfile` - Added `appuser` with proper ownership
- **Modified** `services/etl/Dockerfile` - Added `appuser` with proper ownership  
- **Modified** `services/frontend/Dockerfile` - Added `appuser` with Alpine-specific user creation

**Security Improvements:**
- All containers now run with dedicated non-privileged users (UID 1001)
- Application files properly owned by `appuser:appuser`
- Eliminated root privilege escalation attack surface
- Used `--chown` flag during COPY operations for efficient ownership transfer

**Technical Details:**
- Backend/ETL: Standard Linux `groupadd`/`useradd` commands
- Frontend: Alpine-specific `addgroup`/`adduser` commands for lightweight containers
- Maintained Docker layer caching optimization by placing user creation early

**Next Steps:** Multi-stage builds for production optimization, secrets management, TLS implementation.

**✅ Action Item 2: Multi-Stage Build Implementation**
- **Modified** `services/backend/Dockerfile` - Added builder/production stages, eliminated build tools from final image
- **Modified** `services/etl/Dockerfile` - Added builder/production stages, copied only runtime dependencies
- **Modified** `services/frontend/Dockerfile` - Added Node.js builder stage + nginx production serving
- **Created** `services/frontend/nginx.conf` - Production nginx configuration with React Router support

**Production Optimization Benefits:**
- **Smaller Images**: Eliminated build tools (gcc, npm) from production containers
- **Frontend Optimization**: Static files served by nginx instead of Node.js dev server
- **Better Caching**: Separated build dependencies from runtime layers
- **Enhanced Security**: Minimal attack surface with only essential runtime packages
- **Performance**: nginx serving static assets with gzip compression and caching headers

**Technical Implementation:**
- Python services: Used `--user` pip install, copied only `.local` to production stage
- Frontend: `npm run build` creates optimized static bundle served by nginx
- Custom nginx config handles React Router client-side routing
- Maintained non-root user security across all stages