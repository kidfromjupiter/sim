# CeraSim Presentation Plan (15 Minutes)

This document outlines a 15-minute presentation structured for a 5-member team. Each member is allocated **3 minutes** and will focus on a distinct, equally weighted component of the CeraSim project. The structure covers the system's architecture, underlying code, Object-Oriented principles, and applied design patterns.

> [!TIP]
> **Time Management:** 3 minutes goes by quickly. Practice focusing on the _impact_ of your code rather than reading the code line-by-line.

---

## Member 1: Project Overview & System Architecture

**Focus:** High-level introduction, architecture, and system entry points.

- **Topics to Cover:**
  - What is CeraSim? (A discrete-event supply chain simulator for SaniCer).
  - The problem it solves: identifying bottlenecks (like the tunnel kiln), testing supply disruptions, and evaluating capacity planning.
  - System Architecture & Separation of Concerns (Backend simulation engine vs. Frontend UI).
  - Execution flow starting from the CLI.
- **Key Files:**
  - [README.md](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/README.md)
  - [main.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/main.py)
- **Design/Architecture Principles:**
  - **Separation of Concerns:** Explaining how configuration, simulation logic, data models, and UI are completely isolated into different modules.

---

## Member 2: The Core Simulation Engine

**Focus:** The SimPy event-driven pipeline and factory operations.

- **Topics to Cover:**
  - How the `CeramicFactory` orchestrates the entire supply chain.
  - The production pipeline: from `slip_preparation` to `pressure_casting` to `kiln_firing` and `finishing`.
  - How time and resources are managed using SimPy environments and resources.
- **Key Files / Functions:**
  - [cerasim/factory.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/cerasim/factory.py)
  - Functions: `CeramicFactory.__init__`, `kiln_firing()`, `supply_monitor()`.
- **Design Patterns & OOP:**
  - **Producer-Consumer Pattern:** Strongly utilized here. The processes (like casting and fettling) act as producers and consumers, passing `ProductionBatch` objects through asynchronous SimPy `Store` and `Container` buffers (e.g., `slip_buffer`, `cast_store`).
  - **Encapsulation:** The factory encapsulates all internal states, resources (machines), and stores, providing a clean interface (`register_processes()`).

---

## Member 3: Data Modeling & Business Configuration

**Focus:** How real-world entities and rules are represented in code.

- **Topics to Cover:**
  - How physical items (batches of commodes) and logical events (orders, breakdowns) are modeled as data structures.
  - How the system is made flexible via centralized configuration (products, machines, financial parameters).
- **Key Files:**
  - [cerasim/models.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/cerasim/models.py)
  - [cerasim/config.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/cerasim/config.py)
- **Design Patterns & OOP:**
  - **Data Transfer Objects (DTOs):** Using Python `@dataclass` to create lightweight, strictly typed objects that travel through the pipeline (`ProductionBatch`, `CustomerOrder`).
  - **Encapsulation & Computed Properties:** Explain how data models encapsulate state and use `@property` decorators to dynamically calculate values on the fly (e.g., `cycle_time_hr` or `saleable_units`).
  - **Centralized Configuration:** The use of dictionary-based configs acts as a single source of truth for the entire simulator.

---

## Member 4: Metrics Collection & Event Tracking

**Focus:** How the system observes the simulation and calculates KPIs.

- **Topics to Cover:**
  - How data is extracted from the running simulation without tightly coupling the factory logic to the reporting logic.
  - Key Performance Indicators (KPIs) calculation: tracking fill rates, stockouts, margins, and machine bottlenecks.
  - The daily snapshot mechanism for trend analysis.
- **Key Files:**
  - [cerasim/metrics.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/cerasim/metrics.py)
  - Class: `MetricsCollector` (specifically `compute_kpis()`).
- **Design Patterns & OOP:**
  - **Observer / Collector Pattern:** The `MetricsCollector` acts as a centralized observer. The factory pushes events (breakdowns, completions, daily snapshots) to it, isolating the complex KPI math from the core simulation logic.

---

## Member 5: User Interface, Scenarios & Visualization

**Focus:** The interactive web dashboard and practical scenario testing.

- **Topics to Cover:**
  - The Streamlit application that brings the backend to life.
  - How the user can manipulate custom parameters (demand, machine reliability) via the UI.
  - The built-in scenarios (Baseline, Supply Disruption, Demand Surge, Optimised).
- **Key Files:**
  - [app.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/app.py)
  - Mentioning `cerasim/reports.py` and `cerasim/outputs.py` for charting and CSV generation.
- **Design Patterns & OOP:**
  - **Adapter Pattern:** The `GlobalStreamlitProgress` class is a perfect example of an Adapter pattern. It adapts a standard terminal progress bar API (like Rich) to work seamlessly with Streamlit's UI components without changing the backend logic.
  - **State Management (Caching):** Using Streamlit's `@st.cache_resource` and JSON state files to prevent heavy simulations from re-running unnecessarily upon browser refreshes.

---

> [!IMPORTANT]
> **Transitioning Between Speakers:** Make sure each member naturally hands off to the next. For example, Member 2 can end with, "As these batches flow through the factory, we need a way to track their data, which leads into Member 3's topic..."
