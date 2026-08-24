# What the Project Does and How It Is Implemented

## 1. One-Sentence Description
The platform monitors household appliance usage, simulates electricity consumption, forecasts future demand and bills, recommends energy-saving actions, generates daily/monthly billing, and stores daily billing records in a hash-linked ledger.

## 2. Runtime Flow
The frontend calls the simulation endpoint once every real hour.
Each call represents exactly one simulated hour:
```text
GET /step/Abhishek
```
The backend:
```text
Read appliance states
 -> calculate power
 -> calculate hourly energy
 -> save EnergyRecord
 -> update SimulationState
 -> return state
```
The frontend then refreshes the live dashboard.

## 3. Appliance Model
Appliances have configured power, count, and status. If the fan is ON at 150 W, one simulated hour contributes:
```text
150 / 1000 = 0.15 kWh
```

## 4. Persistent SimulationState
The backend persists:
```text
current_hour
current_day
current_energy_kwh
```
so the simulation state is not dependent only on browser variables.

## 5. Hourly Records
Each `/step` call creates an `EnergyRecord` containing:
```text
user_id
date
hour
power_watts
energy_kwh
```

## 6. End-of-Day Processing
When the hour reaches 24:
```text
daily energy
 -> daily bill
 -> DailyRecord
 -> personalized plan
 -> BlockchainBlock
 -> 30-day check
 -> reset hour/energy
```

## 7. Forecasting
The household forecast returns:
```text
next_hour_kwh
next_6_hours_kwh
projected_daily_kwh
consumed_today_kwh
remaining_today_kwh
projected_monthly_kwh
projected_monthly_bill
current_power_w
current_hour
```
The endpoint identifies the method as **Load-aware weighted forecast**.

## 8. Recommendation Engine
The plan generator uses recent daily records, monthly budget, forecast outputs, and appliance usage. It can identify the largest contributor and suggest reduced usage with an estimated saving.

## 9. Alerts
The alert engine calculates active appliance loads and identifies the highest contributor. It also includes forecast and budget information.

## 10. Daily Billing
At the end of the simulated day, `calc_bill()` is applied to daily energy and the result is persisted in `DailyRecord`.

## 11. Blockchain Billing
The backend finds the latest block. If none exists:
```text
previous_hash = "0"
```
Otherwise:
```text
previous_hash = previous_block.current_hash
```
Then it computes:
```text
current_hash = calculate_block_hash(
    block_number,
    date,
    energy,
    bill,
    previous_hash
)
```
and stores a `BlockchainBlock`.

The chain therefore follows:
```text
Block 1: previous=0,  current=H1
Block 2: previous=H1, current=H2
Block 3: previous=H2, current=H3
```

## 12. Blockchain Validation
The API recomputes hashes and checks:
```text
stored hash == calculated hash
```
and:
```text
current block previous_hash == previous block current_hash
```
The result is exposed through:
```text
hash_valid
linkage_valid
valid
```

## 13. Monthly Billing
When:
```text
completed_days % 30 == 0
```
the system creates `MonthlyBill` with:
```text
month
year
expected
actual
```
This is a 30-day billing period: 30 real days correspond to 30 simulated days.

## 14. Frontend
The simulation loop is:
```text
setInterval(updateSimulation, 3600000)
```
and `updateSimulation()` performs exactly one `/step/{user}` request. `loadDashboard()` only refreshes displayed information.

## 15. Complete Pipeline
```text
Appliance State
      |
      v
Power Calculation
      |
      v
Hourly Energy
      |
      v
EnergyRecord
      |
      +------------------+
      |                  |
      v                  v
 Forecasting         24-hour boundary
                          |
                          v
                     DailyRecord
                          |
                +---------+---------+
                |         |         |
                v         v         v
              Plan    Blockchain  Billing
                          |
                          v
                    Hash Validation
                          |
                          v
                    30-day boundary
                          |
                          v
                     MonthlyBill
```

## 16. Verified Example
A tested 150 W fan produced:
```text
0.15 kWh per simulated hour
```
A tested forecast produced:
```text
Next hour: 0.150 kWh
Next 6 hours: 0.900 kWh
Projected daily: 3.75 kWh
Projected monthly: 112.50 kWh
Projected bill: â‚¹337.50
```
The recommendation identified the fan as the largest contributor. A tested blockchain block returned:
```text
hash_valid = true
linkage_valid = true
valid = true
```

## 17. Implementation Cleanup
An unused legacy `add_block()` path was removed so daily billing/blockchain creation occurs through the active `/step` end-of-day flow. An unused `month_start` variable was also removed. The backend was then checked with:
```text
python -m py_compile backend/main.py
```
with no syntax errors.

## 18. Current State
The core implementation is functionally complete and has been tested for simulation, persistence, forecasting, plans, alerts, billing, blockchain validation, frontend rendering, and browser-console integration.


