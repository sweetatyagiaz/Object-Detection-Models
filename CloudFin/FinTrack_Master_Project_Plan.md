# FinTrack --- Product, Architecture & End-to-End Development Plan

**Document type:** Master Project Plan\
**Project:** FinTrack\
**Version:** 1.0\
**Status:** Proposed baseline for execution\
**Planning horizon:** 47 weeks\
**Delivery model:** Agile, 24 sprints (Sprint 0--23)\
**Sprint cadence:** Two weeks, except Sprint 0 (one week)

------------------------------------------------------------------------

## Document control

  -----------------------------------------------------------------------
  Field                               Value
  ----------------------------------- -----------------------------------
  Project                             FinTrack

  Document owner                      FinTrack Product / Engineering

  Architecture                        Next.js + Django + PostgreSQL

  Cache and task broker               Redis

  Background processing               Celery

  Deployment baseline                 Ubuntu + Docker Compose + Nginx

  Future deployment direction         Cloud-ready, without requiring an
                                      initial Kubernetes deployment

  Primary market focus                Indian financial markets, with an
                                      extensible international-market
                                      model

  Planning status                     Baseline plan; detailed sprint
                                      backlogs are approved incrementally
  -----------------------------------------------------------------------

## 1. Executive summary

FinTrack is a financial information, research and investment analytics
platform. It will bring together market information, company
fundamentals, historical prices, corporate actions, mutual fund data,
financial news, research material, portfolio tracking, stock screening
and quantitative strategy analysis.

The platform will be developed as a greenfield application. The frontend
and backend will be independently deployable applications in a monorepo:

-   **Frontend:** Next.js, React and TypeScript.
-   **Backend:** Django modular monolith, exposed through versioned
    APIs.
-   **Database:** PostgreSQL.
-   **Cache and task broker:** Redis.
-   **Background processing:** Celery workers and scheduled tasks.
-   **Real-time communication:** Django Channels/WebSockets where
    justified.
-   **Ingestion:** A separately managed ingestion application/runtime
    that uses shared domain contracts and writes validated canonical
    data through controlled services.
-   **Initial deployment:** Docker Compose on Ubuntu, behind Nginx.
-   **Future deployment:** Cloud-ready services and infrastructure,
    introduced when scale and operational needs justify them.

The project is planned as 24 sprints over approximately 47 weeks. The
plan deliberately establishes the platform foundation before building
the financial domains, then delivers the data platform, user-facing
research experience, investment analytics, production hardening and
launch.

## 2. Product vision and objectives

### 2.1 Vision

Provide a reliable and extensible platform where users can explore
financial markets, research companies and funds, analyze historical and
fundamental data, monitor portfolios and evaluate investment strategies.

### 2.2 Product objectives

1.  Establish a consistent and auditable financial data foundation.
2.  Provide clear market, equity, mutual fund and research experiences.
3.  Offer accurate financial statements and derived metrics.
4.  Provide interactive historical charts and technical indicators.
5.  Enable watchlists, portfolios, alerts and screening.
6.  Support repeatable quantitative research and backtesting.
7.  Make data lineage, source provenance and validation visible to
    operators.
8.  Build a maintainable system that can scale beyond the initial
    self-hosted deployment.

### 2.3 Non-goals for the initial release

The following should not delay v1.0 unless explicitly promoted into
scope:

-   Building a high-frequency trading or order-execution platform.
-   Providing investment advice or guaranteed-return recommendations.
-   Replacing licensed exchange or institutional market-data
    infrastructure.
-   Launching a complex microservice architecture before there is a
    demonstrated need.
-   Deploying Kubernetes solely for the initial release.
-   Building a general-purpose AI agent before the core financial data
    and workflows are dependable.

## 3. Product scope

### 3.1 Core product modules

  -----------------------------------------------------------------------
  Domain                              Main capabilities
  ----------------------------------- -----------------------------------
  Accounts                            Registration, login, profiles,
                                      sessions and access control

  Organizations and permissions       Roles, permissions and
                                      administrative boundaries where
                                      required

  Instruments and markets             Companies, instruments, exchanges,
                                      identifiers, sectors and industries

  Equities                            Company profiles, prices,
                                      fundamentals, ownership and events

  Market data                         Quotes, historical OHLCV, market
                                      breadth and index data

  Corporate actions                   Dividends, splits, bonus issues,
                                      rights issues and name/symbol
                                      changes

  Fundamentals                        Annual/quarterly statements,
                                      consolidated/standalone data and
                                      ratios

  Mutual funds                        AMC, schemes, NAV, AUM, holdings,
                                      allocation and risk metrics

  News                                Sources, articles, company mapping,
                                      classification and search

  Research                            Notes, reports, recommendations and
                                      company analysis

  Watchlists                          User-defined instrument collections

  Portfolio                           Holdings, transactions, valuation,
                                      returns and allocation

  Screeners                           Configurable fundamental and
                                      technical filters

  Analytics                           Returns, volatility, risk and
                                      comparative analytics

  Quant research                      Factors, strategy experiments,
                                      backtesting and rebalancing

  Alerts                              Price, technical, corporate-event
                                      and news notifications

  Data sources and ingestion          Connectors, raw data,
                                      normalization, validation and job
                                      monitoring

  Audit and administration            Operational visibility, change
                                      history and controlled management
  -----------------------------------------------------------------------

### 3.2 Public and authenticated experiences

**Public-facing experience** may include market overview,
instrument/company pages, public financial data, mutual fund
information, news and research content, subject to licensing and product
access rules.

**Authenticated experience** may include personalized dashboards,
watchlists, portfolios, saved screeners, alerts, user research notes and
preferences.

The exact access policy for each endpoint and page must be recorded in
the product requirements and enforced by the backend, not only hidden in
the frontend.

## 4. Architecture baseline

### 4.1 High-level architecture

``` text
                         Users / Browsers
                                |
                         HTTPS / Nginx
                                |
                    Next.js Web Application
                                |
                         Versioned REST API
                                |
                    Django Modular Monolith
             ___________________|___________________
            |          |          |        |         |
         Domain     Services   Selectors  Tasks    Admin
         Modules       |          |        |
            |          |          |      Celery
            |          |          |        |
            |       PostgreSQL    |      Redis
            |____________________|        |
                                           |
                                  Background workers

External data providers
        |
   Ingestion runtime
        |
 Connectors / Parsers
        |
 Immutable raw data
        |
 Normalize / Validate / Deduplicate
        |
 Controlled canonical-data services
        |
 PostgreSQL / Object storage
```

### 4.2 Architectural principles

-   Use a **modular monolith** for the Django application. Keep domain
    boundaries explicit without prematurely splitting services.
