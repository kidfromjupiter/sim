"""
CeramicFactory — SimPy discrete-event simulation of SaniCer's supply chain.

Production pipeline (left → right):

  Raw materials (clay, kaolin, feldspar, silica)
        │
   [Slip Prep Lines]  ──────────────────── slip_buffer (Container)
        │
   [Pressure Casting] ──────────────────── cast_store (Store of ProductionBatch)
        │
   [Demolding & Drying (18h)] ──────────── demolded_store (Store)
        │
   [Fettling]  ──────────────────────────── fettled_store (Store)
        │
   [Spray Glazing] ←── glaze raw-mat ────── glazed_store (Store)
        │
   [Tunnel Kiln (24h)] ★ bottleneck ────── fired_store (Store)
        │
   [QC & Packaging]  ───────────────────── finished_goods[product] (Container)
        │
   Customer orders  ←── order_queue (Store)
"""

from __future__ import annotations

import math
import random
from typing import Dict, Tuple

import simpy

from .config import (
    BATCH_SIZE_UNITS, BODY_COMPOSITION, AVG_BODY_KG_UNIT,
    CUSTOMERS, DEMAND, FINANCIAL, FG_INITIAL_UNITS, FG_MAX_UNITS,
    HOURS_PER_DAY, INITIAL_INVENTORY, MACHINES, PRODUCTS,
    QUALITY, SCENARIOS, SUPPLIERS,
)
from .metrics import MetricsCollector
from .models import BreakdownEvent, CustomerOrder, ProductionBatch, SupplierDelivery


