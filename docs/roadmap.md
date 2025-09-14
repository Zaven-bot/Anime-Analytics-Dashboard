**Framing:**

- **Core scope:** Weeks 1–4 (MVP → tests → observability → resilience).
- **Stretch scope (time permitting):** Advanced chaos engineering, canary deploys, polish/portfolio assets in Weeks 5–6.
- **Outcome:** Even if only Weeks 1–4 are completed, the project demonstrates a working, tested, observable, resilient system.
    
    ---
    
    ## Week 1 — MVP: ETL + DB + Basic Dashboard
    
    **Goal:** Get a working pipeline: ETL grabs Jikan data → store snapshots in Postgres → simple dashboard shows charts from DB.
    
    **Day-by-day:**
    
    - **Day 1:** Project scaffolding, repo layout, README stub, choose stack (e.g., FastAPI + React).
    - **Day 2:** ETL worker / cron job design (what snapshots to store: top/seasonal/upcoming).
    - **Day 3:** Implement ETL happy-path (fetch → transform → schema validate → insert into Postgres).
        - Add schema validation step: validate Jikan payloads, reject/flag malformed rows, log warnings.
    - **Day 4:** Backend endpoints that surface aggregated analytics (e.g., `/analytics/top-anime`, `/analytics/genre-distribution`).
    - **Day 5:** Minimal React dashboard showing 3 charts (top 10, genre distribution, seasonal trend). Basic styling.
    
    **Deliverables:**
    
    - ETL pipeline that runs locally and writes validated data to Postgres.
    - Backend endpoints returning DB-driven results.
    - Frontend with three working visualizations.
    - README with how to run locally (docker-compose recommended for Week 1).
    
    **Acceptance criteria:**
    
    - ETL runs without errors and inserts only valid snapshot rows.
    - Invalid/missing fields are rejected or logged without crashing ETL.
    - API endpoints return correct JSON for seeded snapshots.
    - Dashboard displays charts based on API responses.
    
    **Risks / mitigations:**
    
    - Jikan rate limits → implement basic caching (in-memory or Redis) and respectful backoff in ETL.
    - Data drift / schema changes → mitigate with validation + migration plan.
    
    ---
    
    ## Week 2 — Tests + CI/CD (unit + integration + linting)
    
    **Goal:** Add robust unit + integration testing, enforce linting/static analysis, and wire checks into CI so every push runs consistently.
    
    **Day-by-day:**
    
    - **Day 1:**
        - Write unit tests for ETL transform functions (schema normalization, aggregation logic, schema validation).
        - Add linting/static checks setup: flake8 + mypy (Python), eslint + prettier (React).
    - **Day 2:** Unit tests for API handlers (logic, error paths, fallback behavior). Aim for clear separation so logic is testable without network.
    - **Day 3:** Integration test harness: docker-compose or Testcontainers to run Postgres+Redis+app; write integration tests:
        - ETL → DB insertion verification.
        - API endpoints reading from DB.
        - Cache behavior (Redis).
    - **Day 4:** Create GitHub Actions workflow:
        - **Lint → static analysis → unit tests → build → start integration stack → run integration tests.**
    - **Day 5:** Add test quality gates (e.g., fail CI on test failures). Add codecov (optional).
    
    **Deliverables:**
    
    - pytest/jest unit suites covering core logic.
    - Integration suite running against disposable containers.
    - CI pipeline (GitHub Actions) running lint, static checks, unit + integration tests on PRs.
    
    **Acceptance criteria:**
    
    - Linting + static analysis pass locally and in CI.
    - Unit tests pass locally and in CI.
    - Integration tests pass in CI using disposable services.
    - CI fails if linting, type checks, or tests fail.
    - Achieve test targets: unit coverage threshold (e.g., ≥70%) and critical integration tests green.
    
    **Notes:**
    
    - Mock external Jikan responses for unit tests; integration tests can use a lightweight mock server (static fixtures) or a recorded set.
    
    ---
    
    ## Week 3 — Observability: Metrics, Logs, Dashboards
    
    **Goal:** Instrument app and pipeline, deploy observability stack (Prometheus, Grafana, Loki), and create operational dashboards.
    
    **Day-by-day:**
    
    - **Day 1:** Add metrics to backend & ETL (HTTP request latency, request count, error count, ETL job success/failure, cache hit ratio).
    - **Day 2:** Expose Prometheus metrics endpoints; add basic instrumentation for DB and Redis usage.
    - **Day 3:** Deploy Prometheus + Grafana + Loki (locally via Helm or docker-compose depending on environment).
    - **Day 4:** Build Grafana dashboards:
        - App metrics (latency, error rate, throughput).
        - ETL metrics (last run time, success rate).
        - Infra metrics (DB connections, memory/CPU).
    - **Day 5:** Create basic logging pipeline: structured logs from services → Loki; add Grafana panels to view correlated logs.
    
    **Deliverables:**
    
    - Instrumented services emitting metrics.
    - Prometheus + Grafana + Loki deployed and reachable.
    - 3+ Grafana dashboards (app health, ETL, DB).
    
    **Acceptance criteria:**
    
    - Metrics scraped by Prometheus and visible in Grafana.
    - Log entries show up in Loki and are queryable.
    - Dashboards display meaningful, up-to-date charts.
    
    **SLI/SLO groundwork (start):**
    
    - Define SLIs: request success rate, request latency distribution, ETL job success.
    - Draft SLO targets (example: 99.5% availability; 95% of requests under 500ms) — finalize in Week 4.
    
    ---
    
    ## Week 4 — Reliability: Chaos, Retry/Fallbacks, Alerting & Incident Practice
    
    **Goal:** Validate resilience (chaos experiments + retries), implement alerting, and run an incident simulation + postmortem.
    
    **Day-by-day:**
    
    - **Day 1:** Implement resilience patterns:
        - Retry with exponential backoff for Jikan calls in ETL and API.
        - Timeouts and circuit-breaker behavior (logical, not necessarily a library if you prefer).
        - Graceful fallback to cached snapshots when external API is slow/down.
    - **Day 2:** Integrate Prometheus Alertmanager and hook it to Slack (or email). Add alert rules:
        - High error rate (e.g., error rate > 1% for 5m).
        - Latency (p95 > 800ms for 5m).
        - ETL failures (2 consecutive failures).
        - Cache hit ratio drops below threshold.
    - **Day 3:** Design chaos experiments (start simple):
        - Simulate Jikan high-latency (inject delay) and verify fallback to cache.
        - Simulate Jikan 5xx errors and verify retries + circuit breaker.
        - Simulate Redis outage and validate graceful degradation (serve DB).
    - **Day 4:** Run a scheduled chaos window, observe alerts and dashboards.
    - **Day 5:** Conduct a simulated incident (inject failure), document timeline, produce a postmortem.
    
    **Deliverables:**
    
    - Retry & fallback logic implemented.
    - Alertmanager rules + Slack alerts configured.
    - Chaos experiment logs + runbook entries.
    - One simulated incident postmortem with timeline & follow-ups.
    
    **Acceptance criteria:**
    
    - Alerts fire in Slack when thresholds breached during chaos tests.
    - System recovers as expected (fallbacks engaged; ETL resumes).
    - Postmortem includes root cause hypothesis, mitigation, action items.
    
    **Incident / Postmortem template (use immediately):**
    
    - Incident title & short summary
    - Timeline (timestamps) — detection to resolution
    - Impact (who/what affected)
    - Root cause analysis
    - Mitigations taken
    - Action items (owner + due date)
    - Lessons learned
    
    ---
    
    ## Week 5 — Infra & Security Hardening (IaC, Secrets, Deployment Strategies)
    
    **Goal:** Move infra to IaC, add secrets management, and implement safer deployment patterns.
    
    **Day-by-day:**
    
    - **Day 1:** Terraform scripts for cloud infra (managed Postgres, Redis if using cloud).
    - **Day 2:** Helm charts for app; add values for staging/production.
    - **Day 3:** Secrets management: Vault or SealedSecrets/Kubernetes Secrets; remove plaintext secrets.
    - **Day 4:** Add TLS via cert-manager or managed LB certs; enforce HTTPS.
    - **Day 5:** Add safer deploy patterns: blue/green or canary and automated rollback on failed health checks.
    
    **Deliverables:**
    
    - Terraform + Helm artifacts in repo.
    - Secrets management approach in place.
    - Canary/blue-green deployment configured.
    
    **Acceptance criteria:**
    
    - Infrastructure can be provisioned reproducibly.
    - Secrets are not stored in plaintext in repo.
    - Canary deploy works and rollbacks proven in a test.
    
    ---
    
    ## Week 6 — Polish, Documentation, Portfolio & Interview Prep
    
    **Goal:** Finish docs, create visual assets, finalize repo, and prepare talking points for interviews.
    
    **Day-by-day:**
    
    - **Day 1:** Finalize README with architecture diagram, setup instructions for both Docker Compose and Kubernetes.
    - **Day 2:** Write SLO/SLI docs (formalize targets and measurement method); include error budget policy.
    - **Day 3:** Write incident response playbook and runbook for common alerts.
    - **Day 4:** Capture screenshots/GIFs of dashboards, alert flow, and test run results.
    - **Day 5:** Prepare a 1–2 page “project brief” for portfolio + 5 interview bullets: design decisions, failures & learnings, metrics you track, how you tested resilience, what you’d build next.
    
    **Deliverables:**
    
    - Complete README + architecture and SLO docs.
    - Postmortem and runbook artifacts.
    - Visual assets and “project brief” ready for portfolio.
    
    **Acceptance criteria:**
    
    - A reviewer can follow README to stand up the project in dev/staging.
    - SLOs and incident docs present and clear.
    - Portfolio assets available.
    
    ---
    
    ## Testing & CI specifics (summary)
    
    - **Unit tests:** transform functions, aggregation logic, schema validation, retry/backoff logic, small helpers. Fast, isolated.
    - **Integration tests:** run against disposable Postgres + Redis; validate ETL inserts, API responses, cache behavior.
    - **CI flow:**
        - PR: lint → static analysis → unit tests.
        - Merge to main: integration tests (docker-compose/testcontainers) → build images → deploy to staging.
        - Staging: run smoke tests and optional load tests.
    - **Test targets:** unit coverage ≥ 70%; critical integration tests must pass.
    
    ---
    
    ## SLOs, Alerts & Runbook snippets
    
    **Example SLIs / SLOs:**
    
    - Request success rate to analytics endpoints: SLO 99.5% (30-day window).
    - Latency: SLO 95% requests < 500ms.
    - ETL job: SLO 99% success (daily jobs).
    
    **Alert rules (examples):**
    
    - Error rate > 1% for 5 minutes → P2 alert to Slack #oncall.
    - p95 latency > 800ms for 5 minutes → P2 alert.
    - ETL job fails 2 consecutive runs → P1 alert.
    - Disk/DB connection pool > 85% → P1 alert.
    
    **Runbook excerpt for ETL failure:**
    
    1. Check ETL job logs in Loki → note error.
    2. Check Jikan availability (curl to a known endpoint), check for 5xx / latency.
    3. If Jikan down → mark incident, increase ETL backoff, spray alert, enable cached data serve mode.
    4. If DB error → scale DB or investigate connections; failover if configured.
    
    ---
    
    ## Mini Risk Register
    
    - Jikan outages / rate limits → mitigate with caching, backoff, daily snapshots.
    - Data drift / schema changes → add schema validation & migration plan.
    - False alerts / noisy monitoring → tune thresholds and use alert suppression windows.
    - Secrets leakage → use Vault/sealed-secrets; rotate creds.