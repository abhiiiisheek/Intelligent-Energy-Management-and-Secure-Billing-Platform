from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# ============================================================
# DATABASE
# ============================================================

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import (
    User,
    Appliance,
    SimulationState,
    EnergyRecord,
    DailyRecord,
    BlockchainBlock,
    MonthlyBill
)

# ============================================================
# MACHINE LEARNING
# ============================================================

import joblib
import pandas as pd

# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Intelligent Energy Management and Secure Billing Platform",
    description="AI-driven energy estimation, forecasting, monitoring and secure billing platform.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# ML MODEL
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FRONTEND_DIR = PROJECT_ROOT / "frontend"

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "forecast_model.pkl"
)

try:
    forecast_model = joblib.load(MODEL_PATH)

    print(
        "Forecasting model loaded successfully."
    )

except FileNotFoundError:

    forecast_model = None

    print(
        f"WARNING: Forecasting model not found at {MODEL_PATH}"
    )


# ============================================================
# HOUSEHOLD ENERGY ESTIMATION MODELS
# ============================================================

class ApplianceEstimate(BaseModel):

    name: str = Field(
        ...,
        min_length=1
    )

    power: float = Field(
        ...,
        gt=0
    )

    count: int = Field(
        ...,
        gt=0
    )

    hours_per_day: float = Field(
        ...,
        ge=0,
        le=24
    )


class EnergyEstimateRequest(BaseModel):

    household_size: int = Field(
        ...,
        gt=0
    )

    appliances: List[ApplianceEstimate]


# ============================================================
# RUNTIME STATE
# ============================================================

# Account + appliances are persistent in SQLite.
#
# Live simulation state is still kept in memory for now:
#
#   energy
#   hour
#   day
#   hourly
#   daily
#   plans
#   blockchain
#   monthly_bills
#
# These will be migrated to SQLite in a later step.

users = {}


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# ============================================================
# DEFAULT APPLIANCES
# ============================================================

DEFAULT_APPLIANCES = [

    {
        "name": "light",
        "power": 10,
        "count": 2
    },

    {
        "name": "fan",
        "power": 75,
        "count": 2
    },

    {
        "name": "ac",
        "power": 1500,
        "count": 1
    },

    {
        "name": "fridge",
        "power": 200,
        "count": 1
    }

]


# ============================================================
# CREATE RUNTIME USER
# ============================================================

def create_runtime_user(
    password_hash,
    monthly_budget=3000,
    household_size=None
):

    return {

        "password": password_hash,

        "household_size": household_size,

        "appliances": {},

        "status": {},

        "usage_hours": {},

        "energy": 0,

        "hour": 0,

        "day": 0,

        "hourly": [],

        "daily": [],

        "plans": [],

        "blockchain": [],

        "monthly_budget": monthly_budget,

        "monthly_bills": [],

        "start_date": datetime.now()

    }


# ============================================================
# LOAD APPLIANCES FROM DATABASE
# ============================================================

def load_user_appliances(
    db,
    db_user,
    runtime_user
):

    appliance_rows = (
        db.query(Appliance)
        .filter(
            Appliance.user_id == db_user.id
        )
        .all()
    )

    # --------------------------------------------------------
    # Existing user with no appliances
    # --------------------------------------------------------

    if not appliance_rows:

        for item in DEFAULT_APPLIANCES:

            appliance = Appliance(
                user_id=db_user.id,
                name=item["name"],
                power=item["power"],
                count=item["count"],
                status=False,
                usage_hours=0
            )

            db.add(appliance)

        db.commit()

        appliance_rows = (
            db.query(Appliance)
            .filter(
                Appliance.user_id == db_user.id
            )
            .all()
        )

    # --------------------------------------------------------
    # Copy database appliances into runtime state
    # --------------------------------------------------------

    for appliance in appliance_rows:

        runtime_user["appliances"][
            appliance.name
        ] = {

            "power": appliance.power,

            "count": appliance.count

        }

        runtime_user["status"][
            appliance.name
        ] = bool(
            appliance.status
        )

        runtime_user["usage_hours"][
            appliance.name
        ] = float(
            appliance.usage_hours or 0
        )


# ============================================================
# SIGN UP
# ============================================================

