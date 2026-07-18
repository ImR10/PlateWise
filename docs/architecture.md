# PlateWise Architecture

## Current foundation

PlateWise is a small monorepo with separately deployable web and API applications backed by
PostgreSQL. Docker Compose provides a reproducible development environment without forcing either
developer to install matching language runtimes or databases locally.

```text
Browser -> Next.js web -> FastAPI API -> PostgreSQL
```

The frontend performs a server-side typed status request to the API. The API exposes versioned
routes and owns database access. This boundary makes it possible for a later mobile client to reuse
the same API without coupling nutrition logic to the website.

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
