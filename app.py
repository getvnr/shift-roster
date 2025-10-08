import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from git import Repo

st.title("Automatic Employee Roster")

# Load employee data
employees = pd.read_csv("employees.csv")

days = 30  # Number of days to schedule
shifts = ['F', 'S', 'N', 'E']  # Available shifts
roster = pd.DataFrame('', index=employees['Name'], columns=[f'Day{i+1}' for i in range(days)])

# Track night shifts
night_count = {name:0 for name in employees['Name']}

# Function to check weekend
def is_weekend(day):
    weekday = day % 7
    return weekday in [5,6]  # Saturday=5, Sunday=6

# Generate roster
for day in range(days):
    for idx, emp in employees.iterrows():
        allowed_shifts = list(emp['ShiftsAllowed'].split(','))
        
        # Weekend off
        if emp['WeekendOff'] == 'Yes' and is_weekend(day):
            roster.iloc[idx, day] = 'O'
            continue
        
        # Night shift limit
        if 'N' in allowed_shifts and night_count[emp['Name']] >= emp['MaxNightShifts']:
            allowed_shifts.remove('N')
        
        # Assign shift
        if allowed_shifts:
            shift = np.random.choice(allowed_shifts)
            roster.iloc[idx, day] = shift
            if shift == 'N':
                night_count[emp['Name']] += 1
        else:
            roster.iloc[idx, day] = 'O'

st.subheader("Generated Roster")
st.dataframe(roster)

# Save to CSV
if st.button("Save Roster Locally"):
    filename = f"Roster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    roster.to_csv(filename)
    st.success(f"Roster saved as {filename}")

# Save to GitHub
if st.button("Push Roster to GitHub"):
    try:
        repo = Repo(".")  # Assuming your Streamlit app is in a git repo
        roster.to_csv("roster.csv", index=True)
        repo.git.add("roster.csv")
        repo.git.commit("-m", f"Update roster {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        repo.git.push()
        st.success("Roster pushed to GitHub successfully!")
    except Exception as e:
        st.error(f"Git push failed: {e}")
