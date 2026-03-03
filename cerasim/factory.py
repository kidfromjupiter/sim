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
        return MACHINES[machine_key]["proc_mean_hr"], False

    def _choose_product(self) -> str:
        return next(iter(PRODUCTS))

    # Supply-chain processes
    # =========================================================================

    def supply_monitor(self):
        while False:
            yield self.env.timeout(0)

    def _supplier_delivery(self, material: str):
        yield self.env.timeout(0)

    # Production stages
    # =========================================================================

    def slip_preparation(self):
        while False:
            yield self.env.timeout(0)

    def pressure_casting(self):
        while False:
            yield self.env.timeout(0)

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
