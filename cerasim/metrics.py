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
        k: dict = {}

        # ── Production ────────────────────────────────────────────────────────
        batches = self.completed_batches
        if batches:
            total_a   = sum(b.grade_a_units for b in batches)
            total_b   = sum(b.grade_b_units for b in batches)
            total_rej = sum(b.reject_units  for b in batches)
            total_ok  = total_a + total_b
            k["total_production_units"] = total_ok
            k["avg_daily_m2"]        = total_ok / sim_days
            k["grade_a_units"]          = total_a
            k["grade_b_units"]          = total_b
            k["reject_units"]           = total_rej
            k["total_batches"]       = len(batches)
            cts = [b.cycle_time_hr for b in batches if b.cycle_time_hr is not None]
            k["avg_cycle_time_hr"]   = sum(cts) / len(cts) if cts else 0.0
        else:
            for key in ("total_production_units", "avg_daily_m2", "grade_a_units",
                        "grade_b_units", "reject_units", "total_batches", "avg_cycle_time_hr"):
                k[key] = 0.0

        # Production by product
        k["production_by_product"] = {}
        for prod in PRODUCTS:
            pb = [b for b in batches if b.product == prod]
            k["production_by_product"][prod] = sum(b.saleable_units for b in pb)

        # ── Orders ────────────────────────────────────────────────────────────
        orders = self.orders
        if orders:
            tot_ord  = sum(o.quantity_units    for o in orders)
            tot_ful  = sum(o.fulfilled_qty  for o in orders)
            complete = [o for o in orders if o.is_complete]
            overdue  = [o for o in complete if o.is_overdue]

            k["total_orders"]        = len(orders)
            k["total_ordered_m2"]    = tot_ord
            k["total_fulfilled_m2"]  = tot_ful
            k["fill_rate_pct"]       = (tot_ful / tot_ord * 100) if tot_ord else 0.0
            k["complete_pct"]        = (len(complete) / len(orders) * 100)
            k["otd_rate_pct"]        = ((1 - len(overdue) / len(complete)) * 100
                                        if complete else 100.0)
            k["stockout_events"]     = len(self.stockout_events)
            k["partial_fulfils"]     = self.partial_fulfils

            lts = [(o.fulfilled_at - o.created_at) / HOURS_PER_DAY
                   for o in orders if o.fulfilled_at is not None]
            k["avg_lead_time_days"]  = sum(lts) / len(lts) if lts else 0.0
        else:
            for key in ("total_orders", "total_ordered_m2", "total_fulfilled_m2",
                        "fill_rate_pct", "complete_pct", "otd_rate_pct",
                        "stockout_events", "partial_fulfils", "avg_lead_time_days"):
                k[key] = 0.0

        # ── Financial ─────────────────────────────────────────────────────────
        rev_a = sum(
            b.grade_a_units * PRODUCTS[b.product]["price_eur_unit"]
            for b in batches
        )
        rev_b = sum(
            b.grade_b_units * PRODUCTS[b.product]["price_eur_unit"] * QUALITY["grade_b_price_factor"]
            for b in batches
        )
        raw_mat_cost   = sum(d.total_cost_eur  for d in self.deliveries)
        energy_cost    = k["total_batches"] * FINANCIAL["energy_cost_per_batch_eur"]
        labor_cost     = (sim_days * FINANCIAL["shifts_per_day"]
                          * FINANCIAL["labor_cost_per_shift_eur"])
        breakdown_cost = len(self.breakdowns) * FINANCIAL["breakdown_repair_cost_eur"]
        stockout_cost  = (sum(e["quantity_units"] for e in self.stockout_events)
                          * FINANCIAL["stockout_penalty_eur_unit"])

        total_revenue = rev_a + rev_b
        total_cost    = raw_mat_cost + energy_cost + labor_cost + breakdown_cost + stockout_cost

        k["revenue_eur"]       = total_revenue
        k["raw_mat_cost_eur"]  = raw_mat_cost
        k["energy_cost_eur"]   = energy_cost
        k["labor_cost_eur"]    = labor_cost
        k["breakdown_cost_eur"]= breakdown_cost
        k["stockout_cost_eur"] = stockout_cost
        k["total_cost_eur"]    = total_cost
        k["gross_profit_eur"]  = total_revenue - raw_mat_cost - energy_cost
        k["net_profit_eur"]    = total_revenue - total_cost
        k["gross_margin_pct"]  = ((k["gross_profit_eur"] / total_revenue * 100)
                                  if total_revenue else 0.0)
        k["net_margin_pct"]    = ((k["net_profit_eur"] / total_revenue * 100)
                                  if total_revenue else 0.0)

        # ── Machine reliability ────────────────────────────────────────────────
        k["total_breakdowns"]   = len(self.breakdowns)
        k["breakdown_hours"]    = sum(b.repair_duration for b in self.breakdowns)
        k["disruption_hours"]   = self.disruption_hours

        # Breakdowns per machine type
        k["breakdowns_by_machine"] = {}
        for mkey in MACHINES:
            k["breakdowns_by_machine"][mkey] = sum(
                1 for b in self.breakdowns if b.machine_id == mkey
            )

        # ── Supplier performance ───────────────────────────────────────────────
        if self.deliveries:
            k["total_deliveries"]          = len(self.deliveries)
            k["avg_supplier_lead_time_hr"] = (
                sum(d.lead_time_hr for d in self.deliveries) / len(self.deliveries)
            )
            k["on_time_delivery_pct"] = (
                sum(1 for d in self.deliveries if d.on_time) / len(self.deliveries) * 100
            )
        else:
            k["total_deliveries"]          = 0
            k["avg_supplier_lead_time_hr"] = 0.0
            k["on_time_delivery_pct"]      = 0.0

        # ── Stall / raw-material shortage ────────────────────────────────────
        k["slip_prep_stall_hrs"] = len(self.stall_log["slip_prep"])
        k["glaze_stall_hrs"]     = len(self.stall_log["glazing"])

        return k
