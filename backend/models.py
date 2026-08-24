from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey
)

from datetime import datetime

from .database import Base


# ============================================================
# USER
# ============================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    household_size = Column(
        Integer,
        nullable=True
    )

    monthly_budget = Column(
        Float,
        default=3000
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# ============================================================
# APPLIANCE
# ============================================================

class Appliance(Base):

    __tablename__ = "appliances"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    name = Column(
        String,
        nullable=False
    )

    power = Column(
        Float,
        nullable=False
    )

    count = Column(
        Integer,
        nullable=False
    )

    status = Column(
        Boolean,
        default=False
    )

    usage_hours = Column(
        Float,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

# ============================================================
# SIMULATION STATE
# ============================================================

class SimulationState(Base):

    __tablename__ = "simulation_states"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    current_hour = Column(
        Integer,
        default=0,
        nullable=False
    )

    current_day = Column(
        Integer,
        default=0,
        nullable=False
    )

    current_energy_kwh = Column(
        Float,
        default=0,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.now
    )


# ============================================================
# ENERGY RECORD
# ============================================================

class EnergyRecord(Base):

    __tablename__ = "energy_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    date = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        index=True
    )

    hour = Column(
        Integer,
        nullable=False
    )

    power_watts = Column(
        Float,
        nullable=False
    )

    energy_kwh = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# ============================================================
# DAILY ENERGY RECORD
# ============================================================

class DailyRecord(Base):

    __tablename__ = "daily_records"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    date = Column(
        DateTime,
        nullable=False,
        index=True
    )

    energy_kwh = Column(
        Float,
        nullable=False
    )

    bill = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# ============================================================
# BLOCKCHAIN BLOCK
# ============================================================

class BlockchainBlock(Base):

    __tablename__ = "blockchain_blocks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    block_number = Column(
        Integer,
        nullable=False
    )

    date = Column(
        DateTime,
        nullable=False
    )

    energy_kwh = Column(
        Float,
        nullable=False
    )

    bill = Column(
        Float,
        nullable=False
    )

    previous_hash = Column(
        String,
        nullable=False
    )

    current_hash = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# ============================================================
# MONTHLY BILL
# ============================================================

class MonthlyBill(Base):

    __tablename__ = "monthly_bills"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    month = Column(
        Integer,
        nullable=False
    )

    year = Column(
        Integer,
        nullable=False
    )

    expected = Column(
        Float,
        nullable=False
    )

    actual = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )