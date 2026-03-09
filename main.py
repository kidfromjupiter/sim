#!/usr/bin/env python3
"""
CeraSim — SaniCer Sanitary Ware Industries Supply Chain Simulator
==================================================================

Run all four scenarios (Baseline / Supply Disruption / Demand Surge / Optimised),
print per-scenario KPI tables and a cross-scenario comparison, then save
Matplotlib dashboards to ./reports/.

Usage
-----
    python main.py                  # run all 4 scenarios
    python main.py --scenario baseline   # single scenario
    python main.py --seed 99        # different random seed
    python main.py --no-charts      # skip chart generation
"""

import argparse
import time
from typing import Dict, Tuple

import simpy
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from cerasim.config import SCENARIOS, SIM_DAYS, SIM_DURATION, HOURS_PER_DAY
from cerasim.factory import CeramicFactory
from cerasim.reports import (
    console,
    plot_comparison_chart,
    plot_scenario_dashboard,
    print_banner,
    print_comparison_table,
    print_kpi_table,
)

REPORT_DIR = "reports"


# ─────────────────────────────────────────────────────────────────────────────
# Simulation runner
# ─────────────────────────────────────────────────────────────────────────────

def run_scenario(
    scenario_id: str,
    seed: int = 42,
    progress: Progress | None = None,
    task_id=None,
) -> Tuple[CeramicFactory, dict]:
    """
    Run one full 90-day simulation.

    The simulation is advanced in 24-hour steps so we can update a progress
    bar without multi-threading.
    """
    env     = simpy.Environment()
    factory = CeramicFactory(env, scenario=scenario_id, seed=seed)
    factory.register_processes()

    step = HOURS_PER_DAY   # advance one simulated day at a time
    for day in range(SIM_DAYS):
        env.run(until=(day + 1) * step)
        if progress and task_id is not None:
            progress.advance(task_id, 1)

    kpis = factory.metrics.compute_kpis(SIM_DAYS)
    return factory, kpis


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SaniCer Sanitary Ware Industries — Supply Chain Sim")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()),
                        default=None, help="Run a single scenario (default: all)")
    parser.add_argument("--seed",     type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--no-charts", action="store_true",
                        help="Skip Matplotlib chart generation")
    args = parser.parse_args()

    print_banner()

    scenario_ids = [args.scenario] if args.scenario else list(SCENARIOS.keys())
    results: Dict[str, Tuple[CeramicFactory, dict]] = {}

    # ── Run simulations with a progress bar ──────────────────────────────────
    console.print("[bold]Running simulations…[/bold]\n")
    wall_start = time.perf_counter()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=35),
        MofNCompleteColumn(),
        TextColumn("days"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        tasks = {}
        for sid in scenario_ids:
            label = SCENARIOS[sid]["label"]
            colour = {
                "baseline":          "cyan",
                "supply_disruption": "red",
                "demand_surge":      "yellow",
                "optimised":         "green",
            }.get(sid, "white")
            tasks[sid] = progress.add_task(
                f"[{colour}]{label:<22}[/{colour}]",
                total=SIM_DAYS,
            )

        for sid in scenario_ids:
            factory, kpis = run_scenario(
                sid, seed=args.seed,
                progress=progress, task_id=tasks[sid],
            )
            results[sid] = (factory, kpis)

    wall_elapsed = time.perf_counter() - wall_start
    console.print(
        f"\n[dim]All simulations finished in {wall_elapsed:.1f}s "
        f"(simulated {SIM_DAYS * len(scenario_ids)} factory-days)[/dim]\n"
    )

    # ── Print per-scenario KPI tables ─────────────────────────────────────────
    for sid in scenario_ids:
        _, kpis = results[sid]
        print_kpi_table(sid, kpis)

    # ── Print cross-scenario comparison ──────────────────────────────────────
    if len(results) > 1:
        print_comparison_table(results)

    # ── Generate Matplotlib dashboards ───────────────────────────────────────
    if not args.no_charts:
        console.print("[bold]Generating charts…[/bold]")
        saved = []
        for sid, (factory, kpis) in results.items():
            path = plot_scenario_dashboard(factory, kpis, sid, REPORT_DIR)
            if path:
                saved.append(path)
                console.print(f"  [green]✓[/green]  {path}")

        if len(results) > 1:
            path = plot_comparison_chart(results, REPORT_DIR)
            if path:
                saved.append(path)
                console.print(f"  [green]✓[/green]  {path}")

        console.print()

    # ── Key insights ──────────────────────────────────────────────────────────
    _print_insights(results)


def _print_insights(results: Dict[str, Tuple]) -> None:
    """Print a short auto-generated insight block for stakeholders."""
    if "baseline" not in results:
        return

    base_kpis = results["baseline"][1]
    console.rule("[bold green]Key Insights[/bold green]")

    insights = []

    # Bottleneck
    insights.append(
        "🔩  [bold]Tunnel kiln is the production bottleneck.[/bold]  "
        "With 1 tunnel kiln at 24 h/batch, theoretical max throughput is "
        "1 batch/day (50 units/day).  All upstream stages have spare capacity."
    )

    # Fill rate
    fr = base_kpis["fill_rate_pct"]
    colour = "green" if fr >= 90 else "yellow"
    insights.append(
        f"📦  Baseline quantity fill rate: [{colour}]{fr:.1f}%[/{colour}].  "
        "Service level is driven by finished-goods buffer depth and kiln throughput."
    )

    # Supply disruption impact
    if "supply_disruption" in results:
        sd_kpis = results["supply_disruption"][1]
        prod_loss = base_kpis["total_production_units"] - sd_kpis["total_production_units"]
        rev_loss  = base_kpis["revenue_eur"]          - sd_kpis["revenue_eur"]
        insights.append(
            f"⚠️  [bold]35-day kaolin port strike[/bold] causes "
            f"[red]{prod_loss:,.0f} units[/red] production loss "
            f"(€[red]{rev_loss:,.0f}[/red] revenue impact).  "
            "Consider dual-sourcing kaolin or holding 4-week safety stock."
        )

    # Demand surge
    if "demand_surge" in results:
        ds_kpis = results["demand_surge"][1]
        so = ds_kpis["stockout_events"]
        insights.append(
            f"📈  [bold]30 % demand surge[/bold] generates "
            f"[yellow]{so}[/yellow] stockout events.  "
            "Finished-goods buffer is insufficient to absorb peak demand — "
            "consider building strategic stock ahead of summer season."
        )

    # Optimised
    if "optimised" in results and "baseline" in results:
        opt_kpis  = results["optimised"][1]
        prod_gain = opt_kpis["total_production_units"] - base_kpis["total_production_units"]
        rev_gain  = opt_kpis["revenue_eur"]          - base_kpis["revenue_eur"]
        insights.append(
            f"✅  [bold]Adding a 2nd tunnel kiln + 50 % safety-stock uplift[/bold] "
            f"increases output by [green]{prod_gain:,.0f} units[/green] "
            f"(+€[green]{rev_gain:,.0f}[/green]) over 90 days.  "
            f"Kiln CAPEX ≈ €3.5 M — simple payback ≈ "
            f"{3_500_000 / max(1, rev_gain / 90 * 365):.1f} years."
        )

    for ins in insights:
        console.print(f"  {ins}")
        console.print()


if __name__ == "__main__":
    main()
