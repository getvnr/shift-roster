import streamlit as st
import pandas as pd
from calendar import monthrange

st.title("Dynamic 24/7 Shift Roster")

# --- Employee List ---
employees = [
    "Alice","Bob","Charlie","David","Eve","Frank",
    "Grace","Heidi","Ivan","Judy","Mallory","Niaj"
]

# --- Inputs ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1,13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]

working_days = st.number_input("Number of working days per person:", min_value=1, max_value=num_days, value=21)
off_days_per_person = num_days - working_days

# --- Leave Input ---
st.subheader("Add Leaves")
leave_data = {}
for emp in employees:
    leave_days = st.multiselect(f"Leave days for {emp}:", options=list(range(1, num_days+1)))
    leave_data[emp] = leave_days

# --- Initialize Roster ---
roster = pd.DataFrame(index=employees, columns=[f"{day}-{month}-{year}" for day in range(1, num_days+1)])

# --- Shift Assignment Logic ---
def generate_roster(employees, num_days, working_days):
    roster_dict = {emp: ['O']*num_days for emp in employees}
    day_counter = 0

    while day_counter < num_days:
        # Assign F & N shifts first (at least 2 people each)
        f_emps = employees[day_counter % len(employees): (day_counter % len(employees)) + 2]
        n_emps = employees[(day_counter + 2) % len(employees): (day_counter + 4) % len(employees)]
        for i, emp in enumerate(employees):
            if emp in f_emps:
                roster_dict[emp][day_counter] = 'F'
            elif emp in n_emps:
                roster_dict[emp][day_counter] = 'N'
            else:
                roster_dict[emp][day_counter] = 'S'
        day_counter += 1

    return roster_dict

# Generate roster
roster_dict = generate_roster(employees.copy(), num_days, working_days)

# Apply leaves
for emp in employees:
    for leave_day in leave_data[emp]:
        if leave_day <= num_days:
            roster_dict[emp][leave_day-1] = 'L'

# Convert to DataFrame
roster = pd.DataFrame(roster_dict, index=[f"{day}-{month}-{year}" for day in range(1, num_days+1)]).T

st.subheader("Generated 24/7 Roster")
st.dataframe(roster)

# --- Download Option ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "24_7_dynamic_roster.csv", "text/csv")