-   Keep Next.js independently deployable and communicate with Django
    through documented APIs.
-   Treat PostgreSQL as the system of record for canonical relational
    data.
-   Use Redis for caching, task brokering and other bounded ephemeral
    workloads.
-   Use Celery for long-running and scheduled jobs.
-   Use WebSockets only for experiences that need push updates; ordinary
    data retrieval should remain request/response.
-   Keep ingestion connectors separate from canonical domain
    persistence.
-   Preserve raw source data and provenance so normalized records can be
    audited and reprocessed.
-   Keep financial calculations in reusable backend/analytics services
    rather than duplicating business logic in UI components.
-   Keep all production secrets outside source control.
-   Make services observable through structured logs, metrics, health
    checks and operational status.

### 4.3 Technology baseline

  -----------------------------------------------------------------------
  Layer                               Proposed technology
  ----------------------------------- -----------------------------------
  Frontend                            Next.js, React, TypeScript

  UI                                  Tailwind CSS, shadcn/ui and
                                      accessible Radix primitives

  Frontend data                       TanStack Query

  Tables                              TanStack Table

  Local UI state                      Zustand where shared client state
                                      is needed

  Forms and validation                React Hook Form and Zod

  Charts                              Highcharts Stock, ECharts and/or
                                      Lightweight Charts after feature
                                      and licensing review

  Backend                             Django and Django REST Framework

  API schema                          drf-spectacular / OpenAPI

  Database                            PostgreSQL

  Cache / broker                      Redis

  Background jobs                     Celery and Celery Beat

  Real-time                           Django Channels where required

  Analytics                           Python, NumPy, Pandas, Polars,
                                      SciPy and scikit-learn as
                                      appropriate

  Ingestion                           HTTP clients, BeautifulSoup, lxml,
                                      CSV/Excel parsers and Playwright
                                      where justified

  Deployment                          Docker, Docker Compose, Nginx and
                                      Ubuntu

  Backend testing                     pytest, pytest-django, factory-boy

  Frontend testing                    Vitest, Testing Library and
                                      Playwright

  Quality and security                Ruff, mypy where useful, Bandit,
                                      pip-audit and npm audit
  -----------------------------------------------------------------------

**Version policy:** Versions listed in implementation manifests must be
checked for compatibility at the time of implementation, locked and
updated through controlled dependency changes. Do not assume that a
major version mentioned in planning is automatically the correct
production version.

**Licensing policy:** Review commercial terms and redistribution rights
for charting libraries and financial data providers before production
use.

### 4.4 Repository structure

``` text
FinTrack/
├── apps/
│   ├── web/                       # Next.js frontend
│   ├── api/                       # Django backend
│   └── ingestion/                 # Data ingestion runtime
├── packages/
│   ├── api-contracts/             # Shared API schemas/types
│   ├── ui/                        # Shared UI components, if needed
│   └── shared-config/             # Shared lint/build configuration
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   ├── postgres/
│   ├── redis/
│   ├── monitoring/
│   └── deployment/
│       ├── self-hosted/
│       └── cloud/
├── scripts/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── development/
│   ├── deployment/
│   ├── operations/
│   └── adr/
├── .github/
│   └── workflows/
├── .env.example
├── Makefile
└── README.md
```

The exact folder layout can evolve, but changes should be documented and
should preserve clear ownership of the frontend, API and ingestion
runtime.

### 4.5 Backend domain application pattern

A Django domain application should use a consistent internal layout
where it adds clarity:

``` text
domain_app/
├── models/
├── api/
│   ├── serializers/
│   ├── views/
│   ├── urls.py
│   └── filters/
├── services/
├── selectors/
├── tasks.py
├── admin.py
├── migrations/
└── tests/
```

-   **models:** Persistence and domain constraints.
-   **services:** Business operations and write workflows.
-   **selectors:** Read/query logic.
-   **api:** Request/response contracts and HTTP behavior.
-   **tasks:** Background execution entry points.
-   **tests:** Unit, integration and API tests.

Avoid placing complex financial calculations directly in views,
serializers or model properties.

### 4.6 Frontend route organization

``` text
apps/web/
└── src/
    ├── app/
    │   ├── (public)/
    │   │   ├── markets/
    │   │   ├── equities/[slug]/
    │   │   ├── mutual-funds/
    │   │   ├── indices/
    │   │   ├── commodities/
    │   │   ├── news/
    │   │   └── research/
    │   └── (dashboard)/
    │       ├── dashboard/
    │       ├── portfolio/
    │       ├── watchlists/
    │       ├── screeners/
    │       ├── analytics/
    │       └── settings/
    ├── features/
    ├── components/
    ├── lib/
    ├── hooks/
    └── types/
```

Use feature-oriented components and API hooks. Keep shared visual
primitives separate from domain-specific financial components.

## 5. Data architecture and financial data governance

### 5.1 Identity model

Use internal UUIDs for canonical company and instrument identities. Do
not use exchange tickers as permanent primary keys.

Distinguish:

-   **Company:** The legal or operating company.
-   **Instrument:** A tradable security or financial instrument.
-   **Listing:** The instrument's listing on a specific exchange/market.
-   **Identifier:** Exchange-specific code, symbol, ISIN or other
    identifier.
-   **Alias/history:** Historical names, symbols and identifiers with
    effective dates.

This supports multiple listings, symbol changes, delistings and
historical data reconciliation.

### 5.2 Financial observations

Financial observations should preserve, as applicable:

-   Company/instrument identity.
-   Financial particular or metric.
-   Period start and end.
-   Annual or quarterly period type.
-   Consolidated or standalone category.
-   Currency and scale/unit.
-   Decimal value.
-   Source and source record identifier.
-   Publication/availability date.
-   Ingestion timestamp.
-   Revision/version information.

Store financial values using appropriate decimal types rather than
binary floating point.

### 5.3 Market price data

OHLCV data should define:

-   Instrument and exchange/listing.
-   Timestamp and interval.
-   Open, high, low and close.
-   Adjusted close where supported by the source and methodology.
-   Volume.
-   Currency.
-   Source and ingestion metadata.

Keep raw/unadjusted prices conceptually separate from
corporate-action-adjusted series. Document the adjustment methodology
and avoid applying adjustments twice.

### 5.4 Provenance and raw data

For externally sourced information, preserve:

-   Provider/source.
-   Retrieval timestamp.
-   Source publication date, if available.
-   Original URL or provider identifier where permitted.
-   Raw payload or durable raw-file reference.
-   Parser/connector version.
-   Validation outcome.
-   Normalization version.
-   Ingestion job/run identifier.

Raw data should be immutable or versioned. Reprocessing should create
traceable new canonical outcomes rather than silently destroying source
evidence.

