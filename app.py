import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from git import Repo

st.title("Automatic Employee Roster")

# ---------------------------
# Step 1: Load employee data
# ---------------------------
try:
    employees = pd.read_csv("employees.csv", encoding='utf-8-sig')  # Handles BOM
except UnicodeDecodeError:
    employees = pd.read_csv("employees.csv", encoding='latin1')

# Clean column names (remove spaces and special characters)
employees.columns = employees.columns.str.strip()

# Display columns for debugging
st.write("Detected columns:", employees.columns.tolist())

# Check if 'Name' column exists
if 'Name' not in employees.columns:
    st.error("CSV must have a 'Name' column")
    st.stop()

# ---------------------------
# Step 2: Initialize roster
# ---------------------------
days = 30  # Number of days to schedule
shifts = ['F', 'S', 'N', 'E']  # Possible shifts
roster = pd.DataFrame('', index=employees['Name'], columns=[f'Day{i+1}' for i in range(days)])

# Track night shifts per employee
night_count = {name:0 for name in employees['Name']}

# ---------------------------
# Step 3: Helper functions
# ---------------------------
def is_weekend(day):
    """Return True if the day index corresponds to Saturday(5) or Sunday(6)"""
    weekday = day % 7
    return weekday in [5,6]

def allowed_shift(emp, day):
    """Return list of allowed shifts for employee on a day considering night limit & weekend off"""
    shifts_allowed = list(str(emp['ShiftsAllowed']).split(','))
    
    # Weekend off
    if str(emp['WeekendOff']).strip().lower() == 'yes' and is_weekend(day):
        return ['O']
    
    # Night shift limit
    if 'N' in shifts_allowed and night_count[emp['Name']] >= int(emp['MaxNightShifts']):
        shifts_allowed.remove('N')
    
    if not shifts_allowed:
        return ['O']  # No shifts possible
    return shifts_allowed

# ---------------------------
# Step 4: Generate roster
# ---------------------------
for day in range(days):
    for idx, emp in employees.iterrows():
        shifts_today = allowed_shift(emp, day)
        # Randomly assign one of allowed shifts
        assigned_shift = np.random.choice(shifts_today)
        roster.iloc[idx, day] = assigned_shift
        if assigned_shift == 'N':
            night_count[emp['Name']] += 1

# ---------------------------
# Step 5: Display roster
# ---------------------------
st.subheader("Generated Roster")
st.dataframe(roster)

# ---------------------------
# Step 6: Save roster locally
# ---------------------------
if st.button("Save Roster Locally"):
    filename = f"Roster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    roster.to_csv(filename)
    st.success(f"Roster saved as {filename}")

# ---------------------------
# Step 7: Push roster to GitHub
# ---------------------------
if st.button("Push Roster to GitHub"):
    try:
        repo = Repo(".")  # Streamlit app must be inside a git repo
        roster.to_csv("roster.csv", index=True)
        repo.git.add("roster.csv")
        repo.git.commit("-m", f"Update roster {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        repo.git.push()
        st.success("Roster pushed to GitHub successfully!")
    except Exception as e:
        st.error(f"Git push failed: {e}")
