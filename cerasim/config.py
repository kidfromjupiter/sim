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

# ── Production stages ─────────────────────────────────────────────────────────
# proc_mean_hr / proc_std_hr : processing time per BATCH_SIZE_UNITS batch
# mtbf_hr                    : mean time between failures (hours of operation)
# mttr_hr                    : mean time to repair (hours), Exponential distribution
# Theoretical max throughput  = (count / proc_mean_hr) × 24  batches/day
#
# Designed so the TUNNEL KILN is the bottleneck:
#   slip_prep     2 lines × 24/4.0  = 12   batches/day
#   casting       8 molds × 24/6.0  = 32   batches/day
#   demolding     3 lines × 24/18   = 4    batches/day
#   fettling      6 lines × 24/2.5  = 57.6 batches/day
#   glazing       4 booths × 24/1.2 = 80   batches/day
#   kiln ★        1 kiln  × 24/24   = 1    batch/day   ← bottleneck
#   finishing     4 lines × 24/1.5  = 64   batches/day
MACHINES = {
    "slip_prep": {
        "name":         "Slip Preparation Line",
        "detail":       "Ball mill → deflocculation → sieving",
        "count":        2,
        "proc_mean_hr": 4.0,
        "proc_std_hr":  0.5,
        "mtbf_hr":      350,
        "mttr_hr":      5.0,
        "capex_eur":    800_000,
    },
    "casting": {
        "name":         "Pressure Casting Mold Set",
        "detail":       "Gypsum molds + pressure casting equipment",
        "count":        8,
        "proc_mean_hr": 6.0,
        "proc_std_hr":  0.8,
        "mtbf_hr":      400,
        "mttr_hr":      3.5,
        "capex_eur":    500_000,
    },
    "demolding": {
        "name":         "Demolding & Initial Drying",
        "detail":       "Extract from molds + air dry 12-24h",
        "count":        3,
        "proc_mean_hr": 18.0,
        "proc_std_hr":  2.0,
        "mtbf_hr":      500,
        "mttr_hr":      2.0,
        "capex_eur":    300_000,
    },
    "fettling": {
        "name":         "Fettling & Trimming Station",
        "detail":       "Remove seams, smooth edges, create water passages",
        "count":        6,
        "proc_mean_hr": 2.5,
        "proc_std_hr":  0.4,
        "mtbf_hr":      600,
        "mttr_hr":      1.5,
        "capex_eur":    150_000,
    },
    "glazing": {
        "name":         "Spray Glazing Booth",
        "detail":       "Manual/robotic spray glazing + interior coating",
        "count":        4,
        "proc_mean_hr": 1.2,
        "proc_std_hr":  0.2,
        "mtbf_hr":      450,
        "mttr_hr":      3.0,
        "capex_eur":    600_000,
    },
    "kiln": {
        "name":         "Tunnel Kiln",
        "detail":       "Gas-fired continuous tunnel kiln, 1 180 °C peak",
        "count":        1,
        "proc_mean_hr": 24.0,
        "proc_std_hr":  2.0,
        "mtbf_hr":      720,
        "mttr_hr":      8.0,
        "capex_eur":    3_500_000,
    },
    "finishing": {
        "name":         "Quality Control & Packaging",
        "detail":       "Functional testing + inspection + packaging",
        "count":        4,
        "proc_mean_hr": 1.5,
        "proc_std_hr":  0.3,
        "mtbf_hr":      800,
        "mttr_hr":      1.0,
        "capex_eur":    250_000,
    },
}
