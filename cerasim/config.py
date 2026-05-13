# SaniCer Sanitary Ware Industries — Supply Chain Simulation
# All time units are HOURS; quantities in tonnes (raw materials) or units (commodes).

# ── Simulation horizon ────────────────────────────────────────────────────────
SIM_DAYS      = 90
HOURS_PER_DAY = 24
SIM_DURATION  = SIM_DAYS * HOURS_PER_DAY   # 2 160 h

BATCH_SIZE_UNITS = 50   # units per production batch — fundamental granule of the sim

# ── Factory metadata ──────────────────────────────────────────────────────────
FACTORY_NAME     = "SaniCer Sanitary Ware Industries"
FACTORY_LOCATION = "Aveiro, Portugal"
FACTORY_FOUNDED  = 1987
FACTORY_EMPLOYEES = 240

# ── Products ──────────────────────────────────────────────────────────────────
# price_eur_unit  : ex-works price to distributor
# body_kg_per_unit: unfired green body weight (includes moisture, pre-firing shrink)
# glaze_kg_per_unit: wet glaze applied
# demand_share  : fraction of total units ordered by customers
PRODUCTS = {
    "ONE-PIECE-STD": {
        "name":             "One-Piece Standard Commode",
        "price_eur_unit":   180.0,
        "body_kg_per_unit": 35.0,
        "glaze_kg_per_unit": 2.5,
        "needs_glaze":      True,
        "complexity":       "medium",
        "demand_share":     0.45,
        "color":            "#2E86AB",
    },
    "TWO-PIECE-ECO": {
        "name":             "Two-Piece Economy Commode",
        "price_eur_unit":   120.0,
        "body_kg_per_unit": 28.0,
        "glaze_kg_per_unit": 2.0,
        "needs_glaze":      True,
        "complexity":       "low",
        "demand_share":     0.35,
        "color":            "#A23B72",
    },
    "WALL-HUNG-PREM": {
        "name":             "Wall-Hung Premium Commode",
        "price_eur_unit":   280.0,
        "body_kg_per_unit": 22.0,
        "glaze_kg_per_unit": 1.8,
        "needs_glaze":      True,
        "complexity":       "high",
        "demand_share":     0.20,
        "color":            "#F18F01",
    },
}

# Weighted average body weight (kg/unit) across the product mix
AVG_BODY_KG_UNIT = sum(
    PRODUCTS[p]["body_kg_per_unit"] * PRODUCTS[p]["demand_share"] for p in PRODUCTS
)  # ≈ 29.6 kg/unit

# Ceramic body composition (fraction of dry body weight)
# Sanitary ware uses more kaolin for whiteness
BODY_COMPOSITION = {
    "clay":     0.40,
    "kaolin":   0.25,
    "feldspar": 0.20,
    "silica":   0.15,
}
