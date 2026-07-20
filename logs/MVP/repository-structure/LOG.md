# Repository Structure Correction

Date: 2026-07-20

- Renamed the student client from `apps/web` to `apps/user` and its package to
  `@platewise/user`.
- Moved the FastAPI backend from `apps/api` to the explicit `platewise_api`
  package under `api/src/`.
- Extracted models, sessions, repositories, persistence utilities, tests, and
  unchanged Alembic history into the explicit `platewise_db` package under
  `db/src/`.
- Updated pnpm, Docker, Compose, imports, tests, and current documentation for
  the new boundaries.
- Validated 54 DB tests, 139 API/service tests, 2 user tests, 1 admin test,
  Ruff/Prettier/ESLint/type/build checks, `cargo check`, Alembic upgrade/check,
  and healthy `db`, `api`, and `user` Compose services.
