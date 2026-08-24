# Project Report
# Intelligent Energy Management and Secure Billing Platform

## 1. Introduction
The project implements an intelligent household energy-management and secure billing platform using a FastAPI backend, JavaScript frontend, SQLite persistence, household forecasting, energy-saving recommendations, and a hash-linked billing ledger.

The application uses a real-time simulation clock in which each real hour corresponds to one simulated hour.

## 2. Problem Statement
A basic energy dashboard can show instantaneous consumption but does not necessarily provide persistent history, future demand estimates, budget-aware recommendations, actionable appliance-level advice, or tamper-evident billing history. This project integrates these functions.

## 3. Objectives
- Simulate household electricity consumption.
- Persist hourly and daily energy records.
- Forecast future household consumption.
- Estimate future electricity expenditure.
- Monitor household budget.
- Generate personalized energy-saving recommendations.
- Generate daily electricity bills.
- Maintain a hash-linked billing ledger.
- Validate billing-record integrity.
- Generate 30-day billing summaries.

## 4. System Design
The frontend provides dashboard, appliance, analytics, budget, plan, alert, and blockchain views. FastAPI provides the REST backend. SQLAlchemy persists application state in SQLite.

Important entities:
`User`, `Appliance`, `EnergyRecord`, `DailyRecord`, `MonthlyBill`, `BlockchainBlock`, and `SimulationState`.

## 5. Real-Time Simulation

The frontend calls `GET /step/{user}` once every real hour. Each request
represents one simulated hour.

```text
1 real hour = 1 simulated hour
24 real hours = 1 simulated day
30 real days = 30 simulated days
```

## 6. Energy Calculation
```text
Energy (kWh) = Power (W) / 1000
```
A 150 W load therefore contributes 0.15 kWh during one simulated hour.

## 7. Hourly Persistence
Each simulated hour creates an `EnergyRecord` containing user, date, hour, power, and energy. `SimulationState` stores the current simulated hour, day, and accumulated daily energy.

## 8. Daily Processing
At the 24-hour boundary the backend:
1. Calculates daily energy.
2. Calculates the daily bill.
3. Creates `DailyRecord`.
4. Generates a personalized plan.
5. Creates a `BlockchainBlock`.
6. Links the new block to the previous block.
7. Checks the 30-day billing boundary.
8. Resets hour and daily energy.

## 9. Forecasting
`GET /household-forecast/{user}` returns next-hour and next-six-hour expected energy, projected daily and monthly consumption, remaining daily energy, projected monthly bill, current power, and current hour. The endpoint reports its method as **Load-aware weighted forecast**.

A tested example produced:
```text
Next hour: 0.150 kWh
Next 6 hours: 0.900 kWh
Projected daily: 3.75 kWh
Projected monthly: 112.50 kWh
Projected bill: â‚¹337.50
```

## 10. Recommendation Engine
After a day completes, the plan generator uses recent daily records, monthly budget, forecast outputs, and appliance usage to identify high-use appliances and suggest reductions.

Example:
```text
FAN: used 20 hrs; consider reducing to 14 hrs
to save approximately 0.45 kWh.
```

## 11. Budget and Alerts
The alert system identifies the highest active appliance load and combines this with forecast/budget information. For example, a 150 W fan can be reported as the high-use appliance while the system shows projected monthly cost and remaining budget.

## 12. Daily Billing
The billing flow is:
```text
24 hourly records -> DailyRecord -> daily energy -> daily bill
```

## 13. Blockchain Billing
Each completed simulated day creates a billing block with:
- block number
- date
- energy
- bill
- previous hash
- current hash

The current hash is generated from canonical billing data and the previous hash by the application's `calculate_block_hash()` function.

Conceptually:
```text
Hn = SHA256(block_number || date || energy || bill || previous_hash)
```
The exact serialization is determined by the implementation.

## 14. Blockchain Validation
The blockchain endpoint reproduces the expected hash and checks previous-hash linkage. It reports `calculated_hash`, `hash_valid`, `linkage_valid`, and `valid`.

A tested latest block returned all three validation flags as `true`.

## 15. Monthly Billing
When:
```text
completed_days % 30 == 0
```
a `MonthlyBill` is created. It stores month number, year, expected budget, and actual bill. The project uses a 30-day billing period, corresponding to 30 real days.

## 16. Frontend Integration
The frontend schedules:
```text
setInterval(updateSimulation, 3600000)
```
`updateSimulation()` makes exactly one `/step/{user}` request and then refreshes the dashboard. Dashboard refresh does not itself advance simulation time.

## 17. Testing
Verified during development:
- successful login
- persistent simulation state
- appliance persistence
- real-time hourly simulation
- daily rollover
- daily billing records
- 30-day monthly boundary
- forecasting
- personalized plans
- alerts
- blockchain records
- hash verification
- chain linkage
- frontend plan formatting
- alert rendering
- blockchain rendering
- clean browser console

The simulation was advanced across a monthly boundary and the monthly-record count increased, demonstrating creation of a new billing-period record.

## 18. Limitations
1. Simulation time follows a real-time hourly clock; each frontend simulation step represents one hour.
2. Appliance loads are configured values rather than physical smart-meter measurements.
3. The blockchain is a hash-linked application ledger rather than a distributed blockchain network.
4. Forecasting is designed for the project's household simulation.
5. Authentication requires further hardening for production.
6. Billing periods consist of 30 real days, corresponding to 30 simulated days.

## 19. Future Work
Potential extensions include real smart-meter/IoT integration, improved forecasting, dynamic tariffs, appliance scheduling optimization, anomaly detection, stronger authentication, production database deployment, distributed blockchain integration, automated testing, CI/CD, and cloud deployment.

## 20. Conclusion
The project connects measurement, persistence, forecasting, budget analysis, recommendations, daily billing, hash-linked billing records, and monthly billing into one integrated prototype. The real-time simulation models the complete household lifecycle using one real hour per simulated hour.


