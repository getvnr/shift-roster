import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator")

# --- Employee Input ---
st.subheader("Employee List")
default_employees = [
    "Ramesh Polisetty", "Ajay Chidipotu", "Srinivasu Cheedalla", "Imran Khan",
    "Sammeta Balachander", "Muppa Divya", "Anil Athkuri", "Gangavarapu Suneetha",
    "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan", "Lakshmi Narayana Rao"
]
employees = st.text_area("Enter employee names (comma separated):", value=", ".join(default_employees))
employees = [e.strip() for e in employees.split(",") if e.strip()]
if not employees:
    st.error("Please provide at least one employee name.")
    st.stop()
num_employees = len(employees)

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

# --- Working Days & Week-Offs ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
weekoff_per_emp = st.number_input("Number of week-off days per employee:", min_value=0, max_value=num_days-working_days_per_emp, value=2)
if working_days_per_emp + weekoff_per_emp > num_days:
    st.error("Working days plus week-off days cannot exceed the number of days in the month.")
    st.stop()

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days:", options=list(range(1, num_days+1)))

# --- Leaves / Special Codes ---
st.subheader("Add Employee Leaves or Special Codes")
leave_data = {}
for emp in employees:
    st.write(f"{emp} Leaves/Special Codes")
    cols = st.columns(3)
    with cols[0]:
        leave_days = st.multiselect(f"Leave Days for {emp}:", options=list(range(1, num_days+1)), key=f"leave_{emp}")
    with cols[1]:
        codes = st.multiselect(f"Code for each day:", options=['L', 'H', 'CO'], key=f"code_{emp}")
    leave_data[emp] = dict(zip(leave_days, codes[:len(leave_days)]))

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
def assign_shifts(employees, num_days, working_days, weekoff, weekends, festival_days):
    np.random.seed(42)  # For reproducibility
    roster_dict = {emp: ['S']*num_days for emp in employees}
    emp_off_days = {emp: assign_off_days(num_days, working_days, weekoff) for emp in employees}
    
    for day in range(num_days):
        is_special_day = day+1 in weekends or day+1 in festival_days
        f_count, n_count = (3, 2) if is_special_day else (2, 2)
        
        available_emps = [emp for emp in employees if day not in emp_off_days[emp] and roster_dict[emp][day] != 'L']
        if len(available_emps) < f_count + n_count:
            st.warning(f"Insufficient employees for day {day+1}. Adjusting assignments.")
            available_emps = [emp for emp in employees if roster_dict[emp][day] != 'L']
        
        np.random.shuffle(available_emps)
        for i, emp in enumerate(available_emps[:f_count]):
            roster_dict[emp][day] = 'F'
        for i, emp in enumerate(available_emps[f_count:f_count+n_count]):
            roster_dict[emp][day] = 'N'
        
        for emp in employees:
            if day in emp_off_days[emp]:
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekoff_per_emp, weekends, festival_days)

# --- Apply Leaves/Special Codes ---
for emp in employees:
    for day, code in leave_data[emp].items():
        roster_dict[emp][day-1] = code

# Convert to DataFrame
roster = pd.DataFrame(roster_dict, index=dates).T

# --- Check Minimum Coverage ---
for day in range(num_days):
    f_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    n_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    min_f, min_n = (3, 2) if (day+1 in weekends or day+1 in festival_days) else (2, 2)
    if f_assigned < min_f or n_assigned < min_n:
        st.warning(f"Day {day+1} has insufficient coverage: {f_assigned}F, {n_assigned}N (required {min_f}F, {min_n}N).")

# --- Color Coding ---
def color_shifts(val):
    colors = {'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple'}
    return f'background-color: {colors.get(val, "")}'

# --- Display Roster ---
st.subheader("Generated 24/7 Roster")
st.dataframe(roster.style.applymap(color_shifts))

# --- Shift Summary ---
st.subheader("Shift Summary per Employee")
summary = pd.DataFrame({
    'F': [sum(1 for shift in roster_dict[emp] if shift == 'F') for emp in employees],
    'N': [sum(1 for shift in roster_dict[emp] if shift == 'N') for emp in employees],
    'S': [sum(1 for shift in roster_dict[emp] if shift == 'S') for emp in employees],
    'O': [sum(1 for shift in roster_dict[emp] if shift == 'O') for emp in employees],
    'L': [sum(1 for shift in roster_dict[emp] if shift == 'L') for emp in employees],
    'H': [sum(1 for shift in roster_dict[emp] if shift == 'H') for emp in employees],
    'CO': [sum(1 for shift in roster_dict[emp] if shift == 'CO') for emp in employees],
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "automated_24_7_roster.csv", "text/csv")
