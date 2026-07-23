#!/usr/bin/env bash
# Regenerate frontend TypeScript API types from the FastAPI OpenAPI schema.
#
# FastAPI is the source of truth: this exports the schema via
# api/scripts/export_openapi.py and runs openapi-typescript for each frontend.
# Rerun after any backend contract change and commit the regenerated files:
#
#   pnpm api:types
#
# Generated files (do not edit by hand):
#   apps/user/lib/api-schema.gen.ts
#   apps/admin/src/api/schema.gen.ts
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/platewise-openapi.XXXXXX")"
SCHEMA="$TEMP_DIR/openapi.json"
trap 'rm -f "$SCHEMA"; rmdir "$TEMP_DIR"' EXIT

export_schema() {
  if [[ -x "$ROOT/api/.venv/bin/python" ]]; then
    "$ROOT/api/.venv/bin/python" "$ROOT/api/scripts/export_openapi.py" --out "$SCHEMA"
  elif docker compose -f "$ROOT/compose.yaml" ps --status running api >/dev/null 2>&1 \
    && [[ -n "$(docker compose -f "$ROOT/compose.yaml" ps --status running -q api 2>/dev/null)" ]]; then
    docker compose -f "$ROOT/compose.yaml" exec -T api \
      uv run python /workspace/api/scripts/export_openapi.py >"$SCHEMA"
  else
    echo "error: need either api/.venv (host) or a running Compose 'api' service" >&2
    echo "hint: docker compose up -d api" >&2
    exit 1
  fi
}

export_schema

pnpm exec openapi-typescript "$SCHEMA" -o "$ROOT/apps/user/lib/api-schema.gen.ts"
pnpm exec openapi-typescript "$SCHEMA" -o "$ROOT/apps/admin/src/api/schema.gen.ts"

echo "Generated API types for apps/user and apps/admin."
