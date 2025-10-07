import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator")

# --- Employee Input ---
st.subheader("Employee List")
default_employees = [
    "Ramesh Polisetty","Ajay Chidipotu","Srinivasu Cheedalla","Imran Khan",
    "Sammeta Balachander","Muppa Divya","Anil Athkuri","Gangavarapu Suneetha",
    "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan","Lakshmi Narayana Rao"
]
employees = st.text_area("Enter employee names (comma separated):", value=", ".join(default_employees))
employees = [e.strip() for e in employees.split(",")]
num_employees = len(employees)

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1,13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

# --- Working Days & Week-Offs ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
weekoff_per_emp = st.number_input("Number of week-off days per employee:", min_value=0, max_value=num_days-working_days_per_emp, value=2)

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days:", options=list(range(1, num_days+1)))

# --- Leaves / Special Codes ---
st.subheader("Add Employee Leaves or Special Codes")
leave_data = {}
for emp in employees:
    leave_days = st.multiselect(f"{emp} Leaves/Special Codes (L/H/CO):", options=list(range(1, num_days+1)))
    leave_data[emp] = leave_days

# --- Weekends ---
def get_weekends(year, month):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) >= 5]

weekends = get_weekends(year, month)

# --- Assign Off Days ---
def assign_off_days(num_days, working_days, weekoff):
    total_off = num_days - working_days
    off_days_positions = []
    if total_off > 0:
        interval = max(1, num_days // total_off)
        off_days_positions = [i for i in range(interval-1, num_days, interval)][:total_off]
    return off_days_positions

# --- Assign Structured Shifts ---
def assign_shifts(employees, num_days, working_days, weekoff, weekends, festivals):
    roster_dict = {emp: ['']*num_days for emp in employees}
    emp_off_days = {emp: assign_off_days(num_days, working_days, weekoff) for emp in employees}

    # Assign 5N -> 5F -> S rotation with small rotation for fairness
    day_pointer = 0
    for emp in employees:
        pattern = ['N']*5 + ['F']*5
        s_days = num_days - len(pattern)
        pattern += ['S']*s_days
        pattern = pattern[day_pointer:] + pattern[:day_pointer]
        roster_dict[emp] = pattern
        day_pointer = (day_pointer + 2) % num_days

    # Adjust weekends and festivals for minimum coverage
    for day in range(1, num_days+1):
        if day in weekends or day in festival_days:
            f_count, n_count = 3, 2
        else:
            f_count, n_count = 2, 2
        available_emps = [emp for emp in employees if day-1 not in emp_off_days[emp]]
        if len(available_emps) < f_count + n_count:
            available_emps = employees.copy()  # allow off employees to work
        np.random.shuffle(available_emps)
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

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekoff_per_emp, weekends, festival_days)

# --- Apply Leaves/Special Codes ---
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

st.subheader("Generated 24/7 Roster")
st.dataframe(roster.style.applymap(color_shifts))

# --- Download CSV ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "automated_24_7_roster.csv", "text/csv")
