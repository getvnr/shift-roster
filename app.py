import streamlit as st
import pandas as pd
from calendar import monthrange

# --- Employee List ---
employees = [
    "Alice","Bob","Charlie","David","Eve","Frank",
    "Grace","Heidi","Ivan","Judy","Mallory","Niaj"
]

st.title("12-Person Shift Roster with Controlled Shifts")

# --- Month & Year Selection ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1,13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]

# --- Leave Input ---
st.subheader("Add Leaves")
leave_data = {}
for emp in employees:
    leave_days = st.multiselect(f"Leave days for {emp}:", options=list(range(1, num_days+1)))
    leave_data[emp] = leave_days

# --- Initialize Roster ---
roster = pd.DataFrame(index=employees, columns=[f"{day}-{month}-{year}" for day in range(1, num_days+1)])

# --- Shift Assignment Logic ---
def assign_shifts(employees, num_days):
    roster_dict = {emp: [] for emp in employees}
    total_emps = len(employees)
    idx = 0  # Employee index tracker

    day = 0
    while day < num_days:
        # Assign 5-day shifts
        for i in range(5):
            if day >= num_days:
                break
            # First shift (F) → at least 2 people
            f_emps = employees[idx:idx+2]
            # Night shift (N) → next 2 people
            n_emps = employees[idx+2:idx+4]
            # Second shift (S) → rest
            s_emps = [e for e in employees if e not in f_emps + n_emps]
            
            for emp in employees:
                if emp in f_emps:
                    roster_dict[emp].append('F')
                elif emp in n_emps:
                    roster_dict[emp].append('N')
                else:
                    roster_dict[emp].append('S')
            day += 1
        
        # 2 days off
        for _ in range(2):
            if day >= num_days:
                break
            for emp in employees:
                roster_dict[emp].append('O')
            day += 1
        
        # Rotate employees to ensure fairness
        employees = employees[2:] + employees[:2]  # rotate 2 employees
    return roster_dict

# Generate roster
roster_dict = assign_shifts(employees.copy(), num_days)

# Apply leaves
for emp in employees:
    for leave_day in leave_data[emp]:
        if leave_day <= num_days:
            roster_dict[emp][leave_day-1] = 'L'

# Convert to DataFrame
roster = pd.DataFrame(roster_dict, index=[f"{day}-{month}-{year}" for day in range(1, num_days+1)]).T

st.subheader("Generated Roster")
st.dataframe(roster)

# --- Download Option ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "roster.csv", "text/csv")
