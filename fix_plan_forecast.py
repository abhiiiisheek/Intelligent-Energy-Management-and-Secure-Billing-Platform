from pathlib import Path

path = Path("backend/main.py")
lines = path.read_text(encoding="utf-8").splitlines()

# Find the generate_plan forecast variable
for i, line in enumerate(lines):
    if line.strip() == "projected_daily_bill = float(":
        start_var = i
        break
else:
    raise SystemExit("ERROR: projected_daily_bill variable not found.")

# Rename the variable only
lines[start_var] = lines[start_var].replace(
    "projected_daily_bill",
    "projected_monthly_bill"
)

# Find the forecast status comment AFTER the variable
for i in range(start_var, len(lines)):
    if lines[i].strip() == "# Forecast status":
        comment_index = i
        break
else:
    raise SystemExit("ERROR: Forecast status section not found.")

# The section ends at the Next-hour expected consumption line.
for i in range(comment_index, len(lines)):
    if "Next-hour expected consumption:" in lines[i]:
        next_hour_index = i
        break
else:
    raise SystemExit("ERROR: End of forecast status section not found.")

# Preserve the separator immediately before the forecast section.
new_block = [
    "    # --------------------------------------------------------",
    "    # Forecast status",
    "    # --------------------------------------------------------",
    "",
    "    if projected_monthly_bill > monthly_budget:",
    "",
    "        bill_excess = (",
    "            projected_monthly_bill -",
    "            monthly_budget",
    "        )",
    "",
    "        lines.append(",
    "            f\"FORECAST WARNING: \"",
    "            f\"Projected monthly consumption is \"",
    "            f\"{forecast.get('projected_monthly_kwh', 0):.2f} kWh, \"",
    "            f\"with an estimated monthly bill of \"",
    "            f\"₹{projected_monthly_bill:.2f}. \"",
    "            f\"This is ₹{bill_excess:.2f} above \"",
    "            f\"the monthly budget.\"",
    "        )",
    "",
    "    else:",
    "",
    "        bill_remaining = (",
    "            monthly_budget -",
    "            projected_monthly_bill",
    "        )",
    "",
    "        lines.append(",
    "            f\"FORECAST: \"",
    "            f\"Projected monthly consumption is \"",
    "            f\"{forecast.get('projected_monthly_kwh', 0):.2f} kWh \"",
    "            f\"with an estimated monthly bill of \"",
    "            f\"₹{projected_monthly_bill:.2f}. \"",
    "            f\"₹{bill_remaining:.2f} remains \"",
    "            f\"within the monthly budget.\"",
    "        )",
    "",
]

# Replace everything from the forecast comment through the line
# immediately before Next-hour expected consumption.
lines[comment_index:next_hour_index] = new_block

path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("SUCCESS: Forecast status corrected to monthly billing.")
