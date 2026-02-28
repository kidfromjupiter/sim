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