### 5.5 Ingestion lifecycle

``` text
External Provider
      |
Connector / Retrieval
      |
Raw Payload Storage
      |
Parsing
      |
Normalization
      |
Validation
      |
Deduplication / Reconciliation
      |
Canonical Domain Service
      |
PostgreSQL
      |
Analytics / API / Frontend
```

Scrapers and connectors must not bypass validation and write directly
into production canonical tables.

### 5.6 Data quality controls

Implement controls for:

-   Missing required fields.
-   Invalid symbols and identifiers.
-   Duplicate observations.
-   Impossible OHLC relationships.
-   Invalid or negative values where prohibited by the metric.
-   Currency and unit mismatches.
-   Period overlap and duplicate financial filings.
-   Corporate action consistency.
-   Stale data.
-   Unexpected source changes.
-   Outlier values requiring review.

Data-quality failures should be visible to operators and should not be
silently converted into apparently valid records.

### 5.7 Time and market calendars

Store timestamps in UTC where appropriate. Interpret Indian market
sessions and dates using `Asia/Kolkata`. Use exchange calendars and
trading sessions rather than assuming every weekday is a trading day.

### 5.8 Database performance

Start with PostgreSQL and standard indexing:

-   B-tree indexes for common equality/range lookups.
-   Partial indexes for selective subsets.
-   GIN indexes where JSON or text search requires them.
-   Appropriate composite indexes based on query patterns.
-   Partitioning or materialized views only after measuring workload.

TimescaleDB is optional. Evaluate its current PostgreSQL compatibility,
operational implications and actual workload benefit before adopting it.

## 6. API and security standards

### 6.1 API conventions

-   Use a versioned namespace such as `/api/v1/`.
-   Document request and response schemas using OpenAPI.
-   Standardize pagination, filtering, sorting and error responses.
-   Validate all incoming data at the API boundary.
-   Apply authorization on the backend for every protected resource.
-   Avoid exposing internal database structures as public API contracts.
-   Maintain backward compatibility or version changes deliberately.

Example endpoint families:

``` text
/api/v1/auth/
/api/v1/users/
/api/v1/markets/
/api/v1/instruments/
/api/v1/equities/
/api/v1/fundamentals/
/api/v1/corporate-actions/
/api/v1/mutual-funds/
/api/v1/indices/
/api/v1/commodities/
/api/v1/news/
/api/v1/research/
/api/v1/portfolio/
/api/v1/watchlists/
/api/v1/screeners/
/api/v1/analytics/
/api/v1/alerts/
/api/v1/ingestion/
```

### 6.2 Authentication and authorization

Use secure, server-managed authentication. Prefer HttpOnly, Secure
cookies with an appropriate CSRF strategy for browser sessions. Do not
store long-lived authentication secrets in browser localStorage.

Implement:

-   Password hashing using Django-supported secure defaults.
-   Session lifecycle and logout invalidation.
-   CSRF protection.
-   Rate limits for sensitive endpoints.
-   Role and permission checks.
-   Administrative access restrictions.
-   Audit events for sensitive actions.
-   Account recovery and password reset controls.

Choose token-based authentication only when a clearly defined client or
integration requirement justifies it; do not add a token package by
default without an architecture decision.

### 6.3 Security baseline

-   HTTPS in production.
-   Secrets supplied through environment/secrets management.
-   Database and Redis not publicly exposed.
-   Least-privilege service credentials.
-   Dependency and container scanning.
-   Input validation and output encoding.
-   Safe file upload handling.
-   Audit logging.
-   Regular backups and tested restoration.
-   Security review before release.

## 7. Detailed sprint plan

The baseline schedule is 47 weeks: Sprint 0 is one week and Sprint 1--23
are two weeks each.

### Stage 0 --- Planning and architecture (Week 1)

#### Sprint 0 --- Product definition and technical design

**Goal:** Agree on the product scope, architecture and execution
baseline.

  ID      Work item                            Expected output
  ------- ------------------------------------ -------------------------------
  S0-01   Define product requirements          Product Requirements Document
  S0-02   Finalize functional modules          Module specification
  S0-03   Finalize system architecture         Architecture document
  S0-04   Define repository structure          Repository specification
  S0-05   Define financial domain boundaries   Domain map
  S0-06   Design initial data model            ERD draft
  S0-07   Define API conventions               API standards
  S0-08   Define coding standards              Engineering guidelines
  S0-09   Define testing strategy              QA strategy
  S0-10   Create prioritized backlog           Initial backlog

**Acceptance criteria**

-   Product scope and non-goals documented.
-   Frontend/backend/ingestion boundaries agreed.
-   Initial ERD reviewed.
-   Architecture Decision Records (ADRs) created.
-   Initial backlog prioritized and dependencies identified.

**Milestone M0:** Planning and architecture approved.

### Stage 1 --- Platform foundation (Weeks 2--7)

#### Sprint 1 --- Repository and development environment

**Goal:** Establish the monorepo and consistent developer tooling.

Work items:

-   Create the Git repository and branch strategy.
-   Create the root directory structure.
-   Add `.gitignore`, `.env.example` and README.
-   Configure Python environment and dependency management.
-   Configure Node.js package management.
-   Configure Ruff, ESLint and TypeScript.
-   Create the root Makefile and common scripts.
-   Establish code review and commit conventions.
-   Create initial architecture and development documentation.

**Deliverables:** Repository skeleton, development setup guide and
quality-tool configuration.

**Acceptance criteria:** A clean checkout can be configured from
documented instructions without relying on untracked local files.

#### Sprint 2 --- Infrastructure bootstrap

**Goal:** Run the application components locally and through Docker
Compose.

Work items:

-   Bootstrap Next.js frontend.
-   Bootstrap Django backend.
-   Configure PostgreSQL.
-   Configure Redis.
-   Create development Dockerfiles.
-   Create Docker Compose services and networks.
-   Configure Nginx for local integration where appropriate.
-   Add service health checks.
-   Configure structured logging.
-   Add backend and frontend smoke tests.

**Acceptance criteria**

-   Frontend is available on port 3000.
-   Backend is available on port 8000.
-   PostgreSQL and Redis connections succeed.
-   Compose starts the required services.
-   Health checks and smoke tests pass.

#### Sprint 3 --- Authentication and application foundation

**Goal:** Implement the initial identity, permissions and API
foundation.

Work items:

-   Define and create the custom Django user model before initial
    migrations.
-   Implement registration, login and logout.
-   Implement password reset.
-   Implement user profile.
-   Configure session and CSRF behavior.
-   Implement initial role and permission model.
-   Configure Django Admin.
-   Configure DRF and OpenAPI documentation.
-   Configure CORS and trusted origins.
-   Add audit logging for sensitive account actions.
-   Add authentication and permission tests.

