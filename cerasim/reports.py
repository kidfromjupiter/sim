"""
Rich console output and Matplotlib dashboard generation.
"""

from __future__ import annotations

import os
from typing import Dict, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import (
    FACTORY_EMPLOYEES, FACTORY_FOUNDED, FACTORY_LOCATION, FACTORY_NAME,
    MACHINES, PRODUCTS, SCENARIOS, SUPPLIERS, SIM_DAYS,
)

console = Console()

# Colour palette
PRODUCT_COLORS = {p: PRODUCTS[p]["color"] for p in PRODUCTS}
SCENARIO_COLORS = {
    "baseline":          "#2E86AB",
    "supply_disruption": "#E63946",
    "demand_surge":      "#F4A261",
    "optimised":         "#2EC4B6",
}


# ─────────────────────────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────────────────────────

def print_banner() -> None:
    lines = [
        f"[bold white]{FACTORY_NAME}[/bold white]",
        f"[dim]{FACTORY_LOCATION}  ·  est. {FACTORY_FOUNDED}  ·  {FACTORY_EMPLOYEES} employees[/dim]",
        "",
        "[bold cyan]Supply Chain Discrete-Event Simulation[/bold cyan]",
        f"[dim]Powered by CeraSim v1.0  ·  SimPy engine  ·  {SIM_DAYS}-day horizon[/dim]",
    ]
    console.print(Panel("\n".join(lines), style="bold blue", expand=False))
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
# Per-scenario KPI summary
# ─────────────────────────────────────────────────────────────────────────────

def print_kpi_table(scenario_id: str, kpis: dict) -> None:
    scen = SCENARIOS[scenario_id]
    title = f"[bold]{scen['label']}[/bold]  —  {scen['description']}"
    console.rule(title)

    t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold magenta")
    t.add_column("KPI",        style="cyan",  min_width=32)
    t.add_column("Value",      style="white", justify="right", min_width=16)
    t.add_column("Assessment", style="dim",   min_width=20)

    def row(label, value, assessment=""):
        t.add_row(label, value, assessment)

    def pct_style(v, good_above=90):
        colour = "green" if v >= good_above else ("yellow" if v >= 75 else "red")
        return f"[{colour}]{v:.1f}%[/{colour}]"

    # Production
    row("── Production ──────────────────", "", "")
    row("  Total output (units)",
        f"{kpis['total_production_units']:>12,.0f}",
        f"avg {kpis['avg_daily_m2']:,.0f} units/day")
    row("  Grade A (units)",
        f"{kpis['grade_a_units']:>12,.0f}",
        f"{kpis['grade_a_units']/max(1,kpis['total_production_units'])*100:.1f}% of total")
    row("  Grade B / Seconds (units)",
        f"{kpis['grade_b_units']:>12,.0f}", "")
    row("  Scrap (units)",
        f"{kpis['reject_units']:>12,.0f}", "")
    row("  Avg batch cycle time",
        f"{kpis['avg_cycle_time_hr']:>10.1f} h", "")
    row("  Total batches completed",
        f"{kpis['total_batches']:>12,d}", "")

    # Orders
    row("── Orders ──────────────────────", "", "")
    row("  Orders received",
        f"{kpis['total_orders']:>12,d}", "")
    row("  Total demand (units)",
        f"{kpis['total_ordered_m2']:>12,.0f}", "")
    row("  Quantity fill rate",
        pct_style(kpis['fill_rate_pct']), "")
    row("  Order completion rate",
        pct_style(kpis['complete_pct']), "")
    row("  On-time delivery rate",
        pct_style(kpis['otd_rate_pct']), "")
    row("  Avg customer lead time",
        f"{kpis['avg_lead_time_days']:>10.2f} days", "")
    row("  Stockout events",
        f"{kpis['stockout_events']:>12,d}",
        "[red]critical[/red]" if kpis["stockout_events"] > 10 else "")
    row("  Partial fulfilments",
        f"{kpis['partial_fulfils']:>12,d}", "")

    # Machines
    row("── Reliability ─────────────────", "", "")
    row("  Total breakdowns",
        f"{kpis['total_breakdowns']:>12,d}", "")
    row("  Total downtime (h)",
        f"{kpis['breakdown_hours']:>10.1f} h",
        f"{kpis['breakdown_hours']/max(1,SIM_DAYS*24)*100:.1f}% of sim time")
    row("  Kaolin disruption hrs",
        f"{kpis['disruption_hours']:>10.1f} h", "")
    row("  Body-prep stall hrs",
        f"{kpis['slip_prep_stall_hrs']:>12,d}", "")
    row("  Glaze-line stall hrs",
        f"{kpis['glaze_stall_hrs']:>12,d}", "")

    # Supplier
    row("── Supply chain ────────────────", "", "")
    row("  Total deliveries received",
        f"{kpis['total_deliveries']:>12,d}", "")
    row("  Avg supplier lead time",
        f"{kpis['avg_supplier_lead_time_hr']:>10.1f} h", "")
    row("  On-time delivery rate",
        pct_style(kpis['on_time_delivery_pct']), "")

    # Financial
    row("── Financial (90-day) ──────────", "", "")
    row("  Revenue",
        f"€{kpis['revenue_eur']:>14,.0f}", "")
    row("  Raw material cost",
        f"€{kpis['raw_mat_cost_eur']:>14,.0f}", "")
    row("  Energy cost",
        f"€{kpis['energy_cost_eur']:>14,.0f}", "")
    row("  Labour cost",
        f"€{kpis['labor_cost_eur']:>14,.0f}", "")
    row("  Breakdown cost",
        f"€{kpis['breakdown_cost_eur']:>14,.0f}", "")
    row("  Stockout penalty",
        f"€{kpis['stockout_cost_eur']:>14,.0f}", "")
    row("  Gross profit",
        f"€{kpis['gross_profit_eur']:>14,.0f}",
        f"margin {kpis['gross_margin_pct']:.1f}%")
    row("  Net profit",
        f"€{kpis['net_profit_eur']:>14,.0f}",
        f"margin {kpis['net_margin_pct']:.1f}%")

    console.print(t)
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
# Cross-scenario comparison table
# ─────────────────────────────────────────────────────────────────────────────

