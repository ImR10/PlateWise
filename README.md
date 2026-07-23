# PlateWise

PlateWise is a student-built proof of concept that uses dining-hall menu and nutrition data to help
students find foods that match their preferences and goals. The intended experience can rank
individual menu items and suggest practical meal combinations using inputs such as calorie ranges,
protein targets, vegetarian or vegan preferences, and allergen exclusions.

The current repository provides a responsive Next.js frontend, a Vite admin frontend, a typed
FastAPI backend, PostgreSQL persistence, and tested import, nutrition, and recommendation
foundations. The public HTTP surface is still intentionally small (health and status); the admin
feature pages use in-memory mock data and are not connected to backend resource endpoints.

> PlateWise is an independent student-built proof of concept and is not affiliated with, endorsed
> by, or an official service of the University of Georgia or any dining-data provider. Users should
> consult official dining resources for current ingredient and allergen information.

## Architecture

| Application | Stack | Port | Purpose |
| --- | --- | --- | --- |
| `user` | Next.js, TypeScript, Tailwind CSS | `3000` | Student-facing interface (mobile-first) |
| `admin` | Vite, React, TypeScript, Tailwind CSS | `1420` | Dining-hall staff admin website (host-run, not in Compose) |
| `api` | FastAPI | `8000` | Single backend shared by both clients |
| `db` | SQLAlchemy, Alembic, PostgreSQL 17 | `5432` | Persistence package and database service |

See [docs/architecture.md](docs/architecture.md) for design rationale and future module boundaries.

## Repository layout

```text
apps/
  user/                Next.js application and component tests
  admin/               Vite + React admin website for dining-hall staff
api/                    FastAPI service, orchestration, schemas, and tests
db/                     SQLAlchemy models, repositories, migrations, and tests
docs/
  architecture.md
compose.yaml
.env.example
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
```

Only user-facing client applications live under `apps/`. The API depends explicitly on the
editable `platewise-db` package; neither client connects to PostgreSQL directly.

## Prerequisites

- Docker Desktop with Docker Compose v2
- Git
- About 2 GB of free disk space for images and development volumes

