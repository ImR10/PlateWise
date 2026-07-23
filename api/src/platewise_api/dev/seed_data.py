"""Deterministic development seed data.

The payload is a plain JSON-native dict in the ``FixtureDiningSource`` format,
so the seed exercises the real import pipeline end to end (validation,
normalization, provenance, counters, idempotent upserts). Quantities are
strings (Pydantic parses them to ``Decimal``); dates are ISO strings.

All names are generic placeholders consistent with the admin app's "Sample
University" fixtures. Nothing here refers to a real institution or dish.

Allergen and dietary-tag *assignments* live here too, but are applied by
``platewise_api.dev.seed`` directly through the ORM: the import pipeline does
not persist allergen/dietary-tag metadata yet (documented milestone gap), so
the seed supplements it explicitly until that wiring exists.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from platewise_api.imports import FakeIngredientNutritionProvider, ProviderFoodData
from platewise_api.imports.contracts import NutrientValues

#: Source identity for every seeded record; idempotency is keyed on this plus
#: each record's external id.
SOURCE_SYSTEM = "platewise_seed"
SOURCE_NAME = "platewise-dev-seed"
PROVIDER_NAME = "seed-provider"


def _n(**kwargs: str) -> NutrientValues:
    return NutrientValues(**{key: Decimal(value) for key, value in kwargs.items()})


def build_provider() -> FakeIngredientNutritionProvider:
    """Per-100 g canonical foods backing the seeded recipe items."""
    return FakeIngredientNutritionProvider(
        provider_name=PROVIDER_NAME,
        foods=[
            ProviderFoodData(
                provider=PROVIDER_NAME,
                provider_food_id="seed-chicken-breast",
                name="chicken breast, cooked",
                nutrients=_n(
                    calories="165",
                    protein_g="31",
                    carbohydrates_g="0",
                    fat_g="3.6",
                    saturated_fat_g="1.0",
                    fiber_g="0",
                    sugar_g="0",
                    sodium_mg="74",
                    cholesterol_mg="85",
                ),
            ),
            ProviderFoodData(
                provider=PROVIDER_NAME,
                provider_food_id="seed-white-rice",
                name="white rice, cooked",
                nutrients=_n(
                    calories="130",
                    protein_g="2.7",
                    carbohydrates_g="28",
                    fat_g="0.3",
                    saturated_fat_g="0.1",
                    fiber_g="0.4",
                    sugar_g="0.1",
                    sodium_mg="1",
                    cholesterol_mg="0",
                ),
            ),
            ProviderFoodData(
                provider=PROVIDER_NAME,
                provider_food_id="seed-black-beans",
                name="black beans, cooked",
                nutrients=_n(
                    calories="132",
                    protein_g="8.9",
                    carbohydrates_g="23.7",
                    fat_g="0.5",
                    saturated_fat_g="0.1",
                    fiber_g="8.7",
                    sugar_g="0.3",
                    sodium_mg="1",
                    cholesterol_mg="0",
                ),
            ),
            ProviderFoodData(
                provider=PROVIDER_NAME,
                provider_food_id="seed-olive-oil",
                name="olive oil",
                nutrients=_n(
                    calories="884",
                    protein_g="0",
                    carbohydrates_g="0",
                    fat_g="100",
                    saturated_fat_g="13.8",
                    fiber_g="0",
                    sugar_g="0",
                    sodium_mg="2",
                    cholesterol_mg="0",
                ),
            ),
            ProviderFoodData(
                provider=PROVIDER_NAME,
                provider_food_id="seed-tomato",
                name="tomato, raw",
                nutrients=_n(
                    calories="18",
                    protein_g="0.9",
                    carbohydrates_g="3.9",
                    fat_g="0.2",
                    saturated_fat_g="0.03",
                    fiber_g="1.2",
                    sugar_g="2.6",
                    sodium_mg="5",
                    cholesterol_mg="0",
                ),
            ),
        ],
    )


def _ingredient(
    line_no: int,
    text: str,
    grams: str,
    name: str,
    external_food_id: str,
) -> dict[str, Any]:
    return {
        "line_no": line_no,
        "original_text": text,
        "quantity": grams,
        "unit": "g",
        "name": name,
        "external_food_id": external_food_id,
    }


def _provided_item(
    external_id: str,
    name: str,
    *,
    description: str,
    station: str,
    meal_period: str,
    service_date: str,
    serving_size: str,
    serving_unit: str,
    nutrients: dict[str, str],
) -> dict[str, Any]:
    return {
        "source_system": SOURCE_SYSTEM,
        "external_id": external_id,
        "offering_external_id": _offering_external_id(
            external_id, station, service_date, meal_period
        ),
        "name": name,
        "description": description,
        "station_external_id": station,
        "meal_period": meal_period,
        "service_date": service_date,
        "provided_nutrition": {
            "serving_size": serving_size,
            "serving_unit": serving_unit,
            "nutrients": nutrients,
            "source_reference": f"{SOURCE_SYSTEM}:{external_id}",
        },
    }


def _offering_external_id(
    menu_item_external_id: str,
    station_external_id: str,
    service_date: str,
    meal_period: str,
) -> str:
    """Stable identity for one menu item in one dated station/meal slot."""
    return ":".join((menu_item_external_id, station_external_id, service_date, meal_period))


def build_payload(service_date: date) -> dict[str, Any]:
    """The full fixture payload for one service date."""
    day = service_date.isoformat()
    return {
        "institution": {
            "source_system": SOURCE_SYSTEM,
            "external_id": "seed-sample-university",
            "name": "Sample University",
            "slug": "sample-university",
            "institution_type": "university",
            "timezone": "America/New_York",
        },
        "venues": [
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-dining-hall-a",
                "name": "Dining Hall A",
                "slug": "dining-hall-a",
                "venue_type": "dining_hall",
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-dining-hall-b",
                "name": "Dining Hall B",
                "slug": "dining-hall-b",
                "venue_type": "dining_hall",
            },
        ],
        "stations": [
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-st-a-grill",
                "name": "Grill",
                "slug": "grill",
                "venue_external_id": "seed-dining-hall-a",
                "station_type": "grill",
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-st-a-salad",
                "name": "Salad Bar",
                "slug": "salad-bar",
                "venue_external_id": "seed-dining-hall-a",
                "station_type": "salad_bar",
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-st-a-global",
                "name": "Global Kitchen",
                "slug": "global-kitchen",
                "venue_external_id": "seed-dining-hall-a",
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-st-b-breakfast",
                "name": "Breakfast Bar",
                "slug": "breakfast-bar",
                "venue_external_id": "seed-dining-hall-b",
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-st-b-pizza",
                "name": "Pizza Oven",
                "slug": "pizza-oven",
                "venue_external_id": "seed-dining-hall-b",
            },
        ],
        "menu_items": [
            _provided_item(
                "seed-item-scrambled-eggs",
                "Scrambled Eggs",
                description="Fluffy scrambled eggs made fresh each morning.",
                station="seed-st-b-breakfast",
                meal_period="breakfast",
                service_date=day,
                serving_size="120",
                serving_unit="g",
                nutrients={
                    "calories": "180",
                    "protein_g": "12",
                    "carbohydrates_g": "2",
                    "fat_g": "13",
                    "cholesterol_mg": "370",
                    "sodium_mg": "320",
                },
            ),
            _provided_item(
                "seed-item-yogurt-parfait",
                "Greek Yogurt Parfait",
                description="Greek yogurt layered with granola and berries.",
                station="seed-st-b-breakfast",
                meal_period="breakfast",
                service_date=day,
                serving_size="220",
                serving_unit="g",
                nutrients={
                    "calories": "290",
                    "protein_g": "15",
                    "carbohydrates_g": "42",
                    "fat_g": "7",
                    "sugar_g": "24",
                    "fiber_g": "3",
                },
            ),
            _provided_item(
                "seed-item-oatmeal",
                "Steel-Cut Oatmeal",
                description="Slow-cooked oats with brown sugar on the side.",
                station="seed-st-b-breakfast",
                meal_period="breakfast",
                service_date=day,
                serving_size="240",
                serving_unit="g",
                nutrients={
                    "calories": "170",
                    "protein_g": "6",
                    "carbohydrates_g": "29",
                    "fat_g": "3",
                    "fiber_g": "4",
                    "sodium_mg": "10",
                },
            ),
            _provided_item(
                "seed-item-grilled-chicken",
                "Grilled Chicken Breast",
                description="Herb-marinated chicken breast off the grill.",
                station="seed-st-a-grill",
                meal_period="lunch",
                service_date=day,
                serving_size="140",
                serving_unit="g",
                nutrients={
                    "calories": "240",
                    "protein_g": "42",
                    "carbohydrates_g": "1",
                    "fat_g": "7",
                    "sodium_mg": "280",
                },
            ),
            _provided_item(
                "seed-item-mac-cheese",
                "Macaroni & Cheese",
                description="Classic baked macaroni with three cheeses.",
                station="seed-st-a-global",
                meal_period="lunch",
                service_date=day,
                serving_size="230",
                serving_unit="g",
                nutrients={
                    "calories": "430",
                    "protein_g": "16",
                    "carbohydrates_g": "44",
                    "fat_g": "21",
                    "saturated_fat_g": "12",
                    "sodium_mg": "740",
                },
            ),
            _provided_item(
                "seed-item-garden-salad",
                "Garden Salad",
                description="Mixed greens, cucumber, tomato, and carrots.",
                station="seed-st-a-salad",
                meal_period="lunch",
                service_date=day,
                serving_size="180",
                serving_unit="g",
                nutrients={
                    "calories": "60",
                    "protein_g": "2",
                    "carbohydrates_g": "11",
                    "fat_g": "1",
                    "fiber_g": "4",
                },
            ),
            _provided_item(
                "seed-item-fruit-cup",
                "Fresh Fruit Cup",
                description="Seasonal melon, grapes, and berries.",
                station="seed-st-a-salad",
                meal_period="lunch",
                service_date=day,
                serving_size="150",
                serving_unit="g",
                nutrients={
                    "calories": "80",
                    "protein_g": "1",
                    "carbohydrates_g": "20",
                    "sugar_g": "16",
                    "fiber_g": "2",
                },
            ),
            _provided_item(
                "seed-item-cheese-pizza",
                "Cheese Pizza Slice",
                description="Hand-stretched dough with mozzarella.",
                station="seed-st-b-pizza",
                meal_period="dinner",
                service_date=day,
                serving_size="125",
                serving_unit="g",
                nutrients={
                    "calories": "310",
                    "protein_g": "13",
                    "carbohydrates_g": "36",
                    "fat_g": "12",
                    "saturated_fat_g": "6",
                    "sodium_mg": "640",
                },
            ),
            _provided_item(
                "seed-item-pepperoni-pizza",
                "Pepperoni Pizza Slice",
                description="Cheese slice topped with pepperoni.",
                station="seed-st-b-pizza",
                meal_period="dinner",
                service_date=day,
                serving_size="130",
                serving_unit="g",
                nutrients={
                    "calories": "350",
                    "protein_g": "15",
                    "carbohydrates_g": "36",
                    "fat_g": "16",
                    "saturated_fat_g": "7",
                    "sodium_mg": "760",
                },
            ),
            _provided_item(
                "seed-item-tofu-stirfry",
                "Tofu Vegetable Stir-Fry",
                description="Crispy tofu and vegetables in a ginger sauce.",
                station="seed-st-a-global",
                meal_period="dinner",
                service_date=day,
                serving_size="280",
                serving_unit="g",
                nutrients={
                    "calories": "260",
                    "protein_g": "14",
                    "carbohydrates_g": "22",
                    "fat_g": "13",
                    "fiber_g": "5",
                    "sodium_mg": "520",
                },
            ),
            # Recipe-calculated items: no provided nutrition, so these exercise
            # the parser -> resolver -> calculator path end to end.
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-item-chicken-rice-bowl",
                "offering_external_id": _offering_external_id(
                    "seed-item-chicken-rice-bowl",
                    "seed-st-a-grill",
                    day,
                    "dinner",
                ),
                "name": "Chicken & Rice Bowl",
                "description": "Grilled chicken over steamed rice.",
                "station_external_id": "seed-st-a-grill",
                "meal_period": "dinner",
                "service_date": day,
                "recipe": {
                    "source_system": SOURCE_SYSTEM,
                    "external_id": "seed-recipe-chicken-rice-bowl",
                    "servings": "2",
                    "yield_quantity": "715",
                    "yield_unit": "g",
                    "ingredients": [
                        _ingredient(
                            1,
                            "300 g chicken breast, cooked",
                            "300",
                            "chicken breast",
                            "seed-chicken-breast",
                        ),
                        _ingredient(
                            2,
                            "400 g white rice, cooked",
                            "400",
                            "white rice",
                            "seed-white-rice",
                        ),
                        _ingredient(3, "15 g olive oil", "15", "olive oil", "seed-olive-oil"),
                    ],
                },
            },
            {
                "source_system": SOURCE_SYSTEM,
                "external_id": "seed-item-black-bean-bowl",
                "offering_external_id": _offering_external_id(
                    "seed-item-black-bean-bowl",
                    "seed-st-a-global",
                    day,
                    "lunch",
                ),
                "name": "Black Bean Burrito Bowl",
                "description": "Black beans, rice, and fresh tomato salsa.",
                "station_external_id": "seed-st-a-global",
                "meal_period": "lunch",
                "service_date": day,
                "recipe": {
                    "source_system": SOURCE_SYSTEM,
                    "external_id": "seed-recipe-black-bean-bowl",
                    "servings": "2",
                    "yield_quantity": "660",
                    "yield_unit": "g",
                    "ingredients": [
                        _ingredient(
                            1,
                            "250 g black beans, cooked",
                            "250",
                            "black beans",
                            "seed-black-beans",
                        ),
                        _ingredient(
                            2,
                            "300 g white rice, cooked",
                            "300",
                            "white rice",
                            "seed-white-rice",
                        ),
                        _ingredient(3, "100 g tomato, diced", "100", "tomato", "seed-tomato"),
                        _ingredient(4, "10 g olive oil", "10", "olive oil", "seed-olive-oil"),
                    ],
                },
            },
        ],
    }


#: Allergen declarations by menu-item external id (applied via ORM supplement).
ALLERGEN_ASSIGNMENTS: dict[str, tuple[str, ...]] = {
    "seed-item-scrambled-eggs": ("Eggs",),
    "seed-item-yogurt-parfait": ("Milk",),
    "seed-item-mac-cheese": ("Milk", "Wheat"),
    "seed-item-cheese-pizza": ("Milk", "Wheat"),
    "seed-item-pepperoni-pizza": ("Milk", "Wheat"),
    "seed-item-tofu-stirfry": ("Soy",),
}

#: Dietary tags by menu-item external id (applied via ORM supplement).
DIETARY_TAG_ASSIGNMENTS: dict[str, tuple[str, ...]] = {
    "seed-item-yogurt-parfait": ("Vegetarian",),
    "seed-item-oatmeal": ("Vegan", "Vegetarian"),
    "seed-item-garden-salad": ("Vegan", "Vegetarian", "Gluten-Free"),
    "seed-item-fruit-cup": ("Vegan", "Vegetarian", "Gluten-Free"),
    "seed-item-mac-cheese": ("Vegetarian",),
    "seed-item-cheese-pizza": ("Vegetarian",),
    "seed-item-tofu-stirfry": ("Vegan", "Vegetarian"),
    "seed-item-black-bean-bowl": ("Vegan", "Vegetarian", "Gluten-Free"),
}
