# SimPy-Based Discrete-Event Supply Chain Simulator for the Ceramic Industry

## Executive summary
A ceramic supply chain simulator is most valuable when it explicitly represents the process-route constraints and bottlenecks unique to ceramics—especially drying and firing—because these stages strongly couple throughput, energy use, and quality outcomes. For wall/floor tiles, the EU ceramics BAT reference (CER BREF) reports that single-deck roller kilns are "almost universally used" and that firing schedules have been reduced to less than 40 minutes, making kiln capacity and feed stability dominant system drivers.

For ceramic tile manufacturing, a large survey-based Qualicer study (55 companies) reports that thermal energy consumption occurs mainly in spray drying, drying, and firing, with energy costs accounting for ~17-20% of total costs in that sector context; it also provides measured stage-specific energy intensities that can be used as credible priors for early modeling and calibration.

A practical "first simulator" strategy is to build a SimPy-based discrete-event simulation (DES) because SimPy is explicitly designed for process-based DES using Python generator functions, and it provides shared resources (capacity constraints, queues) that map directly to presses, dryers, kilns, forklifts, and transport lanes. SimPy's event model (events succeed/fail, callbacks, interrupts) supports realistic modeling of breakdowns, maintenance, and disruption recovery logic that is common in ceramics plants and logistics.

However, DES alone can under-represent strategic feedback loops (capacity expansion, long-run demand shifts, decarbonization pathways) and behavioral dynamics (supplier bargaining, distributor ordering heuristics). Peer-reviewed supply chain simulation literature distinguishes DES (more operational/tactical) from system dynamics (more strategic/aggregate) and motivates hybridization when you need both.

## Explicit scope assumptions (baseline for this report)
These are "starter" assumptions you can replace with your real business context:
- **Product focus:** primarily ceramic tiles (wall/floor coverings) as the reference process route (wet milling → spray drying → forming → drying → glazing/decoration → firing → sorting → packaging), while still mapping upstream/downstream nodes applicable to broader ceramics.
- **Network shape:** one or a few manufacturing plants, with upstream mineral suppliers and downstream distributors/retail channels; multi-region export is represented as transport lanes and regional demand nodes. (Tile EPDs provide representative multi-region distribution fractions and transport distances that can serve as scenario priors.)
- **Data availability:** limited at the start; you will rely on industry references (CER BREF, Qualicer, EPDs, IPCC factors) as priors and then calibrate to plant-level throughput, energy meters, yield/defect logs, and shipping records.
- **Simulator purpose:** scenario comparison and decision support (capacity, inventory/service, energy/CO₂, disruption resilience), not a perfect "digital twin" on day one. (This aligns with V&V guidance emphasizing adequacy for intended use rather than absolute "correctness.")

## Ceramic supply chain map, stakeholders, and typical flows

### End-to-end mapped supply chain for ceramics
Ceramics is a family of industries (tiles, bricks/roof tiles, sanitaryware, table/ornamental ware, technical ceramics). The CER BREF explicitly covers these classes and describes common processes and environmental aspects.

A robust supply chain map for simulation can be organized as upstream materials, transport, manufacturing, downstream distribution, and recycling/waste. Ceramic tile EPDs are particularly useful because they explicitly lay out process-module boundaries from raw material supply through installation and end-of-life.

### Physical nodes and typical "flows that matter" in a simulator

**Upstream (raw materials and preprocessing)**
Ceramic tiles distinguish plastic vs non-plastic (degreasing) materials; the tile EPD lists body materials (e.g., clay, feldspar, sand, kaolin, deflocculant) and also indicates that factory wastes (sludge, unfired scrap, fired scrap) may be introduced back into milling.
Glaze formulations commonly include quartz, kaolin, borates, alkaline/feldspathic materials, nepheline, carbonates (e.g., calcium carbonate, dolomite), zircon, wollastonite, calcined alumina, and additives (deflocculants/binders/suspending agents), with the same EPD citing an average frit content of 50% in glaze formulation.

**Transport (multi-modal, bulk vs packaged)**
The tile EPD describes raw materials imported via sea freight and then trucks, and notes bulk transport (no packaging) for most raw materials, while finished goods distribution includes road and sea with explicit example distances and utilization assumptions.
This matters in simulation because (a) ceramics is heavy/voluminous, (b) breakage risk exists, and (c) lane variability drives service and inventory needs.

