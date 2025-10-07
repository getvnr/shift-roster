import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange

# --- Employee List ---
employees = [
    "Alice","Bob","Charlie","David","Eve","Frank",
    "Grace","Heidi","Ivan","Judy","Mallory","Niaj"
]

st.title("12-Person Shift Roster")

# --- Month & Year Selection ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1,13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))

# Number of days in month
num_days = monthrange(year, month)[1]

# --- Leave Input ---
st.subheader("Add Leaves")
leave_data = {}
for emp in employees:
    leave_days = st.multiselect(f"Leave days for {emp}:", options=list(range(1, num_days+1)))
    leave_data[emp] = leave_days

# --- Initialize Roster ---
roster = pd.DataFrame(index=employees, columns=[f"{day}-{month}-{year}" for day in range(1, num_days+1)])

# --- Shift Pattern ---
shifts = ['F', 'S', 'N']  # First, Second, Night shifts
off_days = ['O']

# --- Generate Roster ---
for i, emp in enumerate(employees):
    day_counter = 0
    while day_counter < num_days:
        # Assign 5 days of each shift
        for shift in shifts:
            for _ in range(5):
                if day_counter < num_days:
                    day_label = f"{day_counter+1}-{month}-{year}"
                    roster.loc[emp, day_label] = shift
                    day_counter += 1
        # Assign 2 days off
        for _ in range(2):
            if day_counter < num_days:
                day_label = f"{day_counter+1}-{month}-{year}"
                roster.loc[emp, day_label] = 'O'
                day_counter += 1
    # Apply leaves
    for leave_day in leave_data[emp]:
        day_label = f"{leave_day}-{month}-{year}"
        roster.loc[emp, day_label] = 'L'

st.subheader("Generated Roster")
st.dataframe(roster)

# --- Download Option ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "roster.csv", "text/csv")