**Acceptance criteria**

-   Users can register and authenticate.
-   Logout invalidates the session.
-   Protected endpoints enforce permissions.
-   CSRF behavior is verified.
-   Admin access is restricted appropriately.
-   API schema is generated and accessible.

**Milestone M1:** Platform foundation complete.

### Stage 2 --- Core financial backend (Weeks 8--19)

#### Sprint 4 --- Financial master data

**Goal:** Establish canonical company, instrument and market identities.

Work items:

-   Exchange and market masters.
-   Sector and industry masters.
-   Company master.
-   Instrument master.
-   Exchange-specific listings and identifiers.
-   ISIN and other identifier support where available.
-   Instrument aliases and historical symbols.
-   Company/instrument relationships.
-   Search and lookup services.
-   Admin management and integrity tests.

**Acceptance criteria**

-   A company can be related to multiple instruments/listings.
-   Instrument identity is independent of ticker text.
-   Symbol changes can be represented historically.
-   Unique constraints prevent conflicting identities.
-   Search supports company name, symbol and exchange.

#### Sprint 5 --- Market data foundation and corporate actions

**Goal:** Define reliable market and event persistence.

Work items:

-   Trading calendar and sessions.
-   Market holiday data.
-   OHLCV schema.
-   Quote schema where required.
-   Dividends.
-   Splits.
-   Bonus issues.
-   Rights issues.
-   Name and code changes.
-   Delisting events.
-   Corporate-action adjustment rules.
-   API and validation tests.

**Acceptance criteria**

-   Historical prices can be queried by instrument, exchange, period and
    interval.
-   Corporate actions are independently stored.
-   Raw and adjusted price semantics are documented.
-   Duplicate market bars are prevented.

#### Sprint 6 --- Data ingestion framework

**Goal:** Create a reusable, observable and testable ingestion pipeline.

Work items:

-   Data-source registry.
-   Connector contracts and base classes.
-   HTTP retrieval.
-   CSV and Excel parsers.
-   HTML parser.
-   Playwright connector for justified dynamic pages.
-   Raw payload storage.
-   Job/run records.
-   Retry and timeout policies.
-   Normalization framework.
-   Validation framework.
-   Deduplication utilities.
-   Celery worker integration.
-   Operator-facing job status.

**Acceptance criteria**

-   Jobs can be started asynchronously.
-   Each run records source, status and timing.
-   Raw data is retained or referenced durably.
-   Retry behavior is bounded.
-   Invalid records are quarantined or reported.
-   Duplicate ingestion does not create duplicate canonical records.

#### Sprint 7 --- Historical market data

**Goal:** Ingest and reconcile historical market prices.

Work items:

-   NSE historical data connector, subject to source access and terms.
-   BSE historical data connector, subject to source access and terms.
-   Yahoo Finance connector where permitted and suitable.
-   Daily bhavcopy ingestion.
-   Historical OHLCV normalization.
-   Exchange calendar alignment.
-   Duplicate and missing-bar checks.
-   Data reconciliation reports.
-   Historical price API.
-   Query and index optimization.
-   Evaluate TimescaleDB only against measured needs and current
    compatibility.

**Acceptance criteria**

-   Selected instruments have queryable historical data.
-   Duplicate bars are prevented.
-   Missing data is measurable.
-   Source and retrieval provenance are retained.
-   Historical queries meet agreed response-time targets.

#### Sprint 8 --- Financial fundamentals

**Goal:** Implement financial statement storage and normalized
fundamental metrics.

Work items:

-   Financial particulars master.
-   Annual statements.
-   Quarterly statements.
-   Consolidated and standalone categories.
-   Profit and loss.
-   Balance sheet.
-   Cash flow.
-   Financial observation model.
-   Unit and currency normalization.
-   Financial ratio services.
-   Growth and CAGR metrics.
-   Filing/publication dates and revisions.
-   Fundamental APIs and tests.

**Acceptance criteria**

-   Annual and quarterly data are supported.
-   Consolidated and standalone values remain distinct.
-   Units and currencies are explicit.
-   Revisions and provenance are traceable.
-   Ratio calculations have reference tests.

#### Sprint 9 --- Mutual funds, news and research

**Goal:** Establish remaining core research data domains.

Mutual funds:

-   AMC master and scheme master.
-   NAV history.
-   Fund category and classification.
-   AUM history.
-   Portfolio holdings.
-   Sector and asset allocation.
-   Portfolio snapshots.
-   Risk metrics and rating fields where licensed.

News:

-   Source registry.
-   Article retrieval and parsing.
-   Article deduplication.
-   Company/instrument mapping.
-   Classification and keyword extraction.
-   Search and filtering.
-   Source attribution and publication timestamps.

Research:

-   Research notes.
-   Research reports.
-   Recommendations and rating history where appropriate.
-   Company pros and cons.
-   Document metadata and access controls.

**Acceptance criteria**

-   Fund schemes and NAV histories are queryable.
-   Holdings have as-of dates and source provenance.
-   News articles can be mapped to companies.
-   Research content is managed with appropriate permissions.
-   Ingestion failures are visible.

**Milestone M2:** Core financial backend foundation complete.

### Stage 3 --- Frontend development (Weeks 20--31)

#### Sprint 10 --- Design system and application shell

**Goal:** Create the reusable visual foundation.

Work items:

-   Design tokens and typography.
-   Color and theme system.
-   Responsive layout.
-   Header, navigation and footer.
-   Sidebar and user menu.
-   Search interface.
-   Reusable cards and data tables.
-   Form controls and dialogs.
-   Loading, empty and error states.
-   Accessibility and keyboard behavior.
-   Shared API client and error handling.

**Acceptance criteria:** Public and authenticated shells render
responsively and shared components follow consistent design rules.

#### Sprint 11 --- Market dashboard

**Goal:** Deliver a useful market overview.

Work items:

-   Market summary.
-   Major indices.
-   Nifty and Sensex views.
-   Gainers and losers.
-   Volume leaders.
-   Sector performance.
-   Market breadth.
-   News highlights.
-   Market activity.
-   Date and market-session context.
-   Loading and stale-data indicators.

**Acceptance criteria:** Dashboard values come from backend APIs, show
source/update context where available and handle unavailable data
clearly.

#### Sprint 12 --- Equity research interface

**Goal:** Build the company/instrument research experience.

Work items:

-   Company overview.
-   Instrument and exchange details.
-   Current/historical price summary.
-   Key financial metrics.
-   Market capitalization.
-   Sector and industry information.
-   Ownership and shareholding.
-   Insider transactions.
-   Corporate events.
-   News and research links.
-   Company pros and cons.