@app.post("/signup")
def signup(
    user: str,
    password: str,
    db: Session = Depends(get_db)
):
    username = user.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty"
        )

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 3 characters"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password cannot be empty"
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters"
        )

    # --------------------------------------------------------
    # CHECK WHETHER USER ALREADY EXISTS
    # --------------------------------------------------------

    existing_user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # --------------------------------------------------------
    # HASH PASSWORD
    # --------------------------------------------------------

    password_hash = hash_password(password)

    # --------------------------------------------------------
    # CREATE DATABASE USER
    # --------------------------------------------------------

    db_user = User(
        username=username,
        password=password_hash,
        household_size=None,
        monthly_budget=3000
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # --------------------------------------------------------
    # CREATE RUNTIME STATE
    # --------------------------------------------------------

    runtime_user = create_runtime_user(
        password_hash=db_user.password,
        monthly_budget=(
            db_user.monthly_budget
            if db_user.monthly_budget is not None
            else 3000
        ),
        household_size=db_user.household_size
    )

    # --------------------------------------------------------
    # LOAD DEFAULT APPLIANCES
    # --------------------------------------------------------

    load_user_appliances(
        db,
        db_user,
        runtime_user
    )

    # --------------------------------------------------------
    # STORE RUNTIME USER
    # --------------------------------------------------------

    users[username] = runtime_user

    return {
        "msg": "signup success",
        "user": username
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    user: str,
    password: str,
    db: Session = Depends(get_db)
):
    username = user.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty"
        )

    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password cannot be empty"
        )

    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    db_user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # VERIFY PASSWORD
    # --------------------------------------------------------

    password_hash = hash_password(password)

    if db_user.password != password_hash:
        raise HTTPException(
            status_code=401,
            detail="Wrong password"
        )

    # --------------------------------------------------------
    # CREATE RUNTIME STATE
    # --------------------------------------------------------

    runtime_user = create_runtime_user(
        password_hash=db_user.password,
        monthly_budget=(
            db_user.monthly_budget
            if db_user.monthly_budget is not None
            else 3000
        ),
        household_size=db_user.household_size
    )

    # --------------------------------------------------------
    # LOAD PERSISTENT APPLIANCES
    # --------------------------------------------------------

    load_user_appliances(
        db,
        db_user,
        runtime_user
    )

    # --------------------------------------------------------
    # STORE RUNTIME USER
    # --------------------------------------------------------

    users[username] = runtime_user

    return {
        "msg": "login success",
        "user": username
    }


# ============================================================
# POWER CALCULATION
# ============================================================

def calc_power(u):

    return sum(

        u["appliances"][appliance]["power"]
        *
        u["appliances"][appliance]["count"]

        for appliance in u["appliances"]

        if u["status"][appliance]

    )


# ============================================================
# BILL CALCULATION
# ============================================================

def calc_bill(units):

    if units == 0:

        return 0

    if units <= 100:

        cost = (
            units * 2
        )

    elif units <= 200:

        cost = (
            100 * 2
            +
            (units - 100) * 3
        )

    elif units <= 500:

        cost = (
            100 * 2
            +
            100 * 3
            +
            (units - 200) * 5
        )

    else:

        cost = (
            100 * 2
            +
            100 * 3
            +
            300 * 5
            +
            (units - 500) * 8
        )

    fixed_charge = 100

    return round(
        cost + fixed_charge,
        2
    )

# ============================================================
# CANONICAL BLOCKCHAIN HASH
# ============================================================

def calculate_block_hash(
    block_number,
    date,
    energy,
    bill,
    previous_hash
):
    """
    Generate a deterministic SHA-256 hash for a blockchain block.

    The exact same function is used when creating and
    validating blocks.
    """

    data = (
        f"{block_number}|"
        f"{date}|"
        f"{float(energy):.2f}|"
        f"{float(bill):.2f}|"
        f"{previous_hash}"
    )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()

# ============================================================
# HOUSEHOLD ENERGY ESTIMATION
# ============================================================

@app.post("/estimate")
def estimate_energy(
    request: EnergyEstimateRequest
):

    daily_total = 0.0

    appliance_breakdown = []

    for appliance in request.appliances:

        daily_kwh = (
            appliance.power
            *
            appliance.count
            *
            appliance.hours_per_day
            /
            1000
        )

        monthly_kwh = (
            daily_kwh * 30
        )

        daily_total += daily_kwh

        appliance_breakdown.append({

            "name": appliance.name,

            "power_watts":
                appliance.power,

            "count":
                appliance.count,

            "hours_per_day":
                appliance.hours_per_day,

            "daily_kwh":
                round(
                    daily_kwh,
                    2
                ),

            "monthly_kwh":
                round(
                    monthly_kwh,
                    2
                )

        })

    monthly_total = (
        daily_total * 30
    )

    estimated_bill = calc_bill(
        monthly_total
    )

    return {

        "household_size":
            request.household_size,

        "daily_consumption_kwh":
            round(
                daily_total,
                2
            ),

        "monthly_consumption_kwh":
            round(
                monthly_total,
                2
            ),

        "estimated_monthly_bill":
            estimated_bill,

        "currency":
            "INR",

        "appliances":
            appliance_breakdown

    }


# ============================================================
# ALERT
# ============================================================

