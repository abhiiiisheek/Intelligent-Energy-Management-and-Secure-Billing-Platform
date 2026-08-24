# Intelligent Energy Management and Secure Billing Platform

## Overview
An intelligent household energy-management platform combining real-time energy simulation, consumption forecasting, budget monitoring, personalized energy-saving recommendations, alerts, daily/monthly billing, and a tamper-evident hash-linked billing ledger.

### Simulation model
- 1 real hour = 1 simulated hour

- 24 real hours = 1 simulated day
- 30 real days = 1 simulated billing period

## What the Project Does
The system models household appliances, calculates power and hourly energy, persists consumption, forecasts future demand and bills, monitors budgets, generates recommendations, creates daily billing records, and maintains a hash-linked billing ledger.

## Main Features
1. Live appliance/energy simulation
2. Persistent hourly energy records
3. Load-aware household forecasting
4. Personalized energy-saving plans
5. Budget monitoring and alerts
6. Daily electricity billing
7. Hash-linked blockchain billing records
8. Hash and chain-link validation
9. 30-day monthly billing summaries

## Architecture
```text
Frontend (HTML/CSS/JavaScript)
              |
              v
        FastAPI Backend
              |
      +-------+--------+----------------+
      |                |                |
      v                v                v
 Simulation       Forecasting      Recommendation
   Engine           Engine            Engine
      |                |                |
      +----------------+----------------+
                       |
                       v
                    SQLite
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
 EnergyRecord    DailyRecord      MonthlyBill
                       |
                       v
                BlockchainBlock
                       |
                       v
              Hash/Link Validation
```

## Energy Calculation
```text
Energy (kWh) = Power (W) / 1000
```
For a 150 W fan:
```text
150 / 1000 = 0.15 kWh per simulated hour
```

## Forecasting
`GET /household-forecast/{user}` returns next-hour, next-six-hour, projected daily/monthly consumption and projected monthly bill. The endpoint reports the method as **Load-aware weighted forecast**.

## Personalized Plans
`GET /plan/{user}` generates recommendations using consumption history, budget, forecasts, and appliance usage. Example: identifying a fan as the largest contributor and recommending reduced usage.

## Alerts
`GET /alerts/{user}` reports high active appliance usage together with forecast and budget information.

## Daily Billing
After 24 simulated hours:
```text
Hourly records -> DailyRecord -> daily energy -> daily bill
```

## Blockchain Billing
Each completed simulated day creates a `BlockchainBlock` containing block number, date, energy, bill, previous hash, and current hash. The API validates the stored hash and previous-hash linkage.

A verified block reports:
```text
hash_valid = true
linkage_valid = true
valid = true
```

## Monthly Billing
After 30 completed simulated days, a `MonthlyBill` is created containing month number, year, expected budget, and actual bill. This billing period consists of 30 real days.

## Main API Endpoints
| Endpoint | Purpose |
|---|---|
| `POST /login` | Login |
| `GET /status/{user}` | Current household state |
| `GET /step/{user}` | Advance one simulated hour |
| `GET /household-forecast/{user}` | Household forecast |
| `GET /plan/{user}` | Energy-saving plan |
| `GET /alerts/{user}` | Alerts |
| `GET /summary/{user}` | Monthly billing summary |
| `GET /blockchain/{user}` | Blockchain billing ledger |
| `POST /budget/{user}/{amount}` | Set budget |
| `POST /toggle/{user}/{device}` | Toggle appliance |
| `POST /add/{user}` | Add appliance |

## Database Entities
- `EnergyRecord` Ã¢â‚¬â€ hourly power/energy
- `DailyRecord` Ã¢â‚¬â€ completed daily consumption and bill
- `BlockchainBlock` Ã¢â‚¬â€ billing ledger and hashes
- `MonthlyBill` Ã¢â‚¬â€ completed billing-period summary
- `SimulationState` Ã¢â‚¬â€ current simulated hour/day/energy
- `Appliance` Ã¢â‚¬â€ appliance configuration and state

## Technology Stack
Python, FastAPI, SQLAlchemy, SQLite, Uvicorn, HTML, CSS, JavaScript, Python forecasting/ML components, SHA-256-based hashing.

## Running
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m py_compile backend\main.py
uvicorn backend.main:app --reload
```

Backend:
```text
http://127.0.0.1:8000
```

## Demonstration Flow
Login -> observe live consumption -> forecasting -> energy-saving plan -> alerts -> complete a simulated day -> inspect daily billing/blockchain -> complete 30 simulated days -> inspect monthly summary -> verify blockchain integrity.

## Current Verification
The implementation was tested for login, persistent simulation state, appliance persistence, real-time hourly simulation, daily rollover, daily/monthly records, forecasting, plans, alerts, blockchain records, hash verification, chain linkage, frontend rendering, and clean browser-console integration.