Suggested route structure:

``` text
/equities/[slug]/
/equities/[slug]/financials
/equities/[slug]/technicals
/equities/[slug]/shareholding
/equities/[slug]/ownership
/equities/[slug]/insider-trading
/equities/[slug]/corporate-actions
/equities/[slug]/news
/equities/[slug]/research
```

**Acceptance criteria:** Company pages use stable internal identity, not
only ticker text, and all sections handle missing data gracefully.

#### Sprint 13 --- Financial statements and company analytics

**Goal:** Deliver financial statement exploration.

Work items:

-   Profit and loss statement.
-   Balance sheet.
-   Cash flow statement.
-   Annual/quarterly switch.
-   Consolidated/standalone switch.
-   Financial ratio table.
-   Growth and CAGR analysis.
-   Peer comparison.
-   Units and period labels.
-   Export functionality.
-   API pagination and filtering where required.

**Acceptance criteria:** Values, units, periods and statement categories
match backend records and reference test fixtures.

#### Sprint 14 --- Stock charts and technical analysis

**Goal:** Deliver interactive charting.

Work items:

-   Candlestick and line chart modes.
-   Volume subplot.
-   Close-price default view.
-   Range selector.
-   Date range control.
-   SMA and EMA.
-   RSI and MACD.
-   Bollinger Bands.
-   SuperTrend.
-   Buy/sell markers.
-   Percentage and logarithmic axes.
-   Dynamic y-axis bounds.
-   Theme switching.
-   Chart export.
-   Parameter controls.
-   Loading and missing-data states.

Proposed range options:

``` text
5D | 1M | 3M | 6M | YTD | 1Y | 3Y | 5Y | 10Y | FULL
```

**Acceptance criteria**

-   Close price and volume are visible by default.
-   Additional indicators are opt-in.
-   Indicators are calculated consistently and independently.
-   The selected range controls displayed data and axis scaling.
-   Buy/sell markers are tied to verified indicator events.
-   Chart data is sourced from backend APIs.

#### Sprint 15 --- Mutual funds and research interface

**Goal:** Complete core research-facing pages.

Work items:

-   Fund listing and filters.
-   Fund detail page.
-   NAV history chart.
-   Performance and benchmark comparison.
-   Risk metrics.
-   Ratings where licensed.
-   Holdings and sector allocation.
-   Fund comparison.
-   News listing and detail.
-   Research report listing and detail.
-   User research notes.

**Acceptance criteria:** Fund and research interfaces are responsive,
API-driven and show as-of dates and source context where available.

**Milestone M3:** Core financial website complete.

### Stage 4 --- Investment and analytics (Weeks 32--39)

#### Sprint 16 --- Portfolio management

**Goal:** Deliver personal portfolio tracking.

Work items:

-   Portfolio creation and management.
-   Buy/sell transaction ledger.
-   Holdings derived from transactions.
-   Average cost methodology.
-   Realized profit/loss.
-   Unrealized profit/loss.
-   Current valuation.
-   Portfolio performance.
-   Asset and sector allocation.
-   Benchmark comparison.
-   Historical portfolio snapshots.
-   Transaction correction and audit behavior.

**Acceptance criteria**

-   Calculations are based on a documented transaction/cost methodology.
-   Corporate actions are handled consistently.
-   Realized and unrealized P&L are independently tested.
-   Portfolio history can be reproduced from its transaction ledger.

#### Sprint 17 --- Stock screening engine

**Goal:** Build configurable stock discovery.

Work items:

-   Fundamental filters.
-   Technical filters.
-   Valuation filters.
-   Growth and profitability filters.
-   Market capitalization filters.
-   Sector and industry filters.
-   Filter composition.
-   Saved screens.
-   Result sorting and pagination.
-   Export.
-   Query safety and execution limits.

Example screening criteria:

``` text
Market Capitalization > configured threshold
ROE > configured threshold
ROCE > configured threshold
Debt / Equity < configured threshold
Revenue Growth > configured threshold
Profit Growth > configured threshold
```

**Acceptance criteria**

-   Users can combine supported filters.
-   Saved screens can be re-executed.
-   Results show the data date/as-of context.
-   Filters are evaluated against documented metric definitions.

#### Sprint 18 --- Financial analytics and risk engine

**Goal:** Provide reusable analytical services.

Work items:

-   CAGR.
-   Period and rolling returns.
-   Volatility.
-   Sharpe ratio.
-   Sortino ratio.
-   Maximum drawdown.
-   Beta and alpha.
-   Correlation.
-   Portfolio risk.
-   Sector exposure.
-   Fund risk metrics.
-   Benchmark comparison.
-   Metric definitions and reference tests.

**Acceptance criteria**

-   Calculation assumptions are documented.
-   Annualization and risk-free-rate conventions are explicit.
-   Missing-data behavior is defined.
-   Outputs match independently calculated test fixtures.

#### Sprint 19 --- Quantitative research and backtesting

**Goal:** Establish a reproducible research environment.

Work items:

-   Factor data interface.
-   Momentum and relative-strength strategies.
-   Moving-average strategies.
-   Multi-factor scoring.
-   Portfolio weighting.
-   Rebalancing schedules.
-   Backtesting engine.
-   Transaction costs and slippage.
-   Benchmark comparison.
-   Strategy experiment records.
-   Walk-forward and out-of-sample evaluation.
-   Result comparison and export.

**Acceptance criteria**

-   No look-ahead leakage.
-   Survivorship bias is considered and documented.
-   Corporate actions and delisted securities are handled according to
    the selected dataset/methodology.
-   Transaction costs and slippage are configurable.
-   Training/research and evaluation periods are separated.
-   Every experiment records parameters, data window and code/version
    metadata.

**Milestone M4:** Investment analytics complete.

### Stage 5 --- Integration and quality engineering (Weeks 40--43)

#### Sprint 20 --- Alerts, real-time updates and integration

**Goal:** Connect user workflows and event-driven updates.

Work items:

-   Watchlists.
-   Price alerts.
-   Technical alerts.
-   Corporate-event alerts.
-   News alerts.
-   Notification history.
-   Email notifications.
-   WebSocket delivery where needed.
-   Subscription lifecycle.
-   Celery task monitoring.
-   End-to-end integration tests.

**Acceptance criteria**

-   Alert rules are persisted and evaluated predictably.
-   Notifications are not duplicated unintentionally.
-   Users only receive authorized notifications.
-   Disconnections and delivery failures are observable.

#### Sprint 21 --- Performance, security and QA

**Goal:** Prepare the application for production workloads.

Performance:

-   Database query review.
-   Index review.
-   API response optimization.
-   Cache policy review.
-   Frontend performance review.
-   Pagination and large dataset handling.
-   Historical chart query optimization.
-   Worker concurrency and queue tuning.

Security:

-   Authentication and authorization audit.
-   CSRF and CORS verification.
-   SQL injection and XSS checks.
-   File upload review.
-   Dependency scanning.
-   Secrets and configuration review.
-   Administrative access review.

Quality:

-   Backend unit/integration/API tests.
-   Frontend component tests.
-   Browser end-to-end tests.
-   Financial calculation verification.
-   Load and stress tests.
-   Responsive and browser compatibility tests.
-   Backup restoration test.

**Acceptance criteria**

-   No unresolved critical or high-severity security findings.
-   Critical user journeys pass.
-   Financial reference tests pass.
-   Restore procedure is demonstrated.
-   Agreed performance targets are met under the test workload.
-   Release blockers are documented and resolved or formally accepted.

### Stage 6 --- Production release (Weeks 44--45)

#### Sprint 22 --- Production deployment

**Goal:** Deploy FinTrack to the production environment.

Work items:

-   Prepare Ubuntu host.
-   Build production Docker images.
-   Configure Nginx and HTTPS.
-   Configure PostgreSQL and Redis securely.
-   Configure Django application processes.
-   Configure Celery workers and scheduler.
-   Configure static and media/object storage.
-   Configure monitoring and error tracking.
-   Configure automated backups.
-   Configure CI/CD deployment.
-   Apply migrations using a controlled release procedure.
-   Run smoke tests.
-   Validate production data.
-   Publish release notes.

**Acceptance criteria**

-   Production uses secure configuration.
-   Database and Redis are not publicly exposed.
-   HTTPS is operational.
-   Backups are scheduled and restoration has been tested.
-   Health checks, logs and monitoring work.
-   Deployment and rollback procedures are documented.
-   Smoke tests pass.

### Stage 7 --- Stabilization (Weeks 46--47)

#### Sprint 23 --- Hypercare and final acceptance

**Goal:** Stabilize the live release and complete handover.

Work items:

-   Monitor application errors and latency.
-   Monitor database and worker health.
-   Review ingestion failures.
-   Reconcile sampled financial data.
-   Resolve production defects.
-   Optimize identified bottlenecks.
-   Review user feedback.
-   Verify disaster recovery documentation.
-   Complete operational runbooks.
-   Finalize technical and user documentation.
-   Prepare the next-release backlog.

**Acceptance criteria**

-   No unresolved critical release defects.
-   Data integrity checks pass.
-   Monitoring and alerting are active.
-   Backup and recovery procedures are documented and tested.
-   Production deployment is repeatable.
-   Operational ownership and escalation are defined.

**Final milestone:** FinTrack v1.0 accepted.

## 8. Sprint governance

### 8.1 Sprint lifecycle

1.  **Planning:** Confirm the sprint goal, select ready work, estimate
    tasks and identify dependencies.
2.  **Implementation:** Develop in small increments with code review and
    tests.
3.  **Daily progress:** Review completed work, blockers and remaining
    scope.
4.  **Integration:** Merge completed changes and run CI.
5.  **Review:** Demonstrate working outcomes against acceptance
    criteria.
6.  **Retrospective:** Record what worked, what failed and concrete
    improvements.

### 8.2 Task status conventions

  Status        Meaning
  ------------- ---------------------------------------
  BACKLOG       Not scheduled
  READY         Refined and approved for development
  IN_PROGRESS   Work has started
  CODE_REVIEW   Awaiting review
  TESTING       Under verification
  BLOCKED       Waiting on a dependency or resolution
  DONE          Acceptance criteria satisfied

### 8.3 Definition of Ready

A task is ready when:

-   Its purpose and expected outcome are clear.
-   Acceptance criteria are written.
-   Dependencies are identified.
-   API/data contracts are understood where relevant.
-   Required design or source information is available.
-   The task is small enough to complete and verify within a sprint.

### 8.4 Definition of Done

A task is done only when:

-   Implementation is complete.
-   Code review is complete.
-   Relevant tests are written and passing.
-   Security implications have been considered.
-   API and technical documentation are updated.
-   Integration is verified.
-   Acceptance criteria pass.
-   No known critical defect remains in the delivered scope.

### 8.5 Sprint reporting

Each sprint review should report:

-   Sprint goal and outcome.
-   Planned versus completed work.
-   Completed stories and deferred stories.
-   Test results.
-   Defects opened and closed.
-   Security or data-quality concerns.
-   Dependencies and blockers.
-   Technical debt created or resolved.
-   Next sprint readiness.

## 9. Cross-sprint engineering workstreams

These workstreams continue throughout delivery and must not be postponed
until the final release.

  Workstream                         Start      End
  ---------------------------------- ---------- -----------
  Architecture governance and ADRs   Sprint 0   Sprint 23
  Backend testing                    Sprint 1   Sprint 23
  Frontend testing                   Sprint 2   Sprint 23
  Database governance                Sprint 2   Sprint 23
  API documentation                  Sprint 2   Sprint 23
  Data quality                       Sprint 6   Sprint 23
  Security                           Sprint 1   Sprint 23
  Performance                        Sprint 2   Sprint 23
  CI/CD                              Sprint 1   Sprint 23
  Technical documentation            Sprint 0   Sprint 23
  Monitoring and operations          Sprint 2   Sprint 23

## 10. Team and responsibilities

A small cross-functional team can cover the initial scope. Roles may be
combined depending on staffing.

  -----------------------------------------------------------------------
  Role                                Primary responsibilities
  ----------------------------------- -----------------------------------
  Technical lead / architect          Architecture, standards, design
                                      reviews and technical risk

  Backend developer                   Django domains, APIs, permissions
                                      and services

  Data/ingestion developer            Connectors, parsers, validation and
                                      reconciliation

  Frontend developer                  Next.js, design system and
                                      financial interfaces

  QA engineer                         Automated tests, integration and
                                      financial correctness

  DevOps engineer                     Docker, CI/CD, deployment,
                                      monitoring and backups

  Product owner                       Scope, priorities, acceptance and
                                      release decisions
  -----------------------------------------------------------------------

For a solo or very small team, retain the same sequence but revise
duration and scope based on actual capacity. Do not treat the 47-week
plan as a guaranteed solo-developer estimate.

