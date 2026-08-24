import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = PROJECT_ROOT / "data" / "opsd_germany_daily.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "forecast_model.pkl"


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("Loading dataset...")

data = pd.read_csv(CSV_PATH)

print(f"Dataset loaded: {len(data)} rows")


# ============================================================
# 2. PREPROCESS DATA
# ============================================================

# The actual CSV uses "Date", not "Timestamp"
data["Date"] = pd.to_datetime(data["Date"])


# Consumption is our prediction target
data["Demand_MW"] = data["Consumption"]


# Create time-based features
data["DayOfWeek"] = data["Date"].dt.dayofweek
data["Month"] = data["Date"].dt.month


# Remove rows where the target is missing
data = data.dropna(subset=["Demand_MW"]).reset_index(drop=True)


print(f"Usable rows: {len(data)}")

print(
    f"Date range: "
    f"{data['Date'].min().date()} "
    f"to "
    f"{data['Date'].max().date()}"
)


# ============================================================
# 3. FEATURES AND TARGET
# ============================================================

# Features used by the baseline forecasting model
X = data[["DayOfWeek", "Month"]]

# Target
y = data["Demand_MW"]


print()
print("Features:")
print(X.columns.tolist())

print("Target:")
print("Demand_MW")


# ============================================================
# 4. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


print()
print(f"Total samples   : {len(data)}")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples : {len(X_test)}")


# ============================================================
# 5. TRAIN LINEAR REGRESSION MODEL
# ============================================================

print()
print("Training Linear Regression model...")

model = LinearRegression()

model.fit(X_train, y_train)


# ============================================================
# 6. EVALUATE MODEL
# ============================================================

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)


print()
print("Model Evaluation")
print("-----------------")
print(f"Mean Absolute Error: {mae:.2f} MW")


# ============================================================
# 7. MODEL PARAMETERS
# ============================================================

print()
print("Model Parameters")
print("-----------------")
print(f"Intercept: {model.intercept_:.4f}")

for feature, coefficient in zip(X.columns, model.coef_):
    print(f"{feature}: {coefficient:.4f}")


# ============================================================
# 8. SAVE TRAINED MODEL
# ============================================================

joblib.dump(model, MODEL_PATH)

print()
print("Model saved successfully!")
print(f"Path: {MODEL_PATH}")


# ============================================================
# 9. TEST THE SAVED MODEL
# ============================================================

print()
print("Testing saved model...")
print("----------------------")

loaded_model = joblib.load(MODEL_PATH)


# Example prediction:
# DayOfWeek = 0 → Monday
# Month = 8 → August

example_input = pd.DataFrame({
    "DayOfWeek": [0],
    "Month": [8]
})

example_prediction = loaded_model.predict(example_input)[0]


print("Example input:")
print("  DayOfWeek = 0 (Monday)")
print("  Month     = 8 (August)")

print()
print(f"Predicted demand: {example_prediction:.2f} MW")


# ============================================================
# 10. FINISHED
# ============================================================

print()
print("==============================================")
print("Forecasting model training completed!")
print("==============================================")