**Manufacturing (forming → drying → firing as the critical chain)**
A representative tile route is: milling → spray drying → forming → drying → glazing/decoration → firing → finishing treatments → sorting/QC → packaging.
Firing is central: CER BREF highlights roller hearth kilns' prevalence in wall/floor tile manufacture and the fast firing schedules of modern systems.
Thermal energy is concentrated in spray drying, drying, and firing; Qualicer quantifies both energy intensities and the stage shares of energy use.

**Downstream (warehousing, distribution, retail/project channels)**
The tile EPD provides example distribution shares (Spain/Europe/rest of world). This supports modeling multi-echelon inventory: plant finished goods → regional DCs → retailers/project sites.

**Recycling and waste (internal loops + end-of-life)**
Two distinct loops should be explicitly represented: 
- Internal recycling loops: factory sludge, unfired scrap, fired scrap loop back into milling (affects raw mix costs, yields, and potentially quality).
- External/end-of-life recycling: ceramic tile waste is increasingly studied as feedstock for construction materials; an up-to-date review summarizes use pathways and notes that industrialization still needs further work.

### Stakeholders to represent (as decision-making roles)
Even if your simulator starts as a physical flow model, it should anticipate real decision rights. Key stakeholders include:
- Quarry/mineral suppliers and processors (quality variability, moisture, grade availability, disruption risk).
- Additives / glaze / frit suppliers (specialty lead times, quality acceptance, substitution constraints).
- Plant operations (production scheduling, kiln operation, energy management, quality sorting, packaging, maintenance).
- Carriers and logistics providers (lane times/variability, capacities, cost/emissions).
- Distributors / retailers / construction projects (order batching, service targets, seasonality).
- Waste/recycling operators (recycling yields, market demand for recycled products).
- Regulators (emissions, monitoring, BAT compliance expectations).

## Data model and parameterization

### Why "data schema first" is non-negotiable
In manufacturing simulation, data is often fragmented across applications; NIST's CMSD report notes that production-related data is spread across several applications and that common shop-floor standards often miss the ability to capture stochastic behavior, motivating a neutral information model for simulation-related manufacturing data.
This is directly relevant to ceramics because many critical parameters (kiln downtime, defect rates, transit variability, supplier reliability) must be represented as distributions, not single-point averages.

### Ceramics-specific parameters that should be first-class fields
Below are ceramics parameters that frequently dominate model behavior and should be explicit in the schema (not hidden in generic "process time" fields):
- **Kiln residence/cycle times and capacity representation:** Roller hearth firing schedules can be <40 minutes for tiles, changing the nature of WIP buffering and throughput control.
- **Thermal and electric energy intensities by stage:** Qualicer reports measured values such as spray-drying thermal energy (e.g., 476 ± 19 kWh/t dry solid in one measurement set) and pressed tile process energy (drying+firing) expressed per ton and per m², plus the relative shares of energy across firing/spray drying/drying.
- **Fuel type and emissions factors:** IPCC 2006 Guidelines provide default CO₂ emission factors; for natural gas the table shows 56,100 kg CO₂/TJ (net calorific basis) with a lower/upper range.
- **Scrap loops into milling:** factory sludge, unfired and fired scrap inputs into milling must be modeled as material loops affecting upstream demand and quality.
- **Glaze formulation constraints (including frit share):** because they influence procurement risk and potentially quality/firing outcomes.

### Required data fields per node (minimum viable, SimPy-ready)
The table below is a starter schema that is directly implementable in a SimPy DES model. You can treat each row as a "NodeType" class in code with a validated config object.