def get_alert(
    u,
    db,
    user_id
):

    # --------------------------------------------------------
    # Current active appliance load
    # --------------------------------------------------------

    active = {

        appliance:
            u["appliances"][appliance]["power"]
            *
            u["appliances"][appliance]["count"]

        for appliance in u["appliances"]

        if u["status"][appliance]

    }

    lines = []

    # --------------------------------------------------------
    # Appliance alert
    # --------------------------------------------------------

    if active:

        high = max(
            active,
            key=active.get
        )

        lines.append(
            f"High usage due to "
            f"{high.upper()} "
            f"({active[high]}W)"
        )

    else:

        lines.append(
            "No active appliances"
        )

    # --------------------------------------------------------
    # Household forecast
    # --------------------------------------------------------

    try:

        forecast = forecast_household_consumption(
            u,
            db,
            user_id
        )

        projected_monthly_bill = float(
            forecast.get(
                "projected_monthly_bill",
                0
            )
        )

        projected_monthly_kwh = float(
            forecast.get(
                "projected_monthly_kwh",
                0
            )
        )

        monthly_budget = float(
            u.get(
                "monthly_budget",
                3000
            )
        )

        # ----------------------------------------------------
        # Budget warning
        # ----------------------------------------------------

        if projected_monthly_bill > monthly_budget:

            excess = (
                projected_monthly_bill
                -
                monthly_budget
            )

            lines.append(
                f"WARNING: Projected monthly bill is "
                f"₹{projected_monthly_bill:.2f}, "
                f"which is ₹{excess:.2f} above "
                f"the ₹{monthly_budget:.2f} budget."
            )

        else:

            remaining = (
                monthly_budget
                -
                projected_monthly_bill
            )

            lines.append(
                f"Forecast: monthly bill is "
                f"₹{projected_monthly_bill:.2f}. "
                f"₹{remaining:.2f} remains "
                f"within the monthly budget."
            )

        # ----------------------------------------------------
        # Forecast consumption
        # ----------------------------------------------------

        lines.append(
            f"Projected monthly consumption: "
            f"{projected_monthly_kwh:.2f} kWh."
        )

    except Exception as error:

        print(
            f"Alert forecast unavailable: {error}"
        )

    return "\n".join(
        lines
    )


# ============================================================
# PLAN
# ============================================================

def generate_plan(
    u,
    db,
    user_id
):

    # --------------------------------------------------------
    # Load persistent daily energy history
    # --------------------------------------------------------

    daily_records = (
        db.query(DailyRecord)
        .filter(
            DailyRecord.user_id == user_id
        )
        .order_by(
            DailyRecord.date.desc()
        )
        .limit(30)
        .all()
    )

    daily_history = [
        float(record.energy_kwh)
        for record in reversed(
            daily_records
        )
        if float(record.energy_kwh) >= 0
    ]

    monthly_budget = float(
        u.get(
            "monthly_budget",
            3000
        )
    )

    daily_budget = (
        monthly_budget / 30
    )

    # --------------------------------------------------------
    # Forecast household consumption
    # --------------------------------------------------------

    forecast = forecast_household_consumption(
        u,
        db,
        user_id
    )

    projected_daily_kwh = float(
        forecast.get(
            "projected_daily_kwh",
            0
        )
    )

    projected_monthly_bill = float(
        forecast.get(
            "projected_monthly_bill",
            0
        )
    )

    next_hour_kwh = float(
        forecast.get(
            "next_hour_kwh",
            0
        )
    )

    appliances = u.get(
        "appliances",
        {}
    )

    usage_hours = u.get(
        "usage_hours",
        {}
    )

    # --------------------------------------------------------
    # No completed day yet
    # --------------------------------------------------------

    if not daily_history:

        return (
            "Collecting household data. "
            "Continue using the simulator to generate "
            "personalized energy recommendations."
        )

    # --------------------------------------------------------
    # Latest measured daily consumption
    # --------------------------------------------------------

    last_day = float(
        daily_history[-1]
    )

    # --------------------------------------------------------
    # Estimate daily cost
    # --------------------------------------------------------

    estimated_daily_cost = (
        monthly_budget / 30
    )

    lines = []

    # --------------------------------------------------------
    # --------------------------------------------------------
    # Forecast status
    # --------------------------------------------------------

    if projected_monthly_bill > monthly_budget:

        bill_excess = (
            projected_monthly_bill -
            monthly_budget
        )

        lines.append(
            f"FORECAST WARNING: "
            f"Projected monthly consumption is "
            f"{forecast.get('projected_monthly_kwh', 0):.2f} kWh, "
            f"with an estimated monthly bill of "
            f"₹{projected_monthly_bill:.2f}. "
            f"This is ₹{bill_excess:.2f} above "
            f"the monthly budget."
        )

    else:

        bill_remaining = (
            monthly_budget -
            projected_monthly_bill
        )

        lines.append(
            f"FORECAST: "
            f"Projected monthly consumption is "
            f"{forecast.get('projected_monthly_kwh', 0):.2f} kWh "
            f"with an estimated monthly bill of "
            f"₹{projected_monthly_bill:.2f}. "
            f"₹{bill_remaining:.2f} remains "
            f"within the monthly budget."
        )
        lines.append(
            f"Next-hour expected consumption: "
            f"{next_hour_kwh:.3f} kWh."
        )
    

    # --------------------------------------------------------
    # Budget status
    # --------------------------------------------------------

    if last_day > daily_budget:

        excess = (
            last_day -
            daily_budget
        )

        lines.append(
            f"WARNING: Daily energy usage exceeded "
            f"the target by {excess:.2f} kWh."
        )

    else:

        remaining = (
            daily_budget -
            last_day
        )

        lines.append(
            f"Within daily energy target. "
            f"{remaining:.2f} kWh remaining."
        )

    # --------------------------------------------------------
    # Appliance-level recommendations
    # --------------------------------------------------------

    appliance_usage = []

    for device, hours in usage_hours.items():

        hours = float(hours)

        if hours <= 0:
            continue

        appliance_data = appliances.get(
            device,
            {}
        )

        power = float(
            appliance_data.get(
                "power",
                0
            )
        )

        estimated_energy = (
            power *
            hours /
            1000
        )

        appliance_usage.append(
            (
                device,
                hours,
                power,
                estimated_energy
            )
        )

    # --------------------------------------------------------
    # Prioritize highest energy-consuming appliances
    # --------------------------------------------------------

    appliance_usage.sort(
        key=lambda item: item[3],
        reverse=True
    )

    recommendations = 0

    for (
        device,
        hours,
        power,
        estimated_energy
    ) in appliance_usage:

        if recommendations >= 3:
            break

        if estimated_energy <= 0:
            continue

        suggested_hours = max(
            1,
            int(
                hours * 0.7
            )
        )

        potential_saving = (
            power *
            max(
                0,
                hours - suggested_hours
            ) /
            1000
        )

        if potential_saving <= 0:
            continue

        lines.append(
            f"{device.upper()}: "
            f"used {hours:.0f} hrs; "
            f"consider reducing to "
            f"{suggested_hours} hrs "
            f"to save approximately "
            f"{potential_saving:.2f} kWh."
        )

        recommendations += 1

    # --------------------------------------------------------
    # General recommendation
    # --------------------------------------------------------

    if appliance_usage:

        highest_device = appliance_usage[0][0]

        lines.append(
            f"Priority: reduce usage of "
            f"{highest_device.upper()}, "
            f"the largest contributor to household "
            f"energy consumption."
        )

    else:

        lines.append(
            "Continue collecting appliance usage data "
            "for more personalized recommendations."
        )

    return "\n".join(
        lines
    )

