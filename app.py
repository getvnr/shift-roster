import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Dynamic 24/7 Shift Roster with Working Days, Weekends, and Festivals")

# --- Employee List ---
employees = [
    "Alice","Bob","Charlie","David","Eve","Frank",
    "Grace","Heidi","Ivan","Judy","Mallory","Niaj"
]
num_employees = len(employees)

# --- Month & Year Selection ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1,13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]

# --- Input: Working Days per Employee ---
working_days = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
off_days_per_employee = num_days - working_days

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days:", options=list(range(1, num_days+1)))

# --- Leaves Input ---
st.subheader("Add Employee Leaves")
leave_data = {}
for emp in employees:
    leave_days = st.multiselect(f"Leaves for {emp}:", options=list(range(1, num_days+1)))
    leave_data[emp] = leave_days

# --- Initialize Roster ---
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]
roster = pd.DataFrame(index=employees, columns=dates)

# --- Function to get weekends ---
def get_weekends(year, month):
    weekends = []
    for day in range(1, monthrange(year, month)[1]+1):
        if weekday(year, month, day) >= 5:  # Saturday=5, Sunday=6
            weekends.append(day)
    return weekends

weekends = get_weekends(year, month)

# --- Assign Off Days to Meet Working Days Requirement ---
def assign_off_days(num_days, working_days):
    total_off_days = num_days - working_days
    off_days_positions = []
    if total_off_days > 0:
        interval = num_days // total_off_days
        off_days_positions = [i for i in range(interval-1, num_days, interval)][:total_off_days]
    return off_days_positions

# --- Shift Assignment Function ---
def assign_shifts(employees, num_days, working_days, weekends, festivals):
    roster_dict = {emp: ['']*num_days for emp in employees}

    # Pre-calculate off days per employee
    emp_off_days = {emp: assign_off_days(num_days, working_days) for emp in employees}

    for day in range(1, num_days+1):
        # Determine coverage for day
        if day in weekends or day in festivals:
            f_count, n_count = 3, 2
        else:
            f_count, n_count = 2, 2
        s_count = num_employees - f_count - n_count

        # Available employees (not off today)
        available_emps = [emp for emp in employees if day-1 not in emp_off_days[emp]]

        if len(available_emps) < f_count + n_count:
            # If not enough employees, allow off employees to work to meet coverage
            available_emps = employees.copy()

        # Shuffle for fairness
        np.random.shuffle(available_emps)

        # Assign shifts
        f_emps = available_emps[:f_count]
        n_emps = available_emps[f_count:f_count+n_count]
        s_emps = [e for e in employees if e not in f_emps + n_emps]

        for emp in employees:
            if day-1 in emp_off_days[emp]:
                roster_dict[emp][day-1] = 'O'
            elif emp in f_emps:
                roster_dict[emp][day-1] = 'F'
            elif emp in n_emps:
                roster_dict[emp][day-1] = 'N'
            else:
                roster_dict[emp][day-1] = 'S'

    return roster_dict

# Generate roster
roster_dict = assign_shifts(employees, num_days, working_days, weekends, festival_days)

# Apply leaves
for emp in employees:
    for leave_day in leave_data[emp]:
        roster_dict[emp][leave_day-1] = 'L'

# Convert to DataFrame
roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    if val == 'F':
        color = 'green'
    elif val == 'N':
        color = 'blue'
    elif val == 'S':
        color = 'lightgreen'
    elif val == 'O':
        color = 'red'
    elif val == 'L':
        color = 'yellow'
    else:
        color = ''
    return f'background-color: {color}'

st.subheader("Generated 24/7 Shift Roster")
st.dataframe(roster.style.applymap(color_shifts))

# --- Download CSV ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "24_7_shift_roster.csv", "text/csv")