| Node type | Material/flow fields | Time & reliability fields | Cost fields | Energy & emissions fields | Quality, yield & waste fields |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quarry / mine / mineral supplier** | SKU/grade catalogue; lot size; moisture baseline; min/max shipment | Lead time distribution; on-time probability; outage distribution | Unit cost by grade; escalation rules | Transport emissions optional (if supplier-controlled) | Quality variability distributions (chemistry/granulometry); rejection probability |
| **Clay/mineral processing (crush/grind/blend)** | BOM/recipe constraints; batch size; storage capacities | Process time distributions; changeover times; uptime/MTBF/MTTR | Op cost per ton; scrap disposal cost | Electric kWh/ton; dust controls if modeled | Yield; off-spec rate; rework rules |
| **Additives supplier (binders/deflocculants)** | MOQ; shelf-life; substitution groups | Lead time variability; fill-rate distribution | Unit cost; expedite premiums | Embedded emissions optional | Lot acceptance rate effects (if QC data exists) |
| **Glaze/frit/pigment supplier** | Product catalogue; packaging constraints | Lead time; reliability; disruption risk | Unit cost; contract terms | Embedded emissions optional | Lot quality risk; frit content assumptions for mix planning |
| **Inbound transport lane** | Mode; capacity; damage rate; lane distance | Transit time distribution; delay probability | Cost per ton-km or per shipment; demurrage | CO₂e per shipment (or per ton-km) | Loss/damage probability |
| **Raw material storage (plant)** | Silo/bin capacities; FIFO/FEFO rules | Receiving inspection time; handling times | Handling cost | Utility use optional | Contamination/moisture drift (if important) |
| **Milling (wet/dry)** | Recipe; batch size; WIP limits | Cycle time distribution; uptime | Cost per batch | Electric kWh/ton | Yield; off-spec to reblend |
| **Spray drying (tiles route)** | Granule batch size; buffer capacity | Residence time; downtime distributions | Gas cost; electricity cost | Thermal kWh/t (e.g., measured ranges), electric kWh/t | Moisture target distribution; scrap handling |
| **Forming (press / extrusion / casting)** | Mold sets; batch release rules; WIP limit (CONWIP/Kanban) | Cycle times; changeovers; uptime | Labor/machine cost | Electric kWh/unit | Green scrap rate; dimensional variability |
| **Drying** | Dryer capacity; buffer sizes | Residence time distribution; stoppages | Fuel/electric price | Thermal kWh/t or kWh/m²; electric kWh/t | Crack/warp defect probability as function of moisture targets |
| **Glazing/decoration** | Line speed; changeover matrix | Cycle times; downtime | Material cost (glaze); labor | Energy per m² optional | Coating defects; rework rules |
| **Firing (kiln)** | Kiln type; loading rules; throughput; buffer constraints | Residence time/cycle time; planned stops; unplanned downtime | Fuel cost; maintenance cost | Fuel use per m² or per ton; CO₂ via IPCC factors (e.g., NG 56,100 kg CO₂/TJ) | Fired scrap rate; properties acceptance; process emissions optional |
| **Sorting/QC/finishing** | Grade rules; rework routing | Inspection time; inspection accuracy | Cost of quality | Energy per unit optional | Grade yields; scrap loops to milling (sludge/unfired/fired scrap) |
| **Packaging + FG warehouse** | Pallet rules; storage capacity | Pick/pack time; dock capacity | Packaging material cost | Forklift/warehouse electricity optional | Damage in handling |
| **DC / wholesaler** | Inventory policy parameters (s,S), base-stock, review cycles | Handling/processing times | Storage cost; handling cost | Facility emissions optional | Shrink/damage |
| **Retail / project demand node** | Demand distribution; seasonality profile; order batching rules | Order cycle times; service targets | Margin/penalty costs | Transport emissions optional | Returns/damage |
| **Waste / recycling** | Collection rates; processing yields | Processing time distributions | Disposal vs recycling cost | Emissions for recycling treatments | Recycling yield; diversion constraints; downstream demand |

## Modeling approach and rationale

### Why SimPy + DES is a strong default for ceramics
SimPy is explicitly described as a process-based discrete-event simulation framework in Python; processes are defined by generator functions, and the framework provides shared resources to model limited-capacity congestion points.
Ceramic supply chains (especially plant operations) are naturally event-driven: arrivals, batches, queueing at presses/dryers/kilns, transport departures/arrivals, breakdowns, maintenance start/finish, and quality sorting outcomes.
SimPy maps well to ceramic constraints because it provides:
- **Resources** and priority/preemption variants for constrained equipment and dispatching logic.
- **Containers** for bulk continuous/discrete materials (e.g., clay slurry volume, granulate tons, fuel tanks), with put/get operations naturally blocking when full/empty.
- **Stores and FilterStores** for WIP/FG items, enabling requests for specific SKUs/grades and selective retrieval logic.
- **Interrupts** for failures and preemption, represented as exceptions that processes can catch and handle rather than terminating.
- **Events** that succeed/fail, carry values, and trigger callbacks, supporting custom synchronization patterns (e.g., "kiln batch completed" events).

### Comparison table: when DES/SimPy is enough vs when to add SD/ABM/hybrids
Peer-reviewed supply chain simulation literature often separates operational/tactical DES use from strategic SD use. Hybrid approaches are recommended when one abstraction level is insufficient, consistent with multimethod modeling guidance.

