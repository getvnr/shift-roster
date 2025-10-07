import streamlit as st
import pandas as pd
from calendar import monthrange

st.title("24/7 Shift Roster with Holidays Every 5 Days")

# --- Employee List ---
employees = [
    "Alice","Bob","Charlie","David","Eve","Frank",
    "Grace","Heidi","Ivan","Judy","Mallory","Niaj"
]

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
def generate_24_7_roster(employees, num_days):
    roster_dict = {emp: [] for emp in employees}
    emp_count = len(employees)
    day = 0
    rotation_index = 0

    while day < num_days:
        # --- 5 working days ---
        for i in range(5):
            if day >= num_days:
                break
            # Rotate employees to assign F/N/S while ensuring coverage
            f_emps = employees[rotation_index:rotation_index+2]
            n_emps = employees[(rotation_index+2) % emp_count:(rotation_index+4) % emp_count]
            # Handle wrap-around
            if len(f_emps) < 2:
                f_emps += employees[:2-len(f_emps)]
            if len(n_emps) < 2:
                n_emps += employees[:2-len(n_emps)]
            s_emps = [e for e in employees if e not in f_emps + n_emps]

            for emp in employees:
                if emp in f_emps:
                    roster_dict[emp].append('F')
                elif emp in n_emps:
                    roster_dict[emp].append('N')
                else:
                    roster_dict[emp].append('S')
            day += 1
            rotation_index = (rotation_index + 2) % emp_count

        # --- 2 days off (O) ---
        for _ in range(2):
            if day >= num_days:
                break
            for emp in employees:
                roster_dict[emp].append('O')
            day += 1

    return roster_dict

# Generate roster
roster_dict = generate_24_7_roster(employees.copy(), num_days)

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
st.download_button("Download CSV", csv, "24_7_roster.csv", "text/csv")