def print_comparison_table(results: Dict[str, Tuple]) -> None:
    console.rule("[bold yellow]Scenario Comparison (90-day summary)[/bold yellow]")

    t = Table(box=box.DOUBLE_EDGE, show_header=True, header_style="bold yellow")
    t.add_column("Metric", style="cyan", min_width=30)

    scen_ids = list(results.keys())
    for sid in scen_ids:
        colour = SCENARIO_COLORS.get(sid, "white")
        t.add_column(
            Text(SCENARIOS[sid]["label"], style=f"bold {colour}"),
            justify="right", min_width=16,
        )

    def _fmt(v, fmt=","):
        if isinstance(v, float):
            if fmt == "pct":
                colour = "green" if v >= 90 else ("yellow" if v >= 75 else "red")
                return f"[{colour}]{v:.1f}%[/{colour}]"
            return f"{v:,.0f}"
        return str(v)

    kpis_list = [results[s][1] for s in scen_ids]

    rows = [
        ("Output (units)",          "total_production_m2",  ","),
        ("Avg daily output (units)", "avg_daily_m2",          ","),
        ("Fill rate",            "fill_rate_pct",         "pct"),
        ("On-time delivery",     "otd_rate_pct",          "pct"),
        ("Avg lead time (days)", "avg_lead_time_days",    "f2"),
        ("Stockout events",      "stockout_events",        ","),
        ("Total breakdowns",     "total_breakdowns",       ","),
        ("Downtime (h)",         "breakdown_hours",        ","),
        ("Revenue (€)",          "revenue_eur",            ","),
        ("Net profit (€)",       "net_profit_eur",         ","),
        ("Net margin",           "net_margin_pct",        "pct"),
        ("Kaolin stall (h)",     "disruption_hours",       ","),
    ]

    for label, key, fmt in rows:
        vals = []
        for k in kpis_list:
            v = k.get(key, 0)
            if fmt == "pct":
                colour = "green" if v >= 90 else ("yellow" if v >= 75 else "red")
                vals.append(f"[{colour}]{v:.1f}%[/{colour}]")
            elif fmt == "f2":
                vals.append(f"{v:.2f}")
            else:
                vals.append(f"{v:,.0f}")
        t.add_row(label, *vals)

    console.print(t)
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
# Matplotlib dashboard
# ─────────────────────────────────────────────────────────────────────────────

def plot_scenario_dashboard(factory, kpis: dict, scenario_id: str, out_dir: str) -> str:
    return ""


def plot_comparison_chart(results: Dict[str, Tuple], out_dir: str) -> str:
    return ""
