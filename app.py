import os
import json
import streamlit as st
import pandas as pd
from main import run_scenario, REPORT_DIR
from cerasim.config import SCENARIOS, SIM_DAYS
from cerasim.reports import plot_scenario_dashboard, plot_comparison_chart
from cerasim.outputs import generate_pdf_report, generate_csv_report

STATE_FILE = "cerasim_state.json"

st.set_page_config(page_title="CeraSim Dashboard", layout="wide")

# ── Light Theme CSS ──────────────────────────────────────────────────────────
LIGHT_THEME_CSS = """
<style>
    /* Main background */
    .stApp {
        background-color: #f8f9fa;
        color: #1a1a2e;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #1a1a2e !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #16213e !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    div[data-testid="stMetric"] label {
        color: #555555 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #16213e !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #2E86AB;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1a6b8a;
        box-shadow: 0 4px 12px rgba(46, 134, 171, 0.3);
        transform: translateY(-1px);
    }
    .stDownloadButton > button {
        background-color: #ffffff;
        color: #2E86AB;
        border: 1.5px solid #2E86AB;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background-color: #2E86AB;
        color: #ffffff;
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Divider */
    hr {
        border-color: #e0e0e0 !important;
    }

    /* Info / Success boxes */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }
</style>
"""
st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


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


# ── State Persistence ────────────────────────────────────────────────────────

def save_state(results, comp_path):
    """Persist KPIs and chart paths to disk so they survive a browser refresh."""
    data = {
        "comp_path": comp_path,
        "scenarios": {}
    }
    for sid, (factory, kpis, chart_path) in results.items():
        data["scenarios"][sid] = {
            "kpis": kpis,
            "chart_path": chart_path,
        }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, default=str)
    except (OSError, TypeError):
        pass  # Non-critical — if save fails, user just loses state on refresh


def load_state():
    """Restore the last simulation results from disk if available."""
    if not os.path.exists(STATE_FILE):
        return None, None
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        results = {}
        for sid, entry in data.get("scenarios", {}).items():
            # Store (None, kpis, chart_path) — factory object can't be serialized,
            # but we only need kpis and chart_path for display purposes
            results[sid] = (None, entry["kpis"], entry.get("chart_path"))
        return results, data.get("comp_path")
    except (OSError, json.JSONDecodeError, KeyError):
        return None, None


# ── Simulation Cache ─────────────────────────────────────────────────────────

# Caching: Use cache_resource to keep the factory objects in memory without serializing
@st.cache_resource(show_spinner=False)
def get_cached_simulation(sid, seed, demand_factor, mach_rel_factor, supp_rel_factor, extra_kilns, safety_factor):
    # Patch config dynamically for this run
    original_config = SCENARIOS[sid].copy()
    
    SCENARIOS[sid]["demand_factor"] = demand_factor
    SCENARIOS[sid]["machine_reliability_factor"] = mach_rel_factor
    SCENARIOS[sid]["supplier_reliability_factor"] = supp_rel_factor
    SCENARIOS[sid]["extra_kilns"] = extra_kilns
    SCENARIOS[sid]["safety_stock_factor"] = safety_factor
    
    factory, kpis = run_scenario(sid, seed=seed, progress=None, task_id=sid)
    
    # Generate chart immediately so we cache its path too
    chart_path = plot_scenario_dashboard(factory, kpis, sid, REPORT_DIR)
    
    # Restore original config just in case
    SCENARIOS[sid].update(original_config)
    
    return factory, kpis, chart_path


# ── Main App ─────────────────────────────────────────────────────────────────