class CeramicFactory:
    """
    Full supply-chain model of SaniCer Sanitary Ware Industries.

    Usage::

        env     = simpy.Environment()
        factory = CeramicFactory(env, scenario="baseline", seed=42)
        factory.register_processes()
        env.run(until=SIM_DURATION)
        kpis = factory.metrics.compute_kpis(SIM_DAYS)
    """

    def __init__(
        self,
        env: simpy.Environment,
        scenario: str = "baseline",
        seed: int = 42,
    ) -> None:
        self.env      = env
        self.scenario = scenario
        self.scen     = SCENARIOS[scenario]

        random.seed(seed)

        # ── Raw-material inventory (tonnes) ───────────────────────────────────
        self.raw_mat: Dict[str, simpy.Container] = {}
        for mat, cfg in SUPPLIERS.items():
            init = INITIAL_INVENTORY[mat] * self.scen["safety_stock_factor"]
            init = min(init, cfg["max_stock_t"])
            self.raw_mat[mat] = simpy.Container(
                env, capacity=cfg["max_stock_t"], init=init
            )

        # ── Inter-stage buffers ───────────────────────────────────────────────
        self.slip_buffer    = simpy.Container(env, capacity=5_000, init=200)
        # Stores carry ProductionBatch objects so product type travels with the commode
        self.cast_store      = simpy.Store(env)
        self.demolded_store  = simpy.Store(env)
        self.fettled_store   = simpy.Store(env)
        self.glazed_store    = simpy.Store(env)
        self.fired_store     = simpy.Store(env)

        # ── Finished-goods warehouse (units) ──────────────────────────────────
        self.fg: Dict[str, simpy.Container] = {
            prod: simpy.Container(
                env,
                capacity=FG_MAX_UNITS[prod],
                init=FG_INITIAL_UNITS[prod],
            )
            for prod in PRODUCTS
        }

        # ── Machine resources ─────────────────────────────────────────────────
        self.machines: Dict[str, simpy.Resource] = {}
        for key, cfg in MACHINES.items():
            count = cfg["count"]
            if key == "kiln":
                count += self.scen["extra_kilns"]
            self.machines[key] = simpy.Resource(env, capacity=count)

        # ── Order queue (shared by multiple fulfilment workers) ───────────────
        self.order_queue = simpy.Store(env)

        # ── Metrics ───────────────────────────────────────────────────────────
        self.metrics = MetricsCollector(env)

        # ── Internal state ────────────────────────────────────────────────────
        self._pending_replen: Dict[str, int] = {m: 0 for m in SUPPLIERS}
        self._machine_busy_hr: Dict[str, float] = {k: 0.0 for k in MACHINES}
        self._daily_prod: Dict[str, float] = {p: 0.0 for p in PRODUCTS}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _proc_time(self, machine_key: str) -> Tuple[float, bool]:
        """
        Sample processing time for one batch on *machine_key*.

        Returns ``(duration_hours, had_breakdown)``.  If a breakdown occurs,
        ``duration_hours`` already includes the repair time so the caller
        just yields a single timeout.
        """
        cfg     = MACHINES[machine_key]
        rel     = self.scen["machine_reliability_factor"]
        base_t  = max(0.05, random.normalvariate(cfg["proc_mean_hr"], cfg["proc_std_hr"]))
        eff_mtbf = cfg["mtbf_hr"] * rel

        # Probability of at least one failure in *base_t* hours of operation
        p_fail  = 1.0 - math.exp(-base_t / eff_mtbf)
        if random.random() < p_fail:
            repair_t = random.expovariate(1.0 / cfg["mttr_hr"])
            event = BreakdownEvent(
                machine_id      = machine_key,
                machine_name    = cfg["name"],
                occurred_at     = self.env.now + base_t,
                repair_duration = repair_t,
                repair_cost_eur = FINANCIAL["breakdown_repair_cost_eur"],
            )
            self.metrics.breakdowns.append(event)
            return base_t + repair_t, True
        return base_t, False

    def _choose_product(self) -> str:
        """
        Weighted product selection for a new press batch.

        Biases toward products whose finished-goods level is below target
        so the factory naturally replenishes low-stock SKUs.
        """
        scores = {}
        for prod, cfg in PRODUCTS.items():
            level  = self.fg[prod].level
            target = FG_INITIAL_UNITS[prod] * 2.0
            deficit_bonus = max(0.0, (target - level) / target) * 0.25
            scores[prod]  = cfg["demand_share"] + deficit_bonus

        total = sum(scores.values())
        r, cum = random.random() * total, 0.0
        for prod, s in scores.items():
            cum += s
            if r <= cum:
                return prod
        return list(PRODUCTS.keys())[0]

    # =========================================================================
    # Supply-chain processes
    # =========================================================================

    def supply_monitor(self):
        """
        Inventory review every 4 hours.
        Triggers replenishment orders when stock falls below the reorder point.
        A maximum of 2 in-flight orders per material prevents over-ordering.
        """
        while True:
            yield self.env.timeout(4)

            for mat, cfg in SUPPLIERS.items():
                # ── Scenario: kaolin supply disruption ────────────────────────
                disruption = self.scen["kaolin_disruption"]
                if disruption and mat == "kaolin":
                    d_start, d_end = disruption
                    if d_start <= self.env.now <= d_end:
                        self.metrics.disruption_hours += 4
                        continue   # No kaolin orders during the strike

                reorder_pt = cfg["reorder_point_t"] * self.scen["safety_stock_factor"]
                if (
                    self.raw_mat[mat].level < reorder_pt
                    and self._pending_replen[mat] < 2
                ):
                    self._pending_replen[mat] += 1
                    self.env.process(self._supplier_delivery(mat))

    def _supplier_delivery(self, material: str):
        """
        Simulate one supplier delivery:
          1. Compute lead time (Normal, truncated at 4 h minimum).
          2. Apply reliability — unreliable suppliers add random delays.
          3. Arrive at factory gate and top up the raw-material container.
        """
        cfg        = SUPPLIERS[material]
        ordered_at = self.env.now
        rel_factor = self.scen["supplier_reliability_factor"]

        lead_t  = max(4.0, random.normalvariate(
            cfg["lead_time_mean_hr"], cfg["lead_time_std_hr"]
        ))
        eff_rel = cfg["reliability"] * rel_factor
        on_time = random.random() < eff_rel
        if not on_time:
            lead_t *= random.uniform(1.25, 2.50)   # Late delivery penalty

        yield self.env.timeout(lead_t)

        space   = self.raw_mat[material].capacity - self.raw_mat[material].level
        qty     = min(cfg["delivery_qty_t"], space)
        if qty > 0:
            yield self.raw_mat[material].put(qty)

        self.metrics.deliveries.append(SupplierDelivery(
            supplier_name   = cfg["name"],
            material        = material,
            quantity_tonnes = qty,
            unit_cost_eur_t = cfg["unit_cost_eur_t"],
            ordered_at      = ordered_at,
            delivered_at    = self.env.now,
            on_time         = on_time,
        ))
        self._pending_replen[material] -= 1

    # =========================================================================
    # Production stages
    # =========================================================================

    def slip_preparation(self):
        """
        Stage 1 — Slip preparation (ball milling + deflocculation + sieving).

        Consumes raw materials and produces ceramic slip.
        One SimPy process instance per slip-prep line.
        """
        BATCH = BATCH_SIZE_UNITS

        # Tonnes of each mineral consumed per batch
        mat_per_batch = {
            mat: BATCH * AVG_BODY_KG_UNIT * frac / 1000   # kg → t
            for mat, frac in BODY_COMPOSITION.items()
        }

        while True:
            # ── Wait until all raw materials are available ──────────────────
            while not all(
                self.raw_mat[m].level >= qty
                for m, qty in mat_per_batch.items()
            ):
                self.metrics.record_stall("slip_prep")
                yield self.env.timeout(1.0)   # poll every hour

            # ── Consume raw materials ────────────────────────────────────────
            # (Safe: we checked all levels; no yield between checks and gets,
            #  so no other body-prep process can interleave and steal stock.)
            for m, qty in mat_per_batch.items():
                yield self.raw_mat[m].get(qty)

            # ── Process on a slip-prep line ──────────────────────────────────
            with self.machines["slip_prep"].request() as req:
                yield req
                t, _ = self._proc_time("slip_prep")
                yield self.env.timeout(t)
                self._machine_busy_hr["slip_prep"] += t

            yield self.slip_buffer.put(BATCH)
            self.metrics.record_stage("slip_prep", BATCH)

    def pressure_casting(self):
        """
        Stage 2 — Pressure casting.

        Gets slip from the buffer, assigns a product type, produces a
        ProductionBatch object that carries the product identity downstream.
        One process per casting mold.
        """
        BATCH = BATCH_SIZE_UNITS
        while True:
            yield self.slip_buffer.get(BATCH)
            product = self._choose_product()

            with self.machines["casting"].request() as req:
                yield req
                t, _ = self._proc_time("casting")
                yield self.env.timeout(t)
                self._machine_busy_hr["casting"] += t

            batch = ProductionBatch(
                product      = product,
                quantity_units  = BATCH,
                created_at   = self.env.now,
                casting_done = self.env.now,
            )
            yield self.cast_store.put(batch)
            self.metrics.record_stage("casting", BATCH)

    def demolding_and_drying(self):
        while False:
            yield self.env.timeout(0)

    def fettling(self):
        while False:
            yield self.env.timeout(0)

    def spray_glazing(self):
        while False:
            yield self.env.timeout(0)

    def kiln_firing(self):
        while False:
            yield self.env.timeout(0)

    def finishing(self):
        while False:
            yield self.env.timeout(0)

    # Demand & order fulfilment
    # =========================================================================

    def demand_generator(self):
        while False:
            yield self.env.timeout(0)

    def order_fulfilment(self):
        while False:
            yield self.env.timeout(0)

    # Monitoring
    # =========================================================================

    def daily_recorder(self):
        while False:
            yield self.env.timeout(0)

    def _current_utilization(self) -> Dict[str, float]:
        return {}

    # Bootstrap
    # =========================================================================

    def register_processes(self) -> None:
        pass