# ============================================================
# ML PREDICTION
# ============================================================

def predict_grid_demand():

    if forecast_model is None:

        raise HTTPException(

            status_code=500,

            detail=(
                "Forecasting model "
                "is not available."
            )

        )

    today = datetime.now()

    day_of_week = (
        today.weekday()
    )

    month = (
        today.month
    )

    features = pd.DataFrame({

        "DayOfWeek":
            [day_of_week],

        "Month":
            [month]

    })

    prediction = (

        forecast_model
        .predict(features)[0]

    )

    return {

        "prediction":
            round(
                float(prediction),
                2
            ),

        "unit":
            "MW",

        "date":
            today.strftime(
                "%Y-%m-%d"
            ),

        "day_of_week":
            today.strftime(
                "%A"
            ),

        "month":
            today.strftime(
                "%B"
            )

    }


# ============================================================
# ADD BLOCK
# ============================================================

# ============================================================
# STEP / LIVE SIMULATION
# ============================================================

@app.get("/step/{user}")
def step(
    user: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate user in runtime state
    # --------------------------------------------------------

    if user not in users:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    u = users[user]

    # --------------------------------------------------------
    # Get persistent database user
    # --------------------------------------------------------

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )

    # --------------------------------------------------------
    # Get persistent simulation state
    # --------------------------------------------------------

    state = (
        db.query(SimulationState)
        .filter(
            SimulationState.user_id == db_user.id
        )
        .first()
    )

    # Create state if it does not exist
    if state is None:

        state = SimulationState(

            user_id=db_user.id,

            current_hour=0,

            current_day=0,

            current_energy_kwh=0.0

        )

        db.add(state)

        db.commit()

        db.refresh(state)

    # --------------------------------------------------------
    # Synchronize runtime state with database state
    # --------------------------------------------------------

    u["hour"] = state.current_hour

    u["day"] = state.current_day

    u["energy"] = state.current_energy_kwh

    # --------------------------------------------------------
    # Calculate current appliance power
    # --------------------------------------------------------

    power = calc_power(u)

    # --------------------------------------------------------
    # Calculate energy consumed during this hour
    #
    # Each /step call represents one simulated hour.
    #
    # Energy (kWh) = Power (W) / 1000
    # --------------------------------------------------------

    hourly_energy = 0.0

    if power > 0:

        hourly_energy = power / 1000
    # --------------------------------------------------------
    # Track appliance usage
    # --------------------------------------------------------

    for appliance in u["appliances"]:

        if u["status"][appliance]:

            u["usage_hours"][appliance] += 1

    # --------------------------------------------------------
    # Save hourly energy record
    # --------------------------------------------------------

    energy_record = EnergyRecord(

        user_id=db_user.id,

        date=datetime.now(),

        hour=state.current_hour,

        power_watts=power,

        energy_kwh=hourly_energy

    )

    db.add(
        energy_record
    )

    # --------------------------------------------------------
    # Update persistent simulation state
    # --------------------------------------------------------

    new_energy = (
        state.current_energy_kwh
        +
        hourly_energy
    )

    new_hour = (
        state.current_hour
        +
        1
    )


    # ========================================================
    # END OF DAY
    # ========================================================

    if new_hour >= 24:

        # ----------------------------------------------------
        # Use the persistent day's energy
        # ----------------------------------------------------

        day_energy = round(
            new_energy,
            2
        )

        # ----------------------------------------------------
        # Create daily record
        # ----------------------------------------------------

        daily_date = (
            u["start_date"]
            +
            timedelta(
                days=state.current_day
            )
        ).date()

        daily_bill = calc_bill(
            day_energy
        )

        daily_record = DailyRecord(

            user_id=db_user.id,

            date=datetime.combine(
                daily_date,
                datetime.min.time()
            ),

            energy_kwh=day_energy,

            bill=daily_bill

        )

        db.add(
            daily_record
        )


        # ----------------------------------------------------
        # Generate personalized plan for completed day
        # ----------------------------------------------------

        plan = generate_plan(
            u,
            db,
            db_user.id
        )

        u["plans"].append(
            f"Day {state.current_day + 1}: "
            f"{plan}"
        )

        # ----------------------------------------------------
        # Blockchain block
        # ----------------------------------------------------

        previous_block = (
            db.query(BlockchainBlock)
            .filter(
                BlockchainBlock.user_id
                == db_user.id
            )
            .order_by(
                BlockchainBlock.block_number.desc()
            )
            .first()
        )

        previous_hash = (

            previous_block.current_hash

            if previous_block

            else "0"

        )

        block_number = (
            state.current_day + 1
        )

        current_hash = calculate_block_hash(
            block_number=block_number,
            date=daily_date,
            energy=day_energy,
            bill=daily_bill,
            previous_hash=previous_hash
        )

        blockchain_record = BlockchainBlock(

            user_id=db_user.id,

            block_number=block_number,

            date=datetime.combine(
                daily_date,
                datetime.min.time()
            ),

            energy_kwh=day_energy,

            bill=daily_bill,

            previous_hash=previous_hash,

            current_hash=current_hash

        )

        db.add(
            blockchain_record
        )

        # ----------------------------------------------------
        # Monthly bill
        # ----------------------------------------------------

        completed_days = (
            state.current_day + 1
        )

        if completed_days % 30 == 0:

            month_number = (
                completed_days // 30
            )


            previous_month_records = (
                db.query(DailyRecord)
                .filter(
                    DailyRecord.user_id
                    == db_user.id
                )
                .order_by(
                    DailyRecord.date.desc()
                )
                .limit(29)
                .all()
            )

            previous_bill = round(
                sum(
                    r.bill
                    for r in previous_month_records
                ),
                2
            )
            actual_bill = round(
                previous_bill + daily_bill,
                2
            )

            monthly_bill = MonthlyBill(

                user_id=db_user.id,

                month=month_number,

                year=daily_date.year,

                expected=db_user.monthly_budget,

                actual=actual_bill

            )

            db.add(
                monthly_bill
            )

        # ----------------------------------------------------
        # Reset for next day
        # ----------------------------------------------------

        state.current_day += 1

        state.current_hour = 0

        state.current_energy_kwh = 0.0

        u["day"] = state.current_day

        u["hour"] = 0

        u["energy"] = 0.0

        u["hourly"] = []

        u["usage_hours"] = {
            k: 0
            for k in u["appliances"]
        }

    else:

        # ----------------------------------------------------
        # Normal hourly update
        # ----------------------------------------------------

        state.current_hour = new_hour

        state.current_energy_kwh = new_energy

        u["hour"] = new_hour

        u["energy"] = new_energy

        u["hourly"].append(
            new_energy
        )

    # --------------------------------------------------------
    # Commit all database changes
    # --------------------------------------------------------

    db.commit()

    # --------------------------------------------------------
    # Refresh state
    # --------------------------------------------------------

    db.refresh(state)

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "msg": "ok",

        "power": power,

        "hourly_energy_kwh":
            round(
                hourly_energy,
                4
            ),

        "current_hour":
            state.current_hour,

        "current_day":
            state.current_day,

        "total_energy_kwh":
            round(
                state.current_energy_kwh,
                4
            )

    }