## 11. Release milestones

  -------------------------------------------------------------------------
  Milestone                       Target Release          Scope
  ---------------- --------------------- ---------------- -----------------
  M0                              Week 1 Planning         Requirements,
                                         baseline         architecture and
                                                          backlog

  M1                              Week 7 v0.1             Repository,
                                                          infrastructure,
                                                          authentication
                                                          and API
                                                          foundation

  M2                             Week 19 v0.2             Financial
                                                          backend,
                                                          ingestion and
                                                          core datasets

  M3                             Week 31 Core website     Market, equity,
                                         milestone        fundamentals,
                                                          charts, funds and
                                                          research UI

  M4                             Week 39 v0.8             Portfolio,
                                                          screening, risk
                                                          and quantitative
                                                          research

  M5                             Week 45 v1.0 candidate   Integrated
                                                          production
                                                          deployment

  M6                             Week 47 v1.0 accepted    Stabilized
                                                          release and
                                                          operational
                                                          handover
  -------------------------------------------------------------------------

## 12. Scope prioritization

### Essential for v1.0

-   Secure accounts and access control.
-   Financial master data.
-   Historical market data for supported instruments.
-   Company profiles and equity research.
-   Annual and quarterly financial statements.
-   Corporate actions.
-   Core interactive stock charts.
-   Mutual fund listing, details and NAV history.
-   News and research.
-   Watchlists.
-   Basic portfolio tracking.
-   Fundamental and technical screening.
-   Core financial risk analytics.
-   Defined quantitative backtesting capability.
-   Basic alerts and notifications.
-   Production monitoring, backups and security controls.

### Candidate future enhancements

-   AI-assisted research and summaries.
-   Advanced peer intelligence.
-   Advanced chart drawing and custom indicators.
-   Custom screener scripting.
-   Advanced portfolio optimization.
-   Broader international-market coverage.
-   Advanced strategy optimization and experiment orchestration.
-   Subscription tiers and billing.
-   More sophisticated event intelligence.

Promote future features into v1.0 only through an explicit scope and
schedule decision.

## 13. Data provider, licensing and compliance considerations

Data availability is a project dependency, not an assumption that all
public websites permit unrestricted collection or redistribution.

Before implementing each provider connector:

1.  Identify the authoritative or intended source.
2.  Review terms of use, licensing and redistribution rights.
3.  Confirm whether automated retrieval is permitted.
4.  Identify rate limits and authentication requirements.
5.  Record attribution requirements.
6.  Confirm whether data can be stored historically.
7.  Confirm whether derived data can be displayed or redistributed.
8.  Implement source-specific monitoring and failure handling.

Do not represent delayed or end-of-day data as real-time. Show
timestamps and data status where appropriate. The platform should
distinguish information services and analytics from regulated investment
advice or execution services; obtain appropriate legal/compliance review
before offering regulated functionality.

## 14. Testing strategy

### 14.1 Backend

-   Unit tests for domain services and calculations.
-   Model and constraint tests.
-   API tests for permissions, validation and response contracts.
-   Integration tests for database and Redis behavior.
-   Ingestion connector and parser tests using fixtures.
-   Task retry and failure tests.

### 14.2 Frontend

-   Component tests for reusable UI.
-   Feature tests for financial workflows.
-   API client tests.
-   Accessibility checks.
-   Browser end-to-end tests for critical user journeys.

### 14.3 Financial correctness

Build deterministic reference fixtures for:

-   Price returns and adjusted returns.
-   Corporate actions.
-   Annual and quarterly period handling.
-   Consolidated versus standalone data.
-   Financial ratios.
-   CAGR and rolling returns.
-   Portfolio cost basis and P&L.
-   Volatility and risk metrics.
-   Backtesting timing, transaction costs and rebalancing.
-   Missing observations and market holidays.
-   Timezone and trading-session boundaries.

### 14.4 Performance and security

-   Load-test representative API endpoints.
-   Profile expensive database queries.
-   Test large historical time-series queries.
-   Scan dependencies and containers.
-   Review authorization boundaries.
-   Test backups and restore procedures.

Coverage percentages should be agreed by module and risk. A high
coverage percentage is not a substitute for correct financial reference
tests.

## 15. Deployment and operations

### 15.1 Initial self-hosted deployment

The initial production baseline is Ubuntu with Docker Compose and Nginx.
Keep stateful services persistent and backed up. Do not expose
PostgreSQL or Redis directly to the public internet.

Expected service groups:

-   Nginx/reverse proxy.
-   Next.js web process.
-   Django API process.
-   PostgreSQL.
-   Redis.
-   Celery worker(s).
-   Celery scheduler.
-   Ingestion worker/runtime.
-   Monitoring and log collection as selected.

### 15.2 Cloud-ready direction

The architecture should permit a later migration to managed services,
for example:

-   Container orchestration or managed application runtime.
-   Managed PostgreSQL.
-   Managed Redis.
-   Object storage.
-   CDN.
-   Centralized logs and metrics.
-   Managed secrets and identity services.

Choose a specific cloud target only after capacity, budget, operational
ownership and data-residency needs are known.

### 15.3 Operational requirements

-   Health and readiness checks.
-   Structured logs with correlation identifiers.
-   Error and exception tracking.
-   Database and worker monitoring.
-   Ingestion freshness monitoring.
-   Disk and storage monitoring.
-   Automated backups.
-   Periodic restore tests.
-   Documented deployment and rollback.
-   Incident response and escalation runbooks.

## 16. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Data-source             Data ingestion          Review terms, maintain
  restrictions or changes interruption or legal   source registry and
                          risk                    alternative providers

  Inconsistent financial  Incorrect analysis      Provenance, validation,
  data                                            reconciliation and
                                                  review queues

  Scope expansion         Schedule slippage       Prioritized backlog and
                                                  formal scope changes

  Complex financial       Incorrect user outcomes Document methodologies
  calculations                                    and maintain reference
                                                  tests

  Symbol and company      Broken historical       Internal UUID identity
  identity changes        relationships           and effective-dated
                                                  identifiers

  Corporate-action        Distorted returns       Separate raw/adjusted
  adjustment errors                               data and test
                                                  adjustment logic

  Large historical        Slow queries            Query profiling,
  datasets                                        indexes, caching and
                                                  measured partitioning

  Third-party library     Unexpected cost or      License review before
  licensing               restrictions            production selection

  Authentication or       Data exposure           Backend authorization,
  permission flaws                                security tests and
                                                  audit logs

  Single-host failure     Service outage/data     Backups, restore tests
                          loss                    and recovery procedure

  Over-engineering        Delayed delivery        Modular monolith and
  infrastructure                                  Docker Compose first

  Backtesting bias        Misleading strategy     Point-in-time data,
                          results                 out-of-sample testing
                                                  and explicit
                                                  assumptions
  -----------------------------------------------------------------------

## 17. Project tracking dashboard