Node, Python, pnpm, uv, and PostgreSQL do not need to be installed on the host for the Compose-only
workflow, which covers `db`, `api`, and `user`. Node and pnpm are required on the host for the admin
website and API contract generation. See [Admin website](#admin-website).

## Initial setup

```bash
git clone <repository-url>
cd PlateWise
cp .env.example .env
docker compose up -d --build
docker compose exec -w /workspace/db api uv run --project /workspace/api alembic upgrade head
```

This starts PostgreSQL, the API, and the user app. Open:

- User app: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

The admin app runs separately on the host. After installing the pinned workspace dependencies with
`pnpm install`, run `pnpm admin:dev` and open
[http://localhost:1420](http://localhost:1420).

The values in `.env.example` are local-development defaults only. Change them for any shared or
deployed environment. Never commit `.env`.

## Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `POSTGRES_DB` | db | Development database name |
| `POSTGRES_USER` | db | Development database user |
| `POSTGRES_PASSWORD` | db | Development database password |
| `DATABASE_URL` | api | SQLAlchemy connection URL using Compose hostname `db` |
| `APP_ENV` | api | Runtime environment label |
| `CORS_ORIGINS` | api | Comma-separated allowed browser origins (both the user app on `3000` and the admin app on `1420`) |
| `API_INTERNAL_URL` | user | Server-side URL used inside Compose |
| `NEXT_PUBLIC_API_URL` | user | Browser-visible API base URL reserved for client calls |
| `VITE_API_URL` | admin | Optional API base URL override for the host-run admin app (defaults to `http://localhost:8000`) |

Compose reads the first eight values from the root `.env`. `CORS_ORIGINS` is a comma-separated list
of exact origins (scheme, host, and port); the defaults allow
`http://localhost:3000` and `http://localhost:1420`. After changing an API environment value,
recreate the API service with `docker compose up -d --force-recreate api`.

The current user status request runs on the Next.js server and uses `API_INTERNAL_URL`
(`http://api:8000` inside Compose). `NEXT_PUBLIC_API_URL` is reserved for future browser-side user
requests and is not currently read by application code. Because the admin app runs on the host,
override its API URL either in the command environment:

```bash
VITE_API_URL=http://localhost:8000 pnpm admin:dev
```

## Everyday Docker workflow

```bash
docker compose up --build
docker compose logs -f
docker compose down
```

To run only the database and API, use `docker compose up --build db api`. Add `user` to that command
when the user frontend is needed. The admin frontend always runs separately with `pnpm admin:dev`.

Source directories are bind-mounted and both app services hot reload. Dependencies live in named
volumes so Linux container packages never overwrite host directories.

After pulling dependency changes, rebuild:

```bash
docker compose build --no-cache api user
docker compose up
```

Open service shells:

```bash
docker compose exec api sh
docker compose exec user sh
```

## Tests, linting, and formatting

```bash
docker compose exec api uv run pytest
docker compose exec api uv run ruff check src tests
docker compose exec api uv run ruff format --check src tests
docker compose exec -w /workspace/db api uv run --project /workspace/api pytest
docker compose exec -w /workspace/db api uv run --project /workspace/api ruff check src tests alembic
docker compose exec -w /workspace/db api uv run --project /workspace/api ruff format --check src tests alembic

pnpm user:test
pnpm user:lint
pnpm user:format:check
```

Apply automatic formatting with:

```bash
docker compose exec api uv run ruff format src tests
pnpm user:format
```

## API error format

Exceptions and request-validation failures handled by the application use one standard envelope
(see `api/src/platewise_api/schemas/errors.py` and the handlers in
`api/src/platewise_api/core/errors.py`):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      {
        "loc": ["query", "count"],
        "msg": "Input should be a valid integer.",
        "type": "int_parsing"
      }
    ],
    "context": null
  }
}
```

`code` is stable and machine-readable; clients branch on it, never on `message`. Endpoints raise
`platewise_api.core.errors.ApiError` for intentional failures; framework validation and HTTP errors
are translated into the same shape automatically, and headers such as `WWW-Authenticate` are
preserved. Unexpected exceptions are logged and return a generic `500` envelope with code
`internal_error`; exception text and stack traces are not returned. `details` is populated for
request-validation errors and is otherwise normally `null`; `context` is optional structured data
from an intentional `ApiError`.

The operational `/health` route is the deliberate exception: when PostgreSQL is unavailable it
returns its documented `503` health payload (`status: "degraded"`, `database: "unavailable"`) rather
than an exception envelope.

## Generated TypeScript API types

FastAPI's OpenAPI schema is the source of truth for frontend contracts. Generated files are
committed and must never be edited by hand:

- `apps/user/lib/api-schema.gen.ts`
- `apps/admin/src/api/schema.gen.ts`

Regenerate after any backend contract change and commit the result:

```bash
pnpm install
pnpm api:types
```

The script (`scripts/generate-api-types.sh`) exports the schema with
`api/scripts/export_openapi.py` — using `api/.venv` when present, otherwise the running Compose
`api` service — and runs `openapi-typescript` for both apps. The admin HTTP client
(`apps/admin/src/api/client.ts`) consumes these types, including the error envelope.

`pnpm install` is required once on the host. If there is no local `api/.venv`, start the API first
with `docker compose up -d db api`. A successful regeneration should change the generated files only
when the FastAPI contract changed.

## Admin HTTP client

`apps/admin/src/api/client.ts` is a small shared transport foundation; no admin page uses it yet.
Application-facing endpoint modules can use the exported `apiClient`, while tests can inject a
`fetch` implementation through `createApiClient`. It:

- resolves the base URL from an explicit option, then `VITE_API_URL`, then
  `http://localhost:8000`;
- sends and parses JSON, treats empty successful responses as having no body, and supports
  `AbortSignal`;
- converts API envelopes, network failures, and malformed responses into `ApiRequestError` while
  leaving cancellation distinguishable;
- applies default, injected, and caller headers in that order, with caller headers taking
  precedence.

It is transport plumbing, not a generated SDK, authentication implementation, or evidence that the
mock admin pages are connected to the backend.