| Approach | What it captures well | Typical ceramics use cases | Limitations / risks | When to add to a SimPy DES core |
| :--- | :--- | :--- | :--- | :--- |
| **DES (SimPy)** | Queues, batches, finite resources, transport events, stochastic failures, WIP/inventory dynamics | Kiln/dryer/press bottleneck analysis; scheduling policies; disruption response; inventory-service-cost tradeoffs | Can become data-hungry; can overfit operational detail if not calibrated/validated | Keep as core for operational realism |
| **System Dynamics (SD)** | Feedback loops, aggregate stock/flow behavior, long-term dynamics | Capacity expansion; multi-year decarbonization pathways; policy scenarios | Too aggregate for kiln scheduling and batch logistics; may hide variability effects | Add as an outer strategic layer if you need multi-year planning |
| **Agent-Based Modeling (ABM)** | Heterogeneous actor behaviors, decentralized decisions, learning/adaptation | Supplier reliability strategies; carrier choice/bidding; distributor ordering heuristics | Calibration can be assumption-heavy; behavior rules can dominate outcomes | Add when behavior itself is the decision variable (not just flows) |
| **Hybrid / multimethod** | Combines strategic + operational and/or behavioral layers | "Operations + strategy" scenario stacks: e.g., kiln investment + energy pricing + downstream service levels | More engineering and governance complexity | Add once the DES core is validated and demand for broader questions is clear |

## SimPy design blueprint with core patterns and pseudocode
### SimPy concepts you will use constantly
A practical SimPy design uses a small set of primitives repeatedly:
- Environment (`env`): controls simulation time and execution; you can run until the event queue is empty, until a time, or until an event triggers.
- Processes: generator functions scheduled via `env.process(...)`.

### Sample KPI formulas (supply + make + deliver + energy/CO₂)
Below are KPI formulas that are easy to compute from SimPy event logs.
- **Service and inventory**
  - Fill rate = (units shipped on time) / (units demanded)
  - On-time delivery (OTD) = P(delivery_time ≤ promised_time)
  - Days of supply = inventory_on_hand / average_daily_demand
- **Manufacturing**
  - Throughput (m²/day) = total_m²_shipped / horizon_days
  - Utilization (resource r) = busy_time_r / available_time_r
  - First-pass yield = good_units_after_sorting / units_entering_firing
- **Energy and emissions (using IPCC fuel factors)**
  - Fuel CO₂ (kg) = fuel_energy_TJ × EF_CO₂(kg/TJ). For natural gas EF_CO₂ default is 56,100 kg CO₂/TJ (with a stated range).
  - Thermal intensity (kWh/m²) = thermal_kWh_used / m²_fired
  - Stage energy shares: Qualicer reports firing as the largest energy consumer and provides indicative shares (e.g., firing ~55%, spray drying ~36%, tile drying ~9% in the cited context), which you can compute and compare during validation.