def main():
    st.title("🏭 Supply Chain Simulator")

    # Initialise session state, restoring from disk if available
    if "results" not in st.session_state:
        saved_results, saved_comp = load_state()
        st.session_state.results = saved_results if saved_results else {}
        st.session_state.comp_path = saved_comp

    with st.sidebar:
        st.header("Simulation Settings")
        scenario_options = list(SCENARIOS.keys())
        # Provide user friendly labels for scenarios in selectbox
        selected_label = st.selectbox(
            "Select Scenario Preset", 
            ["All Scenarios"] + [SCENARIOS[k]["label"] for k in scenario_options]
        )
        
        if selected_label == "All Scenarios":
            selected_scenario = "All"
            st.info("Custom sliders are disabled when running 'All Scenarios'. Presets will be used.")
            demand_val, mach_val, supp_val, kilns_val, safety_val = 1.0, 1.0, 1.0, 0, 1.0
        else:
            selected_scenario = next(k for k in scenario_options if SCENARIOS[k]["label"] == selected_label)
            preset = SCENARIOS[selected_scenario]
            
            st.subheader("⚙️ Custom Parameters")
            # 1. Dynamic Parameter Sliders
            demand_val = st.slider("Demand Factor", 0.5, 2.0, float(preset["demand_factor"]), 0.1)
            mach_val = st.slider("Machine Reliability", 0.5, 1.5, float(preset["machine_reliability_factor"]), 0.1)
            supp_val = st.slider("Supplier Reliability", 0.5, 1.5, float(preset["supplier_reliability_factor"]), 0.1)
            kilns_val = st.number_input("Extra Kilns", 0, 3, int(preset["extra_kilns"]), 1)
            safety_val = st.slider("Safety Stock Factor", 0.5, 3.0, float(preset["safety_stock_factor"]), 0.1)
            
        seed = st.number_input("Random Seed", value=42, step=1)
        run_btn = st.button("Run Simulation", type="primary")

    if run_btn:
        to_run = scenario_options if selected_scenario == "All" else [selected_scenario]
        st.session_state.results = {}
        
        st.write("Running simulation(s)...")
        progress_bar = st.progress(0.0)
        
        total_days = SIM_DAYS * len(to_run)
        st_prog = GlobalStreamlitProgress(progress_bar, total_days)

        with st.spinner("Processing..."):
            for sid in to_run:
                # If running all, use their default presets instead of sliders
                if selected_scenario == "All":
                    df, mrf, srf, ek, ssf = (
                        SCENARIOS[sid]["demand_factor"],
                        SCENARIOS[sid]["machine_reliability_factor"],
                        SCENARIOS[sid]["supplier_reliability_factor"],
                        SCENARIOS[sid]["extra_kilns"],
                        SCENARIOS[sid]["safety_stock_factor"]
                    )
                else:
                    df, mrf, srf, ek, ssf = demand_val, mach_val, supp_val, kilns_val, safety_val

                # Using cache_resource bypasses execution if parameters are the same!
                factory, kpis, chart_path = get_cached_simulation(
                    sid, seed, df, mrf, srf, ek, ssf
                )
                # Just update progress bar artificially since it's cached
                st_prog.advance(sid, SIM_DAYS)
                st.session_state.results[sid] = (factory, kpis, chart_path)
                
            if len(st.session_state.results) > 1:
                st.session_state.comp_path = plot_comparison_chart(st.session_state.results, REPORT_DIR)
            else:
                st.session_state.comp_path = None
                
        progress_bar.empty()
        st.success(f"Simulation of {total_days} factory-days complete!")

        # Persist results to disk
        save_state(st.session_state.results, st.session_state.comp_path)

    # Display Results if we have them
    if st.session_state.results:
        st.header("📊 Key Performance Indicators")
        
        comp_data = []
        for sid, (_, kpis, _) in st.session_state.results.items():
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
            
        df_comp = pd.DataFrame(comp_data)
        
        # 2. One-Click Data Export
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        col1.dataframe(df_comp, use_container_width=True, hide_index=True)
        col2.download_button(
            label="📥 Download CSV",
            data=generate_csv_report(df_comp),
            file_name='cerasim_kpis.csv',
            mime='text/csv',
            use_container_width=True
        )
        
        pdf_bytes = generate_pdf_report(st.session_state.results, df_comp, st.session_state.comp_path)
        col3.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name='cerasim_report.pdf',
            mime='application/pdf',
            use_container_width=True
        )
            
        if len(st.session_state.results) > 1 and st.session_state.comp_path:
            st.subheader("Scenario Comparison")
            if os.path.exists(st.session_state.comp_path):
                st.image(st.session_state.comp_path, caption="90-Day Scenario Comparison", use_container_width=True)

        for sid, (_, kpis, chart_path) in st.session_state.results.items():
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
            if chart_path and os.path.exists(chart_path):
                st.image(chart_path, use_container_width=True)

if __name__ == "__main__":
    main()
