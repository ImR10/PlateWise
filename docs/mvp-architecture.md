# PlateWise MVP - System Architecture

Scope: MVP only. One campus (UGA), guest mode, local-browser preferences, deterministic
recommendations, single backend service, and the authorized dining-hall admin dashboard as the data
source of record. No auth service, Redis, Celery, workers, or microservices at this stage.

## Container / component diagram

```mermaid
flowchart TB
    subgraph Clients [Clients]
        Student["Student<br/>menu browse + recommendations"]
        Admin["Dining Hall Admin/Manager<br/>maintains food info"]
    end

    subgraph User [user - Next.js 16 / React 19 / TS / Tailwind]
        StudentUI["Student app routes<br/>/, /menus, /menus/[id], /recommend, /recommend/result"]
        LocalPrefs["localStorage<br/>targets, dietary prefs, dislikes"]
        ApiClient["Typed API client<br/>(OpenAPI-generated types)"]
    end

    subgraph AdminApp [admin - Tauri 2 / React / TS desktop app]
        AdminUI["Admin dashboard<br/>menu + food editing"]
    end

    subgraph API [api - FastAPI single service]
        Router["/api/v1 routers<br/>campuses, dining-halls, menu-services, recommendations, data-status"]
        Schemas["Pydantic schemas<br/>(OpenAPI source of truth)"]
        Domain["Domain + normalization"]
        Providers["providers/authorized_uga<br/>fetch + normalize"]
        Ingestion["ingestion<br/>raw snapshot, hash, idempotent upsert"]
        Rec["recommendations<br/>deterministic constrained search"]
    end

    subgraph DBPackage [db - platewise_db package]
        Models["SQLAlchemy models + metadata"]
        Repos["persistence repositories"]
        Migrations["Alembic revisions"]
    end

    DB[("db - PostgreSQL 17")]

    Student -->|HTTPS| StudentUI
    Admin -->|desktop app| AdminUI
    StudentUI --> LocalPrefs
    StudentUI --> ApiClient
    ApiClient -->|REST / JSON| Router
    AdminUI -->|REST / JSON| Router

    Router --> Schemas
    Router --> Repos
    Router --> Rec
    Rec --> Repos
    Repos --> Models
    Repos --> DB

    AdminUI -->|POST food info| Router
    Router --> Ingestion
    Providers --> Ingestion
    Ingestion --> Repos
    Migrations -->|alembic upgrade head| DB

    subgraph Compose [Docker Compose - dev]
        User
        API
        DB
    end
```

## Data layers

The system keeps four separate data categories so raw source data is never silently mixed with
product or user data.

```mermaid
flowchart LR
    Source["Authorized source<br/>admin dashboard entry<br/>(future: authorized feed)"]
    Raw["Immutable raw snapshot<br/>payload + hash + retrieved_at + source_updated_at"]
    Adapter["Provider adapter<br/>normalize units + structure"]
    Normalized["Normalized menu domain<br/>Campus, DiningHall, Station, MealPeriod,<br/>MenuService, MenuOffering, FoodItem,<br/>ServingOption, NutritionFacts, Allergens, DietaryTag"]
    RecReady["Recommendation-ready view<br/>confidence, freshness, safety flags"]
    Response["Stateless recommendation response<br/>plates, totals, warnings (not persisted)"]

    Source --> Raw --> Adapter --> Normalized --> RecReady --> Response
```

## Key architectural decisions

- **Single deployable backend** in `api/src/platewise_api`, with routes, schemas, importer
  orchestration, source adapters, and recommendations. Persistence is an explicit dependency in
  `db/src/platewise_db`; it is a package boundary, not another network service.
- **Separate admin desktop client (updated 2026-07-20).** The dining-hall staff dashboard is a
  separate Tauri 2 + React + TypeScript desktop application (`apps/admin`), not routes inside the
  student web app; earlier revisions of this document that placed admin routes inside `web` are
  superseded. `api` remains the single backend for both clients, `db` owns the persistence
  package and migrations, and no client connects to PostgreSQL directly. The admin app runs on
  the host and is not a Compose service.
- **Admin dashboard is the authorized data source** for the MVP; writes flow through the same
  FastAPI service into raw snapshots, then idempotent normalized upserts (`(provider, external_id,
  service_date)` unique). Re-import of the same snapshot is a no-op.
- **Alembic is owned by `db`.** Migrations run from `db/alembic`; Compose intentionally has only
  `db`, `api`, and `user` services and does not add an automation service.
- **Recommendations are computed, not stored.** `POST /api/v1/recommendations` runs a deterministic
  constrained search and returns plates with totals, confidence, freshness, and warning codes.
- **Local-first preferences.** Student targets, dietary preferences, and dislikes live in
  `localStorage`; they are never written to the server (no accounts in MVP).
- **Single OpenAPI contract.** Frontend TypeScript types are generated from the FastAPI OpenAPI
  schema; Python and TypeScript never define competing versions of the same response.
- **Safety and freshness first.** Missing nutrition is surfaced as unknown (never zero),
  unknown-allergen items are excluded from recommendations, portion caps are enforced, and stale or
  partial data produces visible warnings.

## Deliberately excluded from the MVP

Authentication/accounts, profile sync, Redis, Celery/queues, Kubernetes, native student apps,
multi-campus abstractions beyond a simple provider boundary, ML/LLM food selection, and persistent
recommendation history.