Use this sprint register as the initial project-level checklist.
Detailed tasks should live under each sprint's own backlog.

  Sprint   Name                                          Duration Initial status
  -------- ------------------------------------------- ---------- ----------------
  S0       Planning and Architecture                       1 week BACKLOG
  S1       Repository and Development Environment         2 weeks BACKLOG
  S2       Infrastructure Bootstrap                       2 weeks BACKLOG
  S3       Authentication and Application Foundation      2 weeks BACKLOG
  S4       Financial Master Data                          2 weeks BACKLOG
  S5       Market Data and Corporate Actions              2 weeks BACKLOG
  S6       Data Ingestion Framework                       2 weeks BACKLOG
  S7       Historical Market Data                         2 weeks BACKLOG
  S8       Financial Fundamentals                         2 weeks BACKLOG
  S9       Mutual Funds, News and Research                2 weeks BACKLOG
  S10      Design System and Application Shell            2 weeks BACKLOG
  S11      Market Dashboard                               2 weeks BACKLOG
  S12      Equity Research Interface                      2 weeks BACKLOG
  S13      Financial Statements and Analytics UI          2 weeks BACKLOG
  S14      Stock Charts and Technical Analysis            2 weeks BACKLOG
  S15      Mutual Funds and Research UI                   2 weeks BACKLOG
  S16      Portfolio Management                           2 weeks BACKLOG
  S17      Stock Screening Engine                         2 weeks BACKLOG
  S18      Financial Analytics and Risk Engine            2 weeks BACKLOG
  S19      Quantitative Research and Backtesting          2 weeks BACKLOG
  S20      Alerts, Real-time Updates and Integration      2 weeks BACKLOG
  S21      Performance, Security and QA                   2 weeks BACKLOG
  S22      Production Deployment                          2 weeks BACKLOG
  S23      Hypercare and Final Acceptance                 2 weeks BACKLOG

### 17.1 Progress reporting template

For each sprint, record:

``` text
Sprint:
Sprint dates:
Sprint goal:
Sprint owner:

Planned tasks:
Completed tasks:
Deferred tasks:

Acceptance criteria:
Automated test results:
Defects opened:
Defects closed:

Blockers:
Risks:
Technical debt:
Documentation updates:

Sprint review decision:
Next sprint dependencies:
```

## 18. Immediate execution plan

Do not attempt to implement all domains at once. Start with Sprint 0 and
Sprint 1.

### First execution sequence

1.  Approve this master plan and record it as the project baseline.
2.  Create the FinTrack Git repository.
3.  Create the monorepo directories.
4.  Establish Python and Node package management.
5.  Add environment templates and secret-handling rules.
6.  Configure linting, formatting and type checking.
7.  Create the root Makefile and developer setup guide.
8.  Add the initial CI workflow.
9.  Bootstrap the Next.js and Django applications.
10. Prepare the Docker Compose foundation in Sprint 2.

### Sprint 1 exit gate

Sprint 1 is complete when:

-   Repository structure exists and is committed.
-   Frontend/backend/ingestion ownership is clear.
-   Development dependencies are reproducible.
-   Formatting and lint commands work.
-   Environment variables are documented without secrets.
-   CI runs on a pull request.
-   A new developer can follow the setup guide.

### Sprint 2 exit gate

Sprint 2 is complete when:

-   Next.js starts successfully.
-   Django starts successfully.
-   PostgreSQL and Redis are reachable.
-   Docker Compose starts the required services.
-   Health checks pass.
-   A basic frontend-to-backend request succeeds.
-   Automated smoke tests pass.

## 19. Architecture Decision Records

Maintain ADRs in `docs/adr/`. Initial proposed records:

  ADR       Decision
  --------- ---------------------------------------------------------
  ADR-001   Monorepo organization
  ADR-002   Next.js frontend
  ADR-003   Django modular monolith
  ADR-004   PostgreSQL as primary database
  ADR-005   Conditional evaluation of TimescaleDB
  ADR-006   Versioned REST API
  ADR-007   WebSockets through Channels where required
  ADR-008   Celery for background tasks
  ADR-009   Independent ingestion runtime and validated persistence
  ADR-010   Docker-based hybrid deployment
  ADR-011   Canonical company/instrument identity model
  ADR-012   Python analytics and quantitative research architecture
  ADR-013   Authentication and browser session strategy
  ADR-014   Financial data provenance and revision policy
  ADR-015   Charting and data-provider licensing decision

Each ADR should include context, decision, alternatives, consequences,
status and date.

## 20. Final project success criteria

FinTrack v1.0 is successful when:

1.  The application can be deployed reproducibly from documented source
    and configuration.
2.  Users can securely access the appropriate public and authenticated
    experiences.
3.  Supported financial datasets have clear provenance and validation.
4.  Company and instrument identities remain stable through symbol and
    listing changes.
5.  Market history, financial statements and corporate actions are
    queryable.
6.  Equity, mutual fund, news and research experiences work end to end.
7.  Charts and analytical calculations pass deterministic tests.
8.  Portfolio and screening workflows operate correctly.
9.  Quantitative experiments are reproducible and disclose their
    assumptions.
10. Monitoring, backups, restoration and operational procedures are in
    place.
11. No critical release-blocking security or correctness issue remains.
12. The architecture can evolve without requiring an immediate rewrite
    or premature microservice split.

------------------------------------------------------------------------

## Appendix A --- Planning assumptions

-   The 47-week schedule assumes a small cross-functional team and
    timely decisions.
-   Sprint duration is two weeks except the one-week planning Sprint 0.
-   Data-provider access, licenses and redistribution rights are
    dependencies.
-   Feature scope may be reprioritized, but changes must be recorded.
-   Technology versions must be compatibility-checked and locked at
    implementation time.
-   Cloud migration is a future deployment evolution, not a prerequisite
    for v1.0.
-   This document is the master plan; each sprint requires a more
    detailed implementation specification before execution.

## Appendix B --- Suggested documentation files

``` text
docs/
├── product/
│   ├── product-requirements.md
│   └── scope-and-priorities.md
├── architecture/
│   ├── system-architecture.md
│   ├── backend-architecture.md
│   ├── frontend-architecture.md
│   ├── ingestion-architecture.md
│   └── analytics-architecture.md
├── database/
│   ├── data-model.md
│   ├── financial-data-governance.md
│   └── data-dictionary.md
├── api/
│   └── api-standards.md
├── development/
│   ├── setup.md
│   ├── coding-standards.md
│   └── testing-strategy.md
├── deployment/
│   ├── self-hosted.md
│   ├── cloud-migration.md
│   └── backup-and-recovery.md
├── operations/
│   ├── monitoring.md
│   └── incident-response.md
└── adr/
    ├── ADR-001-monorepo.md
    ├── ADR-002-nextjs.md
    └── ...
```

**End of document.**
