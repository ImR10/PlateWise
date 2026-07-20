"""Record classification tests."""

from __future__ import annotations

import import_fixtures as fx

from platewise_api.imports.classifiers import classify
from platewise_api.imports.contracts import ImportedMenuItem
from platewise_api.imports.enums import RecordClassification


def _item(fixture: dict) -> ImportedMenuItem:
    return ImportedMenuItem.model_validate(fixture["menu_items"][0])


def test_classify_source_nutrition() -> None:
    assert classify(_item(fx.fixture_1_source_nutrition())) == RecordClassification.NUTRITION_READY


def test_classify_recipe_ready() -> None:
    assert classify(_item(fx.fixture_2_resolvable_recipe())) == RecordClassification.RECIPE_READY


def test_classify_missing_serving_basis_is_incomplete() -> None:
    assert classify(_item(fx.fixture_5_missing_serving_basis())) == RecordClassification.INCOMPLETE


def test_classify_missing_yield_is_incomplete() -> None:
    assert classify(_item(fx.fixture_6_missing_yield())) == RecordClassification.INCOMPLETE


def test_classify_both_prefers_nutrition_ready() -> None:
    assert classify(_item(fx.fixture_9_both_nutrition())) == RecordClassification.NUTRITION_READY


def test_classify_blank_name_is_invalid() -> None:
    item = ImportedMenuItem(source_system="fixture", name="   ")
    assert classify(item) == RecordClassification.INVALID