### Experiment orchestration (replications, warm-up, confidence intervals)
A rigorous simulation workflow should include:
- **Warm-up handling (steady-state models):** Robinson proposes an SPC-based method for estimating warm-up period, explicitly framing warm-up as a way to reduce initialization bias and comparing against common methods (time-series inspection, Welch's method).
- **Replication count determination:** Hoad, Robinson, and Davies describe automating the selection of how many replications to run to achieve required accuracy and emphasize three key statistical decisions: warm-up, run-length, and number of replications.
- **Confidence intervals:** implement t-based confidence intervals over replication outputs, and stop when half-width ≤ tolerance (precision-based stopping), consistent with the approach discussed for replication selection.

A practical design: 
- Each scenario → run R replications with distinct random stream seeds. 
- Collect per-replication KPIs. 
- Estimate mean, variance, and confidence intervals. 
- Optionally adaptively increase R until precision targets are met.

### Data storage and dashboards
For a SimPy-based system, it is common to separate: 
- Event logs / time series (optionally large): store as Parquet files or a time-series store. 
- Aggregated KPI tables: store in a relational database for dashboarding and comparisons.

Dashboards frequently use:
- Plotly/Dash for interactive analytic apps, as described in Dash's user guide.
- Grafana for time-series and operational dashboards; Grafana documentation supports connecting to a PostgreSQL-compatible database as a data source for visualization.

### Scaling SimPy simulations (single machine → parallel → cloud batch)
Simulation scaling is mostly about running many replications/scenarios efficiently:
- **Single machine, single process:** easiest to debug and validate.
- **Single machine, multiprocessing:** Python's multiprocessing module supports process-based parallelism and can side-step the GIL by using subprocesses, enabling multi-core replication execution.
- **Cluster/distributed:** Ray supports executing tasks asynchronously on worker processes and scaling beyond a single machine, which is a natural fit for embarrassingly parallel replication workloads.
- **Cloud batch vs on-prem:** NIST's cloud definition highlights rapid elasticity and measured service, which are valuable for bursty experiment workloads; on-prem may be preferred for data residency/governance.

A recommended scaling pattern: 
1. Keep the simulation core deterministic and reproducible. 
2. Parallelize across replications, not within a single replication (simplifies state and avoids nondeterministic race patterns). 
3. Containerize the runner (for consistent environments), then schedule runs via on-prem Kubernetes or cloud batch systems if needed (guided by your governance constraints).

## Calibration, validation, testing, and benchmarks
### Data sources and priors (what you can use on day one)
To start from scratch, you can build a credible baseline using:
- **Process structure and technology constraints:** CER BREF (kiln types, general process and environmental context).
- **Measured energy intensities and stage shares:** Qualicer provides both survey-level and measurement-level energy consumption values for spray-drying and pressed tile production, plus relative stage energy shares.
- **Supply chain boundaries and materials:** tile EPDs offer structured process module maps and explicit material lists (including glaze components and internal scrap use), and example distribution distances.
- **Emissions factors:** IPCC 2006 default emission factors (e.g., natural gas 56,100 kg CO₂/TJ).
- **Waste/recycling pathways:** recent reviews summarize recycling applications and maturity constraints.

### Estimating missing parameters (structured approach)
A defensible estimation approach is:
- Use industry priors as distributions, not fixed points (e.g., energy intensity ranges from Qualicer's tables; lane times as lognormal/triangular initially).
- Calibrate to totals: tune parameters so that simulated totals match reality (monthly fuel consumption, total throughput, total scrap). Qualicer shows how energy data is gathered and summarized and provides a benchmark structure for per-unit consumption reporting.
- Introduce causal drivers gradually: only after the baseline matches totals, add dependencies (defects as function of downtime/moisture; kiln efficiency as function of throughput).

### Verification and validation strategy (aligned to Sargent)
Sargent's V&V paper emphasizes: 
- **verification** = ensuring the computerized model implementation is correct, 
- **validation** = ensuring model accuracy is acceptable for its intended use, 
- and that there is no single universal test suite; each simulation poses unique challenges.

A recommended V&V plan for your SimPy ceramics simulator:
- **Verification (correctness of logic)**
  - Deterministic unit tests with fixed seeds (e.g., one SKU, no failures) to confirm mass balance and cycle times.
  - Invariant checks: no negative inventories, container capacities never exceeded, scrap conservation in loops.
  - Event-log sanity: monotonic timestamps, correct queue ordering, correct resource release.
- **Validation (fit-for-purpose accuracy)**
  - Compare simulated vs observed throughput by day/week/month.
  - Compare energy totals and intensities using metered fuel/electricity (Qualicer provides reference definitions and per-unit reporting examples).
  - Compare scrap rates by SKU family and stage.
  - Compare order lead time distributions and fill rates.

### Sensitivity analysis, benchmarks, and recommended scenarios
A ceramics-focused scenario test suite should include:
- **Kiln constraint stress test:** reduce kiln availability or capacity; verify WIP builds pre-kiln and service degrades predictably (especially relevant given fast roller-kiln schedules).
- **Energy-price / emissions constraint scenario:** apply IPCC EF-based CO₂ accounting; compare policies (e.g., more inventory vs more expedited shipping).
- **Scrap-loop amplification scenario:** increase fired scrap rate; verify upstream raw material consumption rises due to scrap recycling loops in milling.
- **Export mix shock:** use EPD-like distribution splits and change them abruptly; check DC/transport lane bottlenecks.

**Warm-up and replication convergence benchmarks:**
- Use Robinson's warm-up estimation framing for steady-state experiments.
- Use precision-based replication stopping logic described by Hoad et al.

**Performance metrics for the simulator engine itself:** 
- wall-clock runtime per replication, 
- events processed per second, 
- peak memory usage, 
- scalability efficiency (speedup vs number of workers).

## Roadmap, team, risks, and references

### Phased implementation roadmap (deliverables + effort bands)
Effort depends on network size, data availability, kiln model fidelity, and UI expectations. The roadmap below assumes a SimPy core and production-grade orchestration.

| Phase | What you build | Deliverables | Low | Medium | High |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Conceptual model + schema** | Supply chain map, node taxonomy, parameter schema, KPI list | Config templates; baseline scenarios; assumptions register | 2-4 wks | 4-8 wks | 8-12+ wks |
| **SimPy core network** | Nodes, lanes, inventories, demand, order fulfillment | Working DES prototype; event logs | 4-8 wks | 8-14 wks | 14-24+ wks |
