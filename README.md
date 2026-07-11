# CeraSim - Sanitary Ware Industries Supply Chain Simulator

CeraSim is a discrete-event simulation model for SaniCer Sanitary Ware Industries, built using Python and SimPy. It is designed to model the end-to-end supply chain of a sanitary ware factory, helping stakeholders analyze production bottlenecks, evaluate system resilience, and test various capacity planning scenarios.

## Key Features

- End-to-end supply chain simulation from raw material procurement to finished goods fulfillment.
- Terminal-based UI for real-time progress tracking and Key Performance Indicator (KPI) display.
- Automated generation of Matplotlib dashboards for visualizing metrics.
- Configurable, built-in scenarios for testing resilience and capacity constraints.

## File and Folder Structure

- `main.py`: The main entry point for running the simulation, executing scenarios, and generating reports.
- `requirements.txt`: Contains the list of Python package dependencies required to run the project.
- `cerasim/`: The core Python package containing the simulation logic.
  - `__init__.py`: Package initialization file.
  - `config.py`: Defines simulation parameters, machine capacities, raw material properties, and scenario definitions.
  - `factory.py`: Contains the `CeramicFactory` class that sets up the SimPy environment, production processes, and resources.
  - `metrics.py`: Responsible for computing KPIs such as fill rates, bottlenecks, and total production units.
  - `models.py`: Defines the data structures representing physical and logical entities (e.g., batches, customer orders, supplier deliveries).
  - `reports.py`: Handles terminal output tables and the generation of Matplotlib visualizations.

## Installation and Setup

1. Ensure you have Python installed on your system.
2. Clone or download this repository.
3. Create a Python virtual environment:

   On Windows:

   ```powershell
   python -m venv .venv
   ```

   On macOS/Linux:

   ```bash
   python3 -m venv .venv
   ```

4. Activate the virtual environment:

   On Windows (PowerShell):

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   On Windows (CMD):

   ```cmd
   .venv\Scripts\activate.bat
   ```

   On macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

5. Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

The simulation is executed via the `main.py` script. You can run it with different arguments to control its behavior:

Run all predefined scenarios:

```bash
python main.py
```

Run a specific scenario (e.g., the baseline scenario):

```bash
python main.py --scenario baseline
```

Run with a specific random seed for reproducibility:

```bash
python main.py --seed 99
```

Run the simulation without generating matplotlib charts:

```bash
python main.py --no-charts
```

### Streamlit Web App Interface

You can also launch an interactive browser-based web dashboard using Streamlit:

```bash
streamlit run app.py
```

## Simulation Architecture

The simulation models the production pipeline within `factory.py`. The process flow operates as follows:

1. **Raw Material Supply**: Delivery of clay, kaolin, feldspar, silica, and glaze.
2. **Slip Preparation**: Mixing raw materials into ceramic slip.
3. **Pressure Casting**: Forming the commodes in molds.
4. **Demolding and Drying**: Extracting and drying the pieces.
5. **Fettling**: Smoothing edges and finishing surfaces.
6. **Spray Glazing**: Applying the interior and exterior glaze.
7. **Tunnel Kiln**: Firing the glazed pieces. This is the primary bottleneck of the factory.
8. **Finishing and QC**: Quality control and packaging.
9. **Order Fulfillment**: Fulfilling simulated customer demand.

## Built-in Scenarios

The simulator comes with four pre-configured scenarios defined in `config.py`:

1. **Baseline**: Simulates normal 90-day operations with balanced supply and demand.
2. **Supply Disruption**: Models a 35-day kaolin port strike, affecting raw material availability.
3. **Demand Surge**: Introduces a 30% demand uplift simulating a summer construction boom.
4. **Optimised**: Tests the impact of adding a second tunnel kiln and implementing a 50% safety stock uplift.

## Outputs and Reporting

Upon completion of a simulation run, the system provides:

- Detailed, terminal-based KPI tables for each scenario.
- A cross-scenario comparison table summarizing key metrics.
- Generated visualization dashboards (saved as `.png` files) located in the `reports/` directory.

## Collaborators

- Lasan MahaLiyana
- Oshada Jayasinghe
- Sithuka Jayawardhana
- Ranuja Jayawardena
- Sithum Fernando
