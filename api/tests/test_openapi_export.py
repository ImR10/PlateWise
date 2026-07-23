"""OpenAPI export tests: the schema feeding frontend type generation is stable."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_openapi import main as export_main  # noqa: E402


def test_export_writes_valid_schema(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"

    assert export_main(["--out", str(out)]) == 0

    schema = json.loads(out.read_text(encoding="utf-8"))
    assert schema["info"]["title"] == "PlateWise API"
    assert "/api/v1/status" in schema["paths"]
    assert "/health" in schema["paths"]


def test_export_publishes_contract_schemas(tmp_path: Path) -> None:
    out = tmp_path / "openapi.json"
    export_main(["--out", str(out)])

    components = json.loads(out.read_text(encoding="utf-8"))["components"]["schemas"]
    # The envelope models must be present so generated frontend types can
    # reference them; StatusResponse backs the user app's ApiStatus type.
    for name in ("ApiErrorResponse", "ErrorInfo", "ValidationIssue", "StatusResponse"):
        assert name in components


def test_export_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    export_main(["--out", str(first)])
    export_main(["--out", str(second)])

    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
