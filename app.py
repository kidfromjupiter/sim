import os
import streamlit as st
import pandas as pd
from main import run_scenario, REPORT_DIR
from cerasim.config import SCENARIOS, SIM_DAYS
from cerasim.reports import plot_scenario_dashboard, plot_comparison_chart

st.set_page_config(page_title="CeraSim Dashboard", layout="wide")

class GlobalStreamlitProgress:
    """A minimal adapter to replace Rich's Progress bar with Streamlit's."""
    def __init__(self, st_bar, total_steps):
        self.st_bar = st_bar
        self.current = 0
        self.total_steps = total_steps
        
    def advance(self, task_id, advance_by=1):
        self.current += advance_by
        # Update streamlit progress bar safely (0.0 to 1.0)
        self.st_bar.progress(min(self.current / max(1, self.total_steps), 1.0))

def main():
    st.title("🏭 SaniCer Supply Chain Simulator")

    with st.sidebar:
        st.header("Simulation Settings")
        scenario_options = list(SCENARIOS.keys())
        # Provide user friendly labels for scenarios in selectbox
        selected_label = st.selectbox(
            "Select Scenario", 
            ["All Scenarios"] + [SCENARIOS[k]["label"] for k in scenario_options]
        )
        
        # Map back to scenario ID
        if selected_label == "All Scenarios":
            selected_scenario = "All"
        else:
            selected_scenario = next(k for k in scenario_options if SCENARIOS[k]["label"] == selected_label)
            
        seed = st.number_input("Random Seed", value=42, step=1)
        run_btn = st.button("Run Simulation", type="primary")

    if run_btn:
        to_run = scenario_options if selected_scenario == "All" else [selected_scenario]
        results = {}
        
        st.write("Running simulation(s)...")
        progress_bar = st.progress(0.0)
        
        total_days = SIM_DAYS * len(to_run)
        st_prog = GlobalStreamlitProgress(progress_bar, total_days)

        for sid in to_run:
            with st.spinner(f"Simulating {SCENARIOS[sid]['label']}..."):
                factory, kpis = run_scenario(sid, seed=seed, progress=st_prog, task_id=sid)
                results[sid] = (factory, kpis)
                
        progress_bar.empty()
        st.success(f"Simulation of {total_days} factory-days complete!")
        
        # Generate Charts
        with st.spinner("Generating dashboard charts..."):
            saved_paths = {}
            for sid, (factory, kpis) in results.items():
                path = plot_scenario_dashboard(factory, kpis, sid, REPORT_DIR)
                saved_paths[sid] = path
                
            comp_path = None
            if len(results) > 1:
                comp_path = plot_comparison_chart(results, REPORT_DIR)
                
        # Display Results
        st.header("📊 Key Performance Indicators")
        
        if len(results) > 1:
            st.subheader("Scenario Comparison")
            # Build a dataframe for comparison
            comp_data = []
            for sid, (_, kpis) in results.items():
                comp_data.append({
                    "Scenario": SCENARIOS[sid]["label"],
                    "Output (units)": f"{kpis['total_production_units']:,.0f}",
                    "Fill Rate": f"{kpis['fill_rate_pct']:.1f}%",
                    "On-Time Delivery": f"{kpis['otd_rate_pct']:.1f}%",
                    "Breakdowns": kpis["total_breakdowns"],
                    "Revenue": f"€{kpis['revenue_eur']:,.0f}",
                    "Net Profit": f"€{kpis['net_profit_eur']:,.0f}",
                    "Net Margin": f"{kpis['net_margin_pct']:.1f}%"
                })
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
            
            if comp_path and os.path.exists(comp_path):
                st.image(comp_path, caption="90-Day Scenario Comparison", use_container_width=True)

        for sid, (_, kpis) in results.items():
            st.divider()
            st.subheader(f"{SCENARIOS[sid]['label']}")
            st.caption(f"{SCENARIOS[sid]['description']}")
            
            # High level metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Output", f"{kpis['total_production_units']:,.0f} units")
            col2.metric("Order Fill Rate", f"{kpis['fill_rate_pct']:.1f}%")
            col3.metric("Stockout Events", f"{kpis['stockout_events']:,d}")
            col4.metric("Net Profit", f"€{kpis['net_profit_eur']:,.0f}")
            
            # Load the generated matplotlib dashboard
            if sid in saved_paths and os.path.exists(saved_paths[sid]):
                st.image(saved_paths[sid], use_container_width=True)

if __name__ == "__main__":
    main()
