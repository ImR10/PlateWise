"""Export the FastAPI OpenAPI schema as deterministic JSON.

Used by ``scripts/generate-api-types.sh`` to feed frontend TypeScript type
generation. Writes to stdout by default, or to ``--out`` when given.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from platewise_api.main import app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None, help="output file (default: stdout)")
    args = parser.parse_args(argv)

    # sort_keys + fixed indent keep regenerated output byte-stable for diffs.
    schema = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(schema)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(schema, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
