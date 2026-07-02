# CeraSim Web Application Upgrade

This document outlines the plan to upgrade the CeraSim Python CLI application into a modern web application with a frontend dashboard and an interactive simulation capability.

## User Review Required

> [!IMPORTANT]  
> **Technology Stack Choice**: I am proposing a **FastAPI** backend for the Python simulation, paired with a **React (Vite)** frontend using **Recharts** for data visualization and vanilla CSS for a premium, custom design. Please confirm if you are happy with this stack.

> [!WARNING]  
> **Project Structure**: A new `frontend/` directory will be created to house the web app. The existing Python codebase will remain largely intact, but we will add `fastapi` and `uvicorn` to the requirements.

## Open Questions

> [!CAUTION]
>
> 1. **Do you have a specific color scheme or brand identity in mind for SaniCer?** If not, I will design a sleek, modern dark mode interface with vibrant accent colors (e.g., cyan/emerald).
> 2. **Would you like the frontend to support comparing multiple scenarios side-by-side**, similar to what the CLI `main.py` does by default?

## Proposed Changes

---

### Backend (Python)

We will wrap the existing SimPy simulation logic in a FastAPI server to provide RESTful endpoints for the frontend.

#### [NEW] [api.py](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/api.py)

Create a FastAPI application with the following endpoints:

- `GET /api/scenarios`: Returns available scenarios and their descriptions.
- `POST /api/simulate`: Accepts a scenario ID and seed, runs the simulation (using `run_scenario`), and returns the computed KPIs and daily snapshots as JSON.

#### [MODIFY] [requirements.txt](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/requirements.txt)

Add backend web dependencies:

```text
fastapi>=0.110.0
uvicorn>=0.27.0
```

---

### Frontend (React + Vite)

We will scaffold a modern single-page application using Vite.

#### [NEW] [frontend/](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/frontend/)

- Create the Vite project here.
- Implement a dashboard that allows users to configure the simulation.
- Build beautiful, animated charts using Recharts.
- Apply a premium, dynamic CSS design (glassmorphism, smooth transitions, dark mode).

#### [NEW] [frontend/src/App.jsx](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/frontend/src/App.jsx)

Main application component handling state (selected scenario, results) and API calls.

#### [NEW] [frontend/src/components/Dashboard.jsx](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/frontend/src/components/Dashboard.jsx)

The primary layout containing the KPI summary cards and simulation controls.

#### [NEW] [frontend/src/index.css](file:///c:/Users/sithu/My%20Works/UOM/Sem%202/PC/Sem%20Project/sim/frontend/src/index.css)

Global styling for the premium, dark-mode aesthetic with custom animations.

## Current System Limitations

- **Synchronous Execution**: The current simulation runs synchronously in the backend, meaning long-running scenarios could cause API timeouts or block other requests.
- **Lack of Persistence**: There is no database integration. Simulation configurations and results are lost upon server restart or page refresh.
- **Limited Real-time Feedback**: The simulation calculates all results before returning them, preventing real-time visualization of the factory state as time progresses.
- **Single-User Architecture**: The current design lacks user sessions or authentication, making it unsuitable for a multi-tenant environment where different users save their own scenarios.

## Recommended Features

- **Database Integration**: Incorporate a database (e.g., PostgreSQL or SQLite) via an ORM like SQLAlchemy to save user-defined scenarios, historical simulation runs, and custom factory configurations.
- **Asynchronous Task Queue**: Use a task queue (like Celery with Redis) for running simulations in the background, allowing the frontend to poll for status or receive updates without timing out.
- **WebSocket Streaming**: Implement WebSockets in FastAPI to stream simulation progress and live KPI updates to the frontend in real-time, enabling live-updating charts.
- **User Authentication**: Add JWT-based authentication to allow users to create accounts, save their specific simulation parameters, and share scenarios with others.
- **Scenario Comparison View**: Build a dedicated UI to overlay charts and compare KPIs side-by-side between multiple simulation runs.

## Verification Plan

### Automated Tests

- N/A (We will rely on existing python correctness, and test the API endpoints manually).

### Manual Verification

- Start the FastAPI backend using `uvicorn api:app --reload`.
- Start the Vite frontend development server using `npm run dev`.
- Ensure the frontend loads with a premium design.
- Run a simulation from the frontend and verify that the results (KPIs and charts) match the CLI outputs.
