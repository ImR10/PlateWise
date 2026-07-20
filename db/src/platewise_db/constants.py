"""Constants shared by persistence models and their API consumers."""

# The order is stable across imported, provider, calculated, and stored nutrition.
NUTRIENT_FIELDS: tuple[str, ...] = (
    "calories",
    "protein_g",
    "carbohydrates_g",
    "fat_g",
    "saturated_fat_g",
    "fiber_g",
    "sugar_g",
    "sodium_mg",
    "cholesterol_mg",
)
