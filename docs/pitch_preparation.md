# Comprehensive Deep-Dive: SaniCer Supply Chain Simulator

**Goal:** Provide an exhaustive, detailed breakdown of the SaniCer Sanitary Ware supply chain simulation model. This document covers every node, variable, and scenario modeled in the system to support deep-dive presentations and technical reviews.

---

## 1. The Problem: Complex End-to-End Sanitary Ware Manufacturing

Sanitary ware manufacturing is not just about firing clay; it is a highly complex, multi-stage global supply chain heavily constrained by variable supplier lead times, stochastic machine failures, and strict quality control requirements.

### 1.1 Global Upstream Vulnerabilities
SaniCer relies on five critical raw materials, each with unique logistics profiles and disruption risks:
- **Clay (ClayMin Lda, Portugal):** Fast lead times (36 hours), highly reliable (92%).
- **Feldspar (FeldsparCo S.L., Spain):** Moderate lead time (42 hours), reliable (88%).
- **Silica (SilicaTech Lda, Portugal):** Fast lead time (36 hours), reliable (91%).
- **Glaze (ChemGlaze GmbH, Germany):** Longer lead time (72 hours), reliable (85%).
- **Kaolin (KaolinMine S.A., Brazil):** The most vulnerable link. Requires ocean freight with long lead times (72 hours mean, but high variance) and lower reliability (82%), making it susceptible to port strikes and shipping delays.

### 1.2 The 7-Stage Production Gauntlet
Manufacturing commodes (One-Piece Standard, Two-Piece Economy, and Wall-Hung Premium) requires passing through a strict sequence where any failure cascades downstream:
1.  **Slip Preparation:** Ball milling, deflocculation, and sieving.
2.  **Pressure Casting:** Utilizing 8 parallel mold sets.
3.  **Demolding & Initial Drying:** 18-hour air drying process.
4.  **Fettling & Trimming:** Removing seams and smoothing edges.
5.  **Spray Glazing:** Manual/robotic interior and exterior coating.
6.  **Tunnel Kiln Firing:** The definitive bottleneck. A continuous gas-fired kiln with a rigid 24-hour firing cycle.
7.  **Quality Control & Finishing:** Functional leak and flush testing, inspection, and packaging.

### 1.3 Stochastic Breakdowns and Yields
In the real world, machines break and products fail inspection. The model captures:
- **Machine Breakdowns:** Every machine has a specific Mean Time Between Failures (MTBF) and Mean Time To Repair (MTTR). For instance, the Tunnel Kiln has an MTBF of 720 hours but takes 8 hours to repair when it fails.
- **Quality & Yields:** Only 75% of products are Grade A prime quality. 15% are Grade B (sold at a 35% discount), and 10% are completely scrapped. Additional functional testing (leak/flush) introduces further reject rates.

### 1.4 Siloed Decision Making
Decisions about multi-million Euro CAPEX investments (e.g., adding a kiln), increasing inventory buffers, or switching suppliers are traditionally made using static spreadsheets that use averages. Averages completely fail to predict the chaotic intersections of a Kaolin delivery delay coinciding with a casting machine breakdown during a demand surge.

## 2. The Need for Simulation: Why Static Math Fails

You cannot experiment on a live plant. Testing a new production schedule or reducing safety stock in real life risks massive revenue loss and endangers customer service levels.

- **Averages Hide the Truth:** If casting produces at the same average rate as the kiln fires, static math suggests you need zero Work-In-Progress (WIP) inventory between them. In reality, random breakdowns mean that without a buffer, the kiln will go idle.
- **Capturing Stochastic Behavior:** We need to model the probability distributions of machine failures, transit delays, and defect rates. Simulation is the only tool that can capture this random behavior and reveal its compounding effects over time.
- **Risk-Free "What-If" Scenarios:** The business needs a digital twin to answer high-stakes questions safely. 
- Simulation translates operational variables (machine uptime, transport delays) directly into strategic financial outcomes (revenue, profit, customer fill rate).

## 3. Our Solution: The SaniCer Simulator

We have built a bespoke, data-driven Discrete-Event Simulation (DES) platform tailored exactly to the SaniCer supply chain.

### 3.1 Unprecedented End-to-End Visibility
The simulator maps the exact physical and temporal flow of the business:
- **Raw Material Inventory Management:** Continuously monitors silos. When clay drops below 65 tonnes or Kaolin below 22 tonnes, the system automatically triggers replenishment orders subject to real-world lead times and delays.
- **WIP and Bottleneck Management:** Explicitly models capacity constraints at all 7 stages. It reveals exactly where WIP buffers build up and where starvation occurs.
- **Customer Demand:** Simulates a mix of standard (7-day) and express (3-day, 15% price premium) orders from a roster of diverse international distributors.

### 3.2 Dynamic Financial & Operational KPIs
The system doesn't just count widgets; it calculates the P&L impact.
- **Revenues & Penalties:** Calculates sales based on product mix and grade, subtracts €25 penalties for every unit stocked out.
- **Operational Costs:** Dynamically tracks energy costs (€280 per kiln batch), labor shifts (€3,500 per shift), and breakdown repair costs (€2,500 per incident).
- **Core Metrics:** Outputs exact Order Fill Rates, On-Time Delivery percentages, Stockout Events, Revenue, and Net Margin.

### 3.3 Built-in Strategic Scenarios
The model is pre-configured to test four critical business scenarios over a 90-day horizon:
1.  **Baseline:** Normal operations, balanced supply and demand.
2.  **Supply Disruption:** Models a severe 35-day port strike in Brazil affecting Kaolin deliveries (Days 15–50) to stress-test raw material safety stocks.
3.  **Demand Surge:** Models a 30% surge in demand across all product lines representing a summer construction boom to test finished goods inventory limits.
4.  **Optimised:** Evaluates the exact ROI of a €3.5M CAPEX investment for a second tunnel kiln coupled with a 50% increase in raw material safety stocks.

## 4. Our Tech Stack: Python-Powered, Beautiful & Scalable

We use a modern, open-source Python-based technology stack, avoiding the lock-in and limitations of legacy simulation software.

- **Core Engine: SimPy:** We use SimPy, a robust process-based discrete-event simulation framework. It provides built-in constructs (Resources, Containers, Stores, Interrupts) that map perfectly to SaniCer's casting molds, warehouse capacities, and machine breakdowns.
- **Interactive UI:** The simulation is wrapped in a beautiful, interactive **Streamlit** web application, allowing stakeholders to easily select scenarios, set seeds, and run the simulator from their browser.
- **Rich CLI & Analytics:** For power users, a gorgeous command-line interface is built with **Rich**, providing live progress bars. Post-simulation, we use **Pandas** and **Matplotlib** to automatically generate comprehensive analytical dashboards and KPI comparison tables.
- **Data-Schema First:** All physical network parameters—downtime distributions, kiln cycle times, financial costs, and supplier data—are defined in clean Python configuration files (`config.py`). This separation of logic and data makes the model highly extensible and ready for future ERP/MES integration.


