# PlateWise Architecture

## Current foundation

PlateWise is a small monorepo with three client/backend applications backed by PostgreSQL:
a student-facing web app, a dining-hall staff desktop app, and a shared API. Docker Compose
provides a reproducible development environment for the user, API, and database services without
forcing either developer to install matching language runtimes or databases locally; the desktop
app runs on the host.

```text
Browser        -> Next.js user (apps/user)  -> FastAPI API (api) -> platewise_db -> PostgreSQL
Desktop window -> Tauri admin (apps/admin) -> FastAPI API (api) -> platewise_db -> PostgreSQL
```

The web frontend performs a server-side typed status request to the API. The API exposes versioned
routes and owns database access. This boundary makes it possible for any client — the student web
app, the admin desktop app, or a later mobile client — to reuse the same API without coupling
nutrition logic to a particular frontend.

## Client applications

- **`apps/user` — student web app.** Next.js, mobile-first, served in the browser.
- **`apps/admin` — staff desktop app.** Tauri 2 + React + TypeScript, desktop-first, distributed
  as a native application. It exists as a separate application (not routes inside `apps/user`)
  because dining-hall staff have materially different interaction patterns, security requirements,
  deployment considerations, and future native capabilities from students. As of the current
  milestone it is an application-shell foundation only: no API integration, authentication, or
  catalog features yet.

The repository has four explicit ownership boundaries:

1. **`apps/user` and `apps/admin` are clients only.** `apps/` contains no backend or persistence
   implementation.
2. **`api` is the single backend.** It owns HTTP routes, configuration, API schemas, import
   orchestration, and recommendation logic.
3. **`db` owns persistence.** The `platewise_db` package owns SQLAlchemy models, sessions,
   repositories, and Alembic migrations. `platewise_api` depends on it explicitly.
4. **No client accesses PostgreSQL directly.** Both clients communicate only with the API.

## Stack choices

### Next.js and TypeScript

The App Router supports server rendering and a conventional path to production deployment.
TypeScript keeps API contracts and UI states explicit. Native `fetch` is enough for the current
read-only request; a client cache library would add complexity before the application has interactive
server state.

### FastAPI and Python

FastAPI provides typed HTTP boundaries through Pydantic. Python is also a natural home for future
data normalization and constrained meal optimization libraries. Keeping those operations behind an
API prevents the browser from becoming the authority for safety rules.

### PostgreSQL, SQLAlchemy, and Alembic

PostgreSQL supplies relational constraints, mature indexing, and JSON support for menu provenance
where it is useful. SQLAlchemy 2.x defines application models, while reviewed Alembic migrations
make schema changes repeatable across both developers' databases.

### Docker Compose

Compose standardizes Python, Node, pnpm, uv, and PostgreSQL versions. Bind mounts enable application
hot reload; named volumes isolate container dependencies and persist local database state.

## Data boundaries

Future work should maintain four distinct categories:

1. **Raw authorized source records:** immutable snapshots with source and retrieval metadata.
2. **Normalized menu records:** provider-independent campuses, locations, meals, foods, nutrients,
   ingredients, and availability.
3. **Recommendation-ready records:** validated items with confidence, freshness, and safety flags.
4. **User preferences:** minimized inputs, local-first where feasible, never mixed into source data.

## Future modules

- **Authorized menu ingestion:** fetch sanctioned feeds conservatively, retain provenance, detect
  changes, and surface source outages.
- **Normalization:** convert vendor-specific units and structures into a documented internal schema
  without silently inventing missing nutrition values.
- **Recommendation optimization:** apply deterministic constraints and realistic serving increments;
  an LLM must not decide allergen safety or fabricate nutrition facts.
- **Safety rules:** enforce exclusions, stale-data behavior, confidence indicators, approximate-portion
  language, and escalation to dining staff for allergen questions.
- **Privacy-preserving preferences:** begin with guest/local storage and introduce accounts only when a
  concrete user benefit justifies collecting identifiable data.

## Deliberately out of scope

This scaffold contains no authentication, analytics, health profiles, calorie-target calculation,
live menu ingestion, scraping, recommendation engine, production deployment configuration, or
medical claims. The single `Campus` model exists to prove database and migration wiring, not to fix
the future domain model prematurely.
