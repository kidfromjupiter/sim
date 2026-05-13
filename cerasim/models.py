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
