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

# ── Raw-material suppliers ────────────────────────────────────────────────────
# delivery_qty_t     : tonnes per triggered delivery
# lead_time_mean_hr  : average hours from order to gate arrival
# reliability        : probability the delivery is on-time (vs. delayed)
# reorder_point_t    : trigger a replenishment order when stock falls below this
SUPPLIERS = {
    "clay": {
        "name":               "ClayMin Lda",
        "country":            "Portugal",
        "delivery_qty_t":     50.0,
        "lead_time_mean_hr":  36,
        "lead_time_std_hr":    6,
        "reliability":        0.92,
        "unit_cost_eur_t":    85,
        "reorder_point_t":    65,
        "max_stock_t":        260,
    },
    "feldspar": {
        "name":               "FeldsparCo S.L.",
        "country":            "Spain",
        "delivery_qty_t":     30.0,
        "lead_time_mean_hr":  42,
        "lead_time_std_hr":    8,
        "reliability":        0.88,
        "unit_cost_eur_t":    120,
        "reorder_point_t":    40,
        "max_stock_t":        150,
    },
    "silica": {
        "name":               "SilicaTech Lda",
        "country":            "Portugal",
        "delivery_qty_t":     25.0,
        "lead_time_mean_hr":  36,
        "lead_time_std_hr":    6,
        "reliability":        0.91,
        "unit_cost_eur_t":    95,
        "reorder_point_t":    32,
        "max_stock_t":        120,
    },
    "kaolin": {
        "name":               "KaolinMine S.A.",
        "country":            "Brazil",           # Overseas → long lead time
        "delivery_qty_t":     20.0,
        "lead_time_mean_hr":  72,
        "lead_time_std_hr":   16,
        "reliability":        0.82,               # Less reliable — distant supplier
        "unit_cost_eur_t":    110,
        "reorder_point_t":    22,
        "max_stock_t":        100,
    },
    "glaze": {
        "name":               "ChemGlaze GmbH",
        "country":            "Germany",
        "delivery_qty_t":     12.0,
        "lead_time_mean_hr":  72,
        "lead_time_std_hr":   14,
        "reliability":        0.85,
        "unit_cost_eur_t":    280,
        "reorder_point_t":    10,
        "max_stock_t":        55,
    },
}

# Initial raw-material inventory (tonnes) — approx 3 days of production supply
INITIAL_INVENTORY = {
    "clay":     90.0,
    "feldspar": 50.0,
    "silica":   40.0,
    "kaolin":   25.0,
    "glaze":    10.0,
}

# ── Finished-goods warehouse ──────────────────────────────────────────────────
FG_INITIAL_UNITS = {
    "ONE-PIECE-STD":  200,
    "TWO-PIECE-ECO":  150,
    "WALL-HUNG-PREM": 100,
}
FG_MAX_UNITS = {k: 5_000 for k in PRODUCTS}

# ── Customer demand ───────────────────────────────────────────────────────────
DEMAND = {
    "mean_orders_per_day": 5,
    "mean_order_units":    25,
    "std_order_units":     8,
    "min_order_units":     5,
    "std_lead_time_days":    7,    # standard service promise
    "express_lead_time_days": 3,
    "express_fraction":    0.20,
    "express_premium":     1.15,  # 15 % price uplift for express
}

CUSTOMERS = [
    "BuildCo Portugal", "Iberian Sanitary Distributors", "ConstructMax S.A.",
    "Mediterranean Build", "Porto Renovations", "Atlantic Contracts Ltd",
    "HomeStyle Iberia", "SaniPro Europe", "Lisbon Interiors",
    "Douro Construction Group",
]

# ── Quality parameters ────────────────────────────────────────────────────────
QUALITY = {
    "grade_a_rate":         0.75,   # Prime quality — full price
    "grade_b_rate":         0.15,   # Seconds — sold at a discount
    "reject_rate":          0.10,   # Scrapped (higher than tiles)
    "grade_b_price_factor": 0.65,
    # Functional testing pass rates
    "leak_test_pass_rate":  0.98,
    "flush_test_pass_rate": 0.97,
}

# ── Financial parameters ──────────────────────────────────────────────────────
FINANCIAL = {
    "energy_cost_per_batch_eur":      280,   # Gas + electricity per 50-unit batch (longer kiln)
    "labor_cost_per_shift_eur":     3_500,   # One 8-hour shift (more skilled labor)
    "shifts_per_day":                   3,
    "breakdown_repair_cost_eur":    2_500,   # Average cost per incident
    "stockout_penalty_eur_unit":       25,   # Lost margin + expediting cost per unit
    "holding_cost_pct_per_year":     0.20,   # 20 % of FG value per annum
}

# ── Scenario definitions ──────────────────────────────────────────────────────
SCENARIOS = {
    "baseline": {
        "label":       "Baseline",
        "description": "Normal 90-day operations — balanced supply & demand",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           None,   # (start_hr, end_hr) or None
    },
    "supply_disruption": {
        "label":       "Supply Disruption",
        "description": "KaolinMine S.A. — 35-day Brazilian port strike (Day 15–50)",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           (15 * HOURS_PER_DAY, 50 * HOURS_PER_DAY),
    },
    "demand_surge": {
        "label":       "Demand Surge",
        "description": "Summer construction boom — 30 % demand uplift across all products",
        "demand_factor":               1.30,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           None,
    },
    "optimised": {
        "label":       "Optimised",
        "description": "2nd tunnel kiln installed + 50 % safety stock uplift across all raw materials",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 1,      # Total kilns: 2
        "safety_stock_factor":         1.5,    # Reorder points × 1.5
        "kaolin_disruption":           None,
    },
}
