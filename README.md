# UniDine

UniDine is an early campus-dining application foundation. The current scaffold provides a
responsive Next.js frontend, a typed FastAPI backend, and PostgreSQL persistence. Authorized menu
ingestion, nutrition normalization, recommendations, and user preferences are intentionally out of
scope for this first milestone.

## Architecture

| Service | Stack | Port | Purpose |
| --- | --- | --- | --- |
| `web` | Next.js, TypeScript, Tailwind CSS | `3000` | Student-facing interface |
| `api` | FastAPI, SQLAlchemy, Alembic | `8000` | API and future recommendation logic |
| `db` | PostgreSQL 17 | `5432` | Application data |

See [docs/architecture.md](docs/architecture.md) for design rationale and future module boundaries.

## Repository layout

```text
apps/
  api/                 FastAPI service, migrations, and tests
  web/                 Next.js application and component tests
docs/
  architecture.md
compose.yaml
.env.example
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
```

## Prerequisites

- Docker Desktop with Docker Compose v2
- Git
- About 2 GB of free disk space for images and development volumes

Node, Python, pnpm, uv, and PostgreSQL do not need to be installed on the host for the Docker
workflow.

## Initial setup

```bash
git clone <repository-url>
cd unidine
cp .env.example .env
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). API docs are available at
[http://localhost:8000/docs](http://localhost:8000/docs).

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
| `CORS_ORIGINS` | api | Comma-separated allowed browser origins |
| `API_INTERNAL_URL` | web | Server-side URL used inside Compose |
| `NEXT_PUBLIC_API_URL` | web | Browser-visible API base URL reserved for client calls |

## Everyday Docker workflow

```bash
docker compose up --build
docker compose logs -f
docker compose down
```

Source directories are bind-mounted and both app services hot reload. Dependencies live in named
volumes so Linux container packages never overwrite host directories.

After pulling dependency changes, rebuild:

```bash
docker compose build --no-cache api web
docker compose up
```

Open service shells:

```bash
docker compose exec api sh
docker compose exec web sh
```

## Tests, linting, and formatting

```bash
docker compose exec api uv run pytest
docker compose exec api uv run ruff check .
docker compose exec api uv run ruff format --check .

docker compose exec web pnpm test
docker compose exec web pnpm lint
docker compose exec web pnpm format:check
```

Apply automatic formatting with:

```bash
docker compose exec api uv run ruff format .
docker compose exec web pnpm format
```

## Database migrations

Apply all migrations:

```bash
docker compose exec api uv run alembic upgrade head
```

Create a migration after changing SQLAlchemy models, then inspect the generated file before applying
it:

```bash
docker compose exec api uv run alembic revision --autogenerate -m "describe change"
docker compose exec api uv run alembic upgrade head
```

The initial migration creates the `campuses` table.

## Reset local data

This permanently removes the local Compose database volume:

```bash
docker compose down -v
docker compose up --build
docker compose exec api uv run alembic upgrade head
```

## Troubleshooting

- **A port is already in use:** stop the process using `3000`, `8000`, or `5432`, or adjust the host
  side of that mapping in `compose.yaml`.
- **A service is unhealthy:** run `docker compose ps` and `docker compose logs api db web`.
- **Dependencies look stale:** rebuild the affected image and recreate its dependency volume with
  `docker compose down -v` only if a normal rebuild does not resolve it. Note that `-v` also deletes
  the development database.
- **The status panel says unavailable:** confirm `api` is healthy and that `API_INTERNAL_URL` remains
  `http://api:8000` inside Compose.
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