## Seed development data

The deterministic development seed runs the real import pipeline in strict mode. It creates the
Sample University institution, two dining halls, five stations, twelve stable catalog items,
twelve offerings for each selected date, nutrition on both the source-provided and
recipe-calculated paths, and allergen/dietary-tag links. Apply migrations first, then seed today:

```bash
pnpm db:seed
```

`pnpm db:seed` requires the Compose API service to be running and uses today's date. For an explicit
date, a same-date idempotency check, and a second date:

```bash
docker compose exec api uv run python -m platewise_api.dev.seed --date 2026-07-23
docker compose exec api uv run python -m platewise_api.dev.seed --date 2026-07-23
docker compose exec api uv run python -m platewise_api.dev.seed --date 2026-07-24
```

Menu-item identity remains stable across dates, while offering identity includes the item, station,
date, and meal period. Re-running the same date creates another import audit row but does not
duplicate catalog items, offerings, nutrition, or metadata links. Seeding a second date keeps the
same twelve catalog items and adds twelve offerings for that date.

All seed records use the `platewise_seed` source system. Allergen and dietary-tag links are applied
directly through the ORM only after a fully successful import, are marked with `imported`
provenance—not `official`—and are a temporary persistence bridge until the import pipeline handles
that metadata itself. An unsuccessful strict import exits nonzero, rolls back its catalog work, and
does not apply the metadata supplement.

## Admin website

`apps/admin` is a separate browser-based website for dining-hall staff, built with Vite, React,
TypeScript, and Tailwind CSS. It runs on the host as a standard web app rather than inside Docker
Compose. `api` remains the single backend for both clients; the admin app has no backend of its own
and never connects to PostgreSQL directly.

Additional host prerequisites (admin development only):

- Node.js 22+ with pnpm 11 (`corepack enable` provides the pinned version)

Everyday commands, from the repository root:

```bash
pnpm install               # once, and after dependency changes
pnpm admin:dev             # run the dev server at http://localhost:1420
pnpm admin:test            # component and routing tests (Vitest)
pnpm admin:lint            # ESLint
pnpm admin:format:check    # Prettier
pnpm admin:typecheck       # TypeScript
pnpm admin:build           # type-check + production build
```

The dashboard ships the Sample University admin overview against typed local mock data: today's menu
readiness, needs-attention items, dining locations, upcoming menus, recent activity, and quick
actions.

### Frontend-only feature areas

Three feature areas are implemented as **frontend-only MVPs**. Every value is generic mock data
(`Sample University`, `Dining Hall A`–`E`, `Menu Item NN`, `Station A`–`E`, `Category A`–`D`,
`John Doe`/`Jane Doe`/`System`) held in typed modules under `apps/admin/src/data/`. All edits run
against **in-memory React state only** and **refreshing the browser resets everything**. There is no
API, database, persistence, or authentication behind them — backend integration is intentionally
deferred.

- **Menus** (`/menus`, `/menus/:menuId/edit`, `/menus/:menuId/preview`) — create, duplicate,
  publish, draft, delete; station and item editing; publish validation; student preview.
  State: `apps/admin/src/state/MenusProvider.tsx`.
- **Dining Locations** (`/locations`, `/locations/new`, `/locations/:locationId/edit`,
  `/locations/:locationId/preview`) — manage locations with a Draft/Active/Inactive/Archived
  lifecycle, service configuration (meal periods + stations), weekly operating hours, activation
  validation, and a student preview. State: `apps/admin/src/state/DiningLocationsProvider.tsx`.
- **Food Catalog** (`/foods`, `/foods/new`, `/foods/:foodId/edit`, `/foods/:foodId/preview`) —
  manage food items with a Draft/Active/Archived lifecycle, dietary tags, allergens, serving
  metadata, activation validation, and a student preview.
  State: `apps/admin/src/state/FoodCatalogProvider.tsx`.