# ============================================================
# STATUS
# ============================================================

@app.get("/status/{user}")
def status(user: str):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    u = users[user]

    power = calc_power(u)

    return {

        "power":
            power,

        "current":
            round(
                power / 230,
                2
            ) if power else 0,

        "energy":
            round(
                u["energy"],
                2
            ),

        "hour":
            u["hour"],

        "appliances":
            u["status"]

    }


# ============================================================
# TOGGLE APPLIANCE
# ============================================================

@app.get("/toggle/{user}/{device}")
def toggle(
    user: str,
    device: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate runtime user
    # --------------------------------------------------------

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    u = users[user]

    # --------------------------------------------------------
    # Validate appliance
    # --------------------------------------------------------

    if device not in u["appliances"]:

        raise HTTPException(

            status_code=404,

            detail=f"Appliance '{device}' not found"

        )

    # --------------------------------------------------------
    # Toggle runtime state
    # --------------------------------------------------------

    new_status = not u["status"][device]

    u["status"][device] = new_status

    # --------------------------------------------------------
    # Find database user
    # --------------------------------------------------------

    db_user = (

        db.query(User)

        .filter(
            User.username == user
        )

        .first()

    )

    if db_user is None:

        raise HTTPException(

            status_code=404,

            detail="User not found in database"

        )

    # --------------------------------------------------------
    # Find database appliance
    # --------------------------------------------------------

    appliance = (

        db.query(Appliance)

        .filter(

            Appliance.user_id
            == db_user.id,

            Appliance.name
            == device

        )

        .first()

    )

    if appliance is None:

        raise HTTPException(

            status_code=404,

            detail=(
                f"Appliance '{device}' "
                f"not found in database"
            )

        )

    # --------------------------------------------------------
    # Persist status in SQLite
    # --------------------------------------------------------

    appliance.status = new_status

    db.commit()

    db.refresh(
        appliance
    )

    print(
        f"Updated {user}/{device}: "
        f"{appliance.status}"
    )

    return u["status"]


# ============================================================
# ADD APPLIANCE
# ============================================================

@app.post("/add/{user}")
def add(

    user: str,

    name: str,

    power: int,

    count: int,

    db: Session = Depends(get_db)

):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    name = name.strip()

    if not name:

        raise HTTPException(

            status_code=400,

            detail=(
                "Appliance name "
                "cannot be empty"
            )

        )

    if power <= 0:

        raise HTTPException(

            status_code=400,

            detail=(
                "Power must be "
                "greater than 0"
            )

        )

    if count <= 0:

        raise HTTPException(

            status_code=400,

            detail=(
                "Count must be "
                "greater than 0"
            )

        )

    u = users[user]

    # --------------------------------------------------------
    # Get database user
    # --------------------------------------------------------

    db_user = (

        db.query(User)

        .filter(
            User.username == user
        )

        .first()

    )

    if db_user is None:

        raise HTTPException(

            status_code=404,

            detail="User not found in database"

        )

    # --------------------------------------------------------
    # Check whether appliance already exists
    # --------------------------------------------------------

    existing = (

        db.query(Appliance)

        .filter(

            Appliance.user_id
            == db_user.id,

            Appliance.name
            == name

        )

        .first()

    )

    if existing is not None:

        # Update existing appliance

        existing.power = power

        existing.count = count

        # Preserve existing status

        if existing.status is None:

            existing.status = False

        db.commit()

        # Update runtime

        u["appliances"][name] = {

            "power":
                power,

            "count":
                count

        }

        if name not in u["status"]:

            u["status"][name] = (
                bool(existing.status)
            )

        if name not in u["usage_hours"]:

            u["usage_hours"][name] = 0

        return {

            "msg":
                "appliance updated"

        }

    # --------------------------------------------------------
    # Create new appliance
    # --------------------------------------------------------

    appliance = Appliance(

        user_id=db_user.id,

        name=name,

        power=power,

        count=count,

        status=False,

        usage_hours=0

    )

    db.add(appliance)

    db.commit()

    db.refresh(
        appliance
    )

    # Update runtime

    u["appliances"][name] = {

        "power":
            power,

        "count":
            count

    }

    u["status"][name] = False

    u["usage_hours"][name] = 0

    return {
        "msg": "added"
    }


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics/{user}")
def analytics(
    user: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Get persistent database user
    # --------------------------------------------------------

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # HOURLY ANALYTICS
    #
    # Read directly from SQLite EnergyRecord.
    # Each record represents one simulated hour.
    # --------------------------------------------------------

    hourly_records = (
        db.query(EnergyRecord)
        .filter(
            EnergyRecord.user_id == db_user.id
        )
        .order_by(
            EnergyRecord.id
        )
        .all()
    )

    hourly = [
        round(
            record.energy_kwh,
            4
        )
        for record in hourly_records
    ]

    # --------------------------------------------------------
    # DAILY ANALYTICS
    #
    # Read directly from SQLite DailyRecord.
    # --------------------------------------------------------

    daily_records = (
        db.query(DailyRecord)
        .filter(
            DailyRecord.user_id == db_user.id
        )
        .order_by(
            DailyRecord.date
        )
        .all()
    )

    daily = [
        round(
            record.energy_kwh,
            4
        )
        for record in daily_records
    ]

    # --------------------------------------------------------
    # WEEKLY ANALYTICS
    #
    # Group daily consumption into 7-day periods.
    # --------------------------------------------------------

    weekly = [

        round(
            sum(
                daily[i:i + 7]
            ),
            4
        )

        for i in range(
            0,
            len(daily),
            7
        )

    ]

    # --------------------------------------------------------
    # MONTHLY ENERGY ANALYTICS
    #
    # Group daily consumption into 30-day periods.
    # --------------------------------------------------------

    monthly_energy = [

        round(
            sum(
                daily[i:i + 30]
            ),
            4
        )

        for i in range(
            0,
            len(daily),
            30
        )

    ]

    # --------------------------------------------------------
    # MONTHLY BILLING
    #
    # Read persistent MonthlyBill records.
    # --------------------------------------------------------

    monthly_bills = (
        db.query(MonthlyBill)
        .filter(
            MonthlyBill.user_id == db_user.id
        )
        .order_by(
            MonthlyBill.year,
            MonthlyBill.month
        )
        .all()
    )

    billing = [

        {
            "month": bill.month,
            "year": bill.year,
            "expected": round(
                bill.expected,
                2
            ),
            "actual": round(
                bill.actual,
                2
            )
        }

        for bill in monthly_bills

    ]

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "hourly": hourly,

        "daily": daily,

        "weekly": weekly,

        "monthly": monthly_energy,

        "billing": billing

    }


# ============================================================
# ALERTS
# ============================================================

@app.get("/alerts/{user}")
def alerts(
    user: str,
    db: Session = Depends(get_db)
):

    if user not in users:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if not db_user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {

        "msg":
            get_alert(
                users[user],
                db,
                db_user.id
            )

    }


# ============================================================
# PLAN
# ============================================================

@app.get("/plan/{user}")
def plan(user: str):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    return {

        "plan":
            users[user]["plans"]

    }


# ============================================================
# PREDICTION
# ============================================================

@app.get("/predict/{user}")
def prediction(user: str):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    result = (
        predict_grid_demand()
    )

    return {

        "user":
            user,

        **result

    }

# ============================================================
# HOUSEHOLD AI-ASSISTED FORECAST
# ============================================================

def forecast_household_consumption(
    u,
    db,
    user_id
):

    # --------------------------------------------------------
    # Load persistent hourly consumption history
    # --------------------------------------------------------

    records = (
        db.query(EnergyRecord)
        .filter(
            EnergyRecord.user_id == user_id
        )
        .order_by(
            EnergyRecord.id.desc()
        )
        .limit(24)
        .all()
    )

    records = list(
        reversed(records)
    )

    history = [
        round(
            float(record.energy_kwh),
            4
        )
        for record in records
        if float(record.energy_kwh) >= 0
    ]

    # --------------------------------------------------------
    # No historical data
    # --------------------------------------------------------

    if not history:

        current_power = calc_power(u)

        next_hour = (
            current_power / 1000
        )

        return {

            "next_hour_kwh":
                round(
                    next_hour,
                    3
                ),

            "next_6_hours_kwh":
                round(
                    next_hour * 6,
                    3
                ),

            "projected_daily_kwh":
                round(
                    next_hour * 24,
                    3
                ),
            "projected_monthly_kwh":
                round(
                    next_hour * 24 * 30,
                    2
                ),
            "projected_monthly_bill":
                round(
                    calc_bill(
                        next_hour * 24 * 30
                        ),
                    2
                ),

            "history_hours":
                0,

            "current_power_w":
                current_power,

            "current_hour":
                u.get(
                    "hour",
                    0
                ),

            "method":
                "Current-load baseline"

        }

    # --------------------------------------------------------
    # Recent household consumption
    # --------------------------------------------------------

    recent = history[-6:]

    weights = list(
        range(
            1,
            len(recent) + 1
        )
    )

    weighted_sum = sum(
        value * weight
        for value, weight
        in zip(
            recent,
            weights
        )
    )

    weight_total = sum(
        weights
    )

    weighted_average = (
        weighted_sum /
        weight_total
    )

    # --------------------------------------------------------
    # Current appliance load
    # --------------------------------------------------------

    current_power = calc_power(u)

    current_load = (
        current_power / 1000
    )

    # --------------------------------------------------------
    # Load-aware forecast
    # --------------------------------------------------------

    next_hour = (
        0.7 * weighted_average
        +
        0.3 * current_load
    )

    # --------------------------------------------------------
    # Next six simulated hours
    # --------------------------------------------------------
    # --------------------------------------------------------
    # Next six simulated hours
    # --------------------------------------------------------

    next_six_hours = (
        next_hour * 6
    )

    # --------------------------------------------------------
    # Current simulated hour
    # --------------------------------------------------------

    current_hour = int(
        u.get(
            "hour",
            0
        )
    )

    # --------------------------------------------------------
    # Identify the current simulated day
    # --------------------------------------------------------

    current_day = int(
        u.get(
            "day",
            0
        )
    )

    # --------------------------------------------------------
    # Calculate actual consumption for the current
    # simulated day using persistent EnergyRecord data
    # --------------------------------------------------------

    today_records = [
        record
        for record in records
        if record.hour <= current_hour
    ]

    consumed_today = sum(
        float(record.energy_kwh)
        for record in today_records
    )

    # --------------------------------------------------------
    # Predicted remaining consumption
    # --------------------------------------------------------

    remaining_hours = max(
        0,
        24 - current_hour
    )

    predicted_remaining = (
        next_hour *
        remaining_hours
    )

    # --------------------------------------------------------
    # Projected total consumption for today
    # --------------------------------------------------------

    projected_daily = (
        consumed_today
        +
        predicted_remaining
    )

    # --------------------------------------------------------
    # Projected electricity bill
    # --------------------------------------------------------

    projected_monthly_kwh = (
        projected_daily * 30
    )

    projected_monthly_bill = calc_bill(
    
        projected_monthly_kwh
    )

    return {

        "next_hour_kwh":
            round(
                next_hour,
                3
            ),

        "next_6_hours_kwh":
            round(
                next_six_hours,
                3
            ),

        "projected_daily_kwh":
            round(
                projected_daily,
                3
            ),

        "consumed_today_kwh":
            round(
                consumed_today,
                3
            ),

        "remaining_today_kwh":
            round(
                predicted_remaining,
                3
            ),

        "projected_monthly_kwh":
            round(
                projected_monthly_kwh,
                2
            ),

        "projected_monthly_bill":
            round(
                projected_monthly_bill,
                2
            ),

        "history_hours":
            len(history),

        "current_power_w":
            current_power,

        "current_hour":
            current_hour,

        "method":
            "Load-aware weighted forecast"

    }

@app.get(
    "/household-forecast/{user}"
)
def household_forecast(
    user: str,
    db: Session = Depends(get_db)
):

    if user not in users:

        raise HTTPException(
            status_code=404,
            detail="User not logged in"
        )

    u = users[user]

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {

        "user":
            user,

        **forecast_household_consumption(
            u,
            db,
            db_user.id
        )
    }



# ============================================================
# BLOCKCHAIN
# ============================================================

@app.get("/blockchain/{user}")
def blockchain(
    user: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Validate user
    # --------------------------------------------------------

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if db_user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------------------------
    # Load blockchain from SQLite
    # --------------------------------------------------------

    records = (
        db.query(BlockchainBlock)
        .filter(
            BlockchainBlock.user_id == db_user.id
        )
        .order_by(
            BlockchainBlock.block_number.asc()
        )
        .all()
    )

    chain = []

    # The first block must point to "0".
    expected_previous_hash = "0"

    # Once a block is corrupted, every subsequent block
    # is considered part of a compromised chain.
    chain_compromised = False

    # --------------------------------------------------------
    # Validate every block
    # --------------------------------------------------------

    for block in records:

        # ----------------------------------------------------
        # Reproduce EXACTLY the data used by add_block()
        # ----------------------------------------------------

        date = block.date.date()

        energy = round(
            float(block.energy_kwh),
            2
        )

        bill = round(
            float(block.bill),
            2
        )

        previous_hash = block.previous_hash

        calculated_hash = calculate_block_hash(
            block_number=block.block_number,
            date=date,
            energy=energy,
            bill=bill,
            previous_hash=previous_hash
        )

        # ----------------------------------------------------
        # Check this block's own cryptographic integrity
        # ----------------------------------------------------

        hash_valid = (
            calculated_hash ==
            block.current_hash
        )

        # ----------------------------------------------------
        # Check connection to previous block
        # ----------------------------------------------------

        linkage_valid = (
            block.previous_hash ==
            expected_previous_hash
        )

        # ----------------------------------------------------
        # Determine block validity
        # ----------------------------------------------------

        if (
            not hash_valid
            or
            not linkage_valid
        ):

            chain_compromised = True

        block_valid = (
            not chain_compromised
        )

        # ----------------------------------------------------
        # Add block to API response
        # ----------------------------------------------------

        chain.append({

            "day":
                block.block_number,

            "date":
                block.date.strftime(
                    "%Y-%m-%d"
                ),

            "energy":
                round(
                    block.energy_kwh,
                    2
                ),

            "bill":
                round(
                    block.bill,
                    2
                ),

            "prev_hash":
                block.previous_hash,

            "hash":
                block.current_hash,

            "calculated_hash":
                calculated_hash,

            "hash_valid":
                hash_valid,

            "linkage_valid":
                linkage_valid,

            "valid":
                block_valid

        })

        # ----------------------------------------------------
        # Current stored hash becomes expected hash for the
        # next block.
        # ----------------------------------------------------

        expected_previous_hash = (
            block.current_hash
        )

    return chain


# ============================================================
# SUMMARY
# ============================================================

@app.get("/summary/{user}")
def summary(
    user: str,
    db: Session = Depends(get_db)
):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    # --------------------------------------------------------
    # Find persistent database user
    # --------------------------------------------------------

    db_user = (
        db.query(User)
        .filter(
            User.username == user
        )
        .first()
    )

    if db_user is None:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    # --------------------------------------------------------
    # Read monthly bills directly from SQLite
    # --------------------------------------------------------

    monthly_bills = (
        db.query(MonthlyBill)
        .filter(
            MonthlyBill.user_id == db_user.id
        )
        .order_by(
            MonthlyBill.year,
            MonthlyBill.month
        )
        .all()
    )

    return [

        {
            "month":
                bill.month,

            "year":
                bill.year,

            "expected":
                float(
                    bill.expected
                ),

            "actual":
                float(
                    bill.actual
                )

        }

        for bill in monthly_bills

    ]


# ============================================================
# BUDGET
# ============================================================

@app.post("/budget/{user}/{amount}")
def budget(

    user: str,

    amount: int,

    db: Session = Depends(get_db)

):

    if user not in users:

        raise HTTPException(

            status_code=404,

            detail="User not found"

        )

    if amount <= 0:

        raise HTTPException(

            status_code=400,

            detail=(
                "Budget must be "
                "greater than 0"
            )

        )

    # --------------------------------------------------------
    # Runtime
    # --------------------------------------------------------

    users[user]["monthly_budget"] = (
        amount
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    db_user = (

        db.query(User)

        .filter(
            User.username == user
        )

        .first()

    )

    if db_user is not None:

        db_user.monthly_budget = (
            amount
        )

        db.commit()

    return {
        "msg": "updated"
    }





# ============================================================
# FRONTEND
# ============================================================

@app.get("/")
def serve_frontend():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True
    ),
    name="frontend"
)

