"""Metrics collection and KPI computation."""

from __future__ import annotations
from typing import Dict, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import simpy

from .config import (
    PRODUCTS, SUPPLIERS, MACHINES, QUALITY, FINANCIAL,
    HOURS_PER_DAY, BATCH_SIZE_UNITS,
)
from .models import ProductionBatch, CustomerOrder, SupplierDelivery, BreakdownEvent


class MetricsCollector:
    """Accumulates every event that happens during a simulation run."""

    def __init__(self, env: "simpy.Environment") -> None:
        self.env = env

        # ── Event logs ────────────────────────────────────────────────────────
        self.completed_batches: List[ProductionBatch]  = []
        self.orders:            List[CustomerOrder]    = []
        self.deliveries:        List[SupplierDelivery] = []
        self.breakdowns:        List[BreakdownEvent]   = []

        # ── Aggregate counters ────────────────────────────────────────────────
        self.stockout_events:    List[dict] = []   # {"time", "product", "quantity_units"}
        self.partial_fulfils:    int        = 0
        self.disruption_hours:   float      = 0.0

        # ── Per-stage completion log: (sim_time, units_produced) ─────────────────
        self.stage_log: Dict[str, List[Tuple[float, int]]] = {
            s: [] for s in ["slip_prep", "casting", "demolding", "fettling", "glazing", "kiln", "finishing"]
        }

        # ── Raw-material stall log (times when production was waiting for RM) ─
        self.stall_log: Dict[str, List[float]] = {
            "slip_prep": [],
            "glazing":   [],
        }

        # ── Daily snapshots (added every 24 h by daily_recorder) ─────────────
        self.daily_snapshots: List[dict] = []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def record_stage(self, stage: str, qty_units: int) -> None:
        self.stage_log[stage].append((self.env.now, qty_units))

    def record_stall(self, stage: str) -> None:
        """Record a 1-hour stall in slip_prep or glazing due to missing material."""
        log = self.stall_log[stage]
        # De-bounce: only log once per hour
        if not log or (self.env.now - log[-1]) >= 1.0:
            log.append(self.env.now)

    # ── KPI computation ───────────────────────────────────────────────────────

    def compute_kpis(self, sim_days: int) -> dict:
        return {}
