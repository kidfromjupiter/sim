"""Data-model classes shared across the simulation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import uuid


def _short_id() -> str:
    return uuid.uuid4().hex[:8].upper()


@dataclass
class ProductionBatch:
    """Tracks a single batch of commodes from raw material through to packaging."""

    batch_id:     str   = field(default_factory=_short_id)
    product:      str   = ""
    quantity_units: int = 0
    created_at:   float = 0.0          # simulation time (hours)

    # Stage-completion timestamps (set as batch moves through pipeline)
    casting_done:  Optional[float] = None
    demolded_at:   Optional[float] = None
    fettled_at:    Optional[float] = None
    glazing_done:  Optional[float] = None
    firing_done:   Optional[float] = None
    finished_at:   Optional[float] = None

    # Quality outcomes (set in the finishing stage)
    grade_a_units:  int = 0
    grade_b_units:  int = 0
    reject_units:   int = 0

    # Functional testing results
    leak_test_pass:  int = 0
    flush_test_pass: int = 0

    @property
    def cycle_time_hr(self) -> Optional[float]:
        """End-to-end production time from batch creation to packaging."""
        if self.finished_at is not None:
            return self.finished_at - self.created_at
        return None

    @property
    def saleable_units(self) -> int:
        return self.grade_a_units + self.grade_b_units


@dataclass
class CustomerOrder:
    """A purchase order for commodes from a customer."""

    order_id:     str   = field(default_factory=lambda: f"ORD-{_short_id()}")
    customer:     str   = ""
    product:      str   = ""
    quantity_units: int = 0
    is_express:   bool  = False
    created_at:   float = 0.0
    due_at:       float = 0.0
    unit_price:   float = 0.0          # €/unit

    # Filled in during / after fulfilment
    fulfilled_qty: int            = 0
    fulfilled_at:  Optional[float] = None

    @property
    def is_complete(self) -> bool:
        return self.fulfilled_qty >= self.quantity_units

    @property
    def is_overdue(self) -> bool:
        return self.fulfilled_at is not None and self.fulfilled_at > self.due_at

    @property
    def revenue_eur(self) -> float:
        return self.fulfilled_qty * self.unit_price

    @property
    def fill_fraction(self) -> float:
        return min(1.0, self.fulfilled_qty / self.quantity_units) if self.quantity_units > 0 else 0.0


@dataclass
class SupplierDelivery:
    """A raw-material delivery that arrived at the factory gate."""

    delivery_id:      str   = field(default_factory=lambda: f"DEL-{_short_id()}")
    supplier_name:    str   = ""
    material:         str   = ""
    quantity_tonnes:  float = 0.0
    unit_cost_eur_t:  float = 0.0
    ordered_at:       float = 0.0
    delivered_at:     float = 0.0
    on_time:          bool  = True

    @property
    def total_cost_eur(self) -> float:
        return self.quantity_tonnes * self.unit_cost_eur_t

    @property
    def lead_time_hr(self) -> float:
        return self.delivered_at - self.ordered_at
