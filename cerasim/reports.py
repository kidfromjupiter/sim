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

def _style_ax(ax, title):
    ax.set_title(title, fontsize=9, fontweight="bold", pad=6)
    ax.tick_params(labelsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)


def plot_scenario_dashboard(factory, kpis: dict, scenario_id: str, out_dir: str) -> str:
    """
    Generate a 3×2 matplotlib dashboard for a single scenario.
    Returns the saved file path.
    """
    snaps = factory.metrics.daily_snapshots
    if not snaps:
        return ""

    days         = [s["day"]   for s in snaps]
    mat_names    = list(SUPPLIERS.keys())
    prod_names   = list(PRODUCTS.keys())

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    fig.suptitle(
        f"{FACTORY_NAME}  ·  {SCENARIOS[scenario_id]['label']}\n"
        f"{SCENARIOS[scenario_id]['description']}",
        fontsize=11, fontweight="bold", y=1.01,
    )
    plt.subplots_adjust(hspace=0.45, wspace=0.35)

    # ── (0,0) Raw material inventory ──────────────────────────────────────
    ax = axes[0][0]
    mat_colors = ["#8B4513", "#DAA520", "#708090", "#4682B4", "#48A999"]
    for mat, col in zip(mat_names, mat_colors):
        vals = [s["raw_mat"][mat] for s in snaps]
        ax.plot(days, vals, label=mat.capitalize(), color=col, linewidth=1.4)
        reorder = SUPPLIERS[mat]["reorder_point_t"]
        ax.axhline(reorder, color=col, linewidth=0.6, linestyle="--", alpha=0.5)

    # Mark kaolin disruption
    disruption = SCENARIOS[scenario_id]["kaolin_disruption"]
    if disruption:
        d_s = disruption[0] / 24
        d_e = disruption[1] / 24
        ax.axvspan(d_s, d_e, color="#E63946", alpha=0.12, label="Disruption")

    ax.set_ylabel("Stock (tonnes)", fontsize=8)
    ax.set_xlabel("Day", fontsize=8)
    ax.legend(fontsize=6, ncol=2, loc="upper right")
    _style_ax(ax, "Raw Material Inventory")

    # ── (0,1) Daily production by product ──────────────────────────────────
    ax = axes[0][1]
    bottom = np.zeros(len(days))
    for prod in prod_names:
        vals = np.array([s["produced_m2"].get(prod, 0) for s in snaps])
        ax.bar(days, vals, bottom=bottom,
               color=PRODUCT_COLORS[prod], label=prod, alpha=0.85, width=0.9)
        bottom += vals
    ax.set_ylabel("units / day", fontsize=8)
    ax.set_xlabel("Day", fontsize=8)
    ax.legend(fontsize=6, loc="lower right")
    _style_ax(ax, "Daily Production by Product")

    # ── (0,2) Finished-goods warehouse levels ───────────────────────────────
    ax = axes[0][2]
    for prod in prod_names:
        vals = [s["fg"][prod] for s in snaps]
        ax.plot(days, vals, color=PRODUCT_COLORS[prod],
                label=prod, linewidth=1.4)
    ax.set_ylabel("Stock (units)", fontsize=8)
    ax.set_xlabel("Day", fontsize=8)
    ax.legend(fontsize=6)
    _style_ax(ax, "Finished-Goods Warehouse")

    # ── (1,0) Machine utilisation (final cumulative) ────────────────────────
    ax = axes[1][0]
    final_util = snaps[-1]["utilization"]
    mach_labels = [MACHINES[k]["name"].replace(" ", "\n") for k in MACHINES]
    util_vals   = [final_util.get(k, 0) * 100 for k in MACHINES]
    bar_cols    = ["#2E86AB", "#A23B72", "#F18F01", "#E63946", "#2EC4B6"]
    bars = ax.barh(mach_labels, util_vals, color=bar_cols, alpha=0.85)
    ax.axvline(85, color="red", linewidth=1.0, linestyle="--", alpha=0.7, label="85 % threshold")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Utilisation (%)", fontsize=8)
    for bar, v in zip(bars, util_vals):
        ax.text(v + 1, bar.get_y() + bar.get_height() / 2,
                f"{v:.0f}%", va="center", fontsize=7)
    ax.legend(fontsize=6)
    _style_ax(ax, "Machine Utilisation (cumulative)")

    # ── (1,1) Rolling 7-day order fill rate ────────────────────────────────
    ax = axes[1][1]
    orders = factory.metrics.orders
    if orders:
        # Bin fulfilled units and ordered units by day
        daily_ord  = np.zeros(SIM_DAYS + 1)
        daily_ful  = np.zeros(SIM_DAYS + 1)
        for o in orders:
            d = int(o.created_at / 24)
            if d <= SIM_DAYS:
                daily_ord[d] += o.quantity_m2
                daily_ful[d] += o.fulfilled_qty

        rolling_rate = []
        for i in range(len(daily_ord)):
            window_ord = daily_ord[max(0, i-6):i+1].sum()
            window_ful = daily_ful[max(0, i-6):i+1].sum()
            rolling_rate.append(
                (window_ful / window_ord * 100) if window_ord > 0 else 100.0
            )
        ax.plot(range(len(rolling_rate)), rolling_rate,
                color=SCENARIO_COLORS[scenario_id], linewidth=1.6)
        ax.axhline(95, color="green", linewidth=0.8, linestyle="--", alpha=0.6, label="95% target")
        ax.set_ylim(0, 105)
        ax.set_ylabel("Fill rate (%)", fontsize=8)
        ax.set_xlabel("Day", fontsize=8)
        ax.legend(fontsize=6)
    _style_ax(ax, "7-day Rolling Order Fill Rate")

    # ── (1,2) Cumulative revenue vs cost ───────────────────────────────────
    ax = axes[1][2]
    batches = factory.metrics.completed_batches
    if batches:
        # Sort by finished_at
        sorted_b = sorted(batches, key=lambda b: b.finished_at or 0)
        times    = [(b.finished_at or 0) / 24 for b in sorted_b]
        cum_rev  = np.cumsum([
            b.grade_a_m2 * PRODUCTS[b.product]["price_eur_m2"] +
            b.grade_b_m2 * PRODUCTS[b.product]["price_eur_m2"] * 0.65
            for b in sorted_b
        ])
        # Approximate cumulative cost (raw mat only — for clarity)
        cum_cost = np.cumsum([
            b.quantity_m2 * 2.40   # approx €/units raw material (see config comments)
            for b in sorted_b
        ])
        ax.fill_between(times, cum_rev / 1e6, cum_cost / 1e6,
                        alpha=0.25, color="green", label="Gross profit")
        ax.plot(times, cum_rev  / 1e6, color="#2EC4B6",  linewidth=1.5, label="Revenue")
        ax.plot(times, cum_cost / 1e6, color="#E63946",  linewidth=1.5, linestyle="--",
                label="Raw mat. cost")
        ax.set_ylabel("€ millions", fontsize=8)
        ax.set_xlabel("Day", fontsize=8)
        ax.legend(fontsize=6)
    _style_ax(ax, "Cumulative Revenue vs. Raw Material Cost")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"dashboard_{scenario_id}.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_comparison_chart(results: Dict[str, Tuple], out_dir: str) -> str:
    """
    Side-by-side bar chart comparing the 4 scenarios on 6 key KPIs.
    Returns the saved file path.
    """
    scen_ids  = list(results.keys())
    labels    = [SCENARIOS[s]["label"] for s in scen_ids]
    colors    = [SCENARIO_COLORS[s] for s in scen_ids]

    metrics_to_compare = [
        ("avg_daily_m2",        "Avg Daily Production\n(units/day)",     None),
        ("fill_rate_pct",       "Order Fill Rate\n(%)",               95),
        ("otd_rate_pct",        "On-Time Delivery\n(%)",              95),
        ("total_breakdowns",    "Machine\nBreakdowns",                None),
        ("net_profit_eur",      "Net Profit (€)",                     None),
        ("stockout_events",     "Stockout Events",                    None),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    fig.suptitle(
        f"{FACTORY_NAME}  ·  90-Day Scenario Comparison",
        fontsize=12, fontweight="bold",
    )
    plt.subplots_adjust(hspace=0.55, wspace=0.40)

    for idx, (key, title, target) in enumerate(metrics_to_compare):
        ax   = axes[idx // 3][idx % 3]
        vals = [results[s][1].get(key, 0) for s in scen_ids]
        bars = ax.bar(labels, vals, color=colors, alpha=0.85, edgecolor="white")

        if target is not None:
            ax.axhline(target, color="red", linewidth=1.0,
                       linestyle="--", alpha=0.7, label=f"Target {target}")
            ax.legend(fontsize=6)

        for bar, v in zip(bars, vals):
            fmt = f"{v:,.0f}" if abs(v) >= 100 else f"{v:.1f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.01,
                fmt, ha="center", va="bottom", fontsize=7,
            )

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=7, rotation=15, ha="right")
        _style_ax(ax, title)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "scenario_comparison.png")
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return path