- **Analysis** (`/analysis`) — an operations-analytics MVP for dining administrators. It surfaces
  recommendation demand, estimated student selections/consumption, recommendation-to-selection
  rates, and advisory inventory-planning signals (possible shortage / overproduction risk),
  availability and unmet-demand, waste-risk estimates, and a data-source/quality panel. It is driven
  entirely by deterministic mock events (`apps/admin/src/data/analysis.ts`) with pure derivations
  (`apps/admin/src/lib/analysis.ts`); filter state is page-local. **All consumption, prepared-serving,
  and waste figures are estimates derived from mock event counts — never confirmed consumption or
  inventory.** The page clearly labels estimates, disables the export control until integration, and
  is intended to be validated with dining-hall admins during the pitch (which metrics are useful,
  which are misleading, what data they already collect, and what systems PlateWise could integrate
  with). Real analytics would require backend event tracking and dining-system integrations
  (recommendation/selection events, servings prepared/taken, leftovers, POS, and inventory).

The Dining Locations and Food Catalog records are shared managed data that the Menus feature also
consumes: the create-menu location picker offers only active/draft locations (inactive and archived
are excluded), and the menu food-item picker offers only non-archived catalog items. The Analysis
tab resolves its food and location names from the same managed records. This integration is entirely
in memory and resets on refresh.

The remaining sidebar route (Settings) is an intentional placeholder.

## Database migrations

Apply all migrations:

```bash
docker compose exec -w /workspace/db api uv run --project /workspace/api alembic upgrade head
```

Create a migration after changing SQLAlchemy models, then inspect the generated file before applying
it:

```bash
docker compose exec -w /workspace/db api uv run --project /workspace/api alembic revision --autogenerate -m "describe change"
docker compose exec -w /workspace/db api uv run --project /workspace/api alembic upgrade head
```

The two existing revisions create the PlateWise schema and data-import foundation. Migration
revision identifiers and history are owned by `db/alembic/`.

## Reset local data

This permanently removes the local Compose database volume:

```bash
docker compose down -v
docker compose up --build
docker compose exec -w /workspace/db api uv run --project /workspace/api alembic upgrade head
```

## Troubleshooting

- **A port is already in use:** stop the process using `1420`, `3000`, `8000`, or `5432`, or adjust
  the relevant host port. Compose mappings live in `compose.yaml`; the admin port is in
  `apps/admin/vite.config.ts`.
- **A service is unhealthy:** run `docker compose ps` and `docker compose logs api db user`.
- **Dependencies look stale:** rebuild the affected image and recreate its dependency volume with
  `docker compose down -v` only if a normal rebuild does not resolve it. Note that `-v` also deletes
  the development database.
- **The status panel says unavailable:** confirm `api` is healthy and that `API_INTERNAL_URL` remains
  `http://api:8000` inside Compose.
- **The admin cannot reach the API:** confirm the API is available at the configured `VITE_API_URL`
  and that the admin page's exact origin is present in `CORS_ORIGINS`.
- **`pnpm api:types` cannot export the schema:** run `pnpm install`, then either create the local
  `api/.venv` or start `db` and `api` with `docker compose up -d db api`.
- **Seeding fails:** apply migrations, confirm the API service is running, and inspect
  `docker compose logs api db`. A failed strict seed intentionally exits nonzero.
- **Database credentials changed:** recreate the database volume; PostgreSQL initialization variables
  do not modify an existing volume.

## macOS and Apple Silicon

The selected official images support ARM64 and require no `platform` override. Docker Desktop file
sharing can make hot reload slower on macOS; keep the repository in a Docker-shared directory and
avoid storing `node_modules` on the bind mount. PostgreSQL is intentionally exposed on `5432` for
local database tools; change or remove that mapping if it conflicts with a host installation.

## Two-developer Git workflow

1. Pull `main` and create a focused feature branch.
2. Copy `.env.example` to `.env`; never share or commit `.env`.
3. Run `docker compose up --build` after pulling lockfile or Docker changes.
4. Apply migrations before developing and include reviewed migration files with model changes.
5. Run both test suites, linters, and format checks before opening a pull request.
6. Commit lockfile changes with their corresponding dependency manifest changes.
7. Rebase or merge the latest `main`, verify Compose again, and request review.
