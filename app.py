import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (5-day blocks)")

# --- Default Employees and Shift Limits ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", 5, 5, 10, "IIS"],
    ["Paneerselvam F", 5, 5, 10, "IIS"],
    ["Rajesh Jayapalan", 5, 5, 10, "IIS"],
    ["Ajay Chidipotu", 5, 5, 10, "Websphere"],
    ["Imran Khan", 5, 15, 0, "Websphere"],
    ["Sammeta Balachander", 5, 5, 10, "Websphere"],
    ["Ramesh Polisetty", 0, 20, 0, ""],
    ["Muppa Divya", 0, 20, 0, ""],
    ["Anil Athkuri", 0, 20, 0, ""],
    ["D Namithananda", 0, 20, 0, ""],
    ["Srinivasu Cheedalla", 0, 20, 0, ""],
    ["Gangavarapu Suneetha", 0, 20, 0, ""],
    ["Lakshmi Narayana Rao", 0, 20, 0, ""],
    ["Pousali C", 0, 20, 0, ""],
    ["Thorat Yashwant", 0, 20, 0, ""],
    ["Srivastav Nitin", 0, 20, 0, ""],
    ["Kishore Khati Vaibhav", 0, 20, 0, ""],
    ["Rupan Venkatesan Anandha", 0, 20, 0, ""],
    ["Chaudhari Kaustubh", 0, 20, 0, ""],
    ["Shejal Gawade", 0, 20, 0, ""],
    ["Vivek Kushwaha", 0, 20, 0, ""],
    ["Abdul Mukthiyar Basha", 0, 20, 0, ""],
    ["M Naveen", 0, 20, 0, ""],
    ["B Madhurusha", 0, 20, 0, ""],
    ["Chinthalapudi Yaswanth", 0, 20, 0, ""],
    ["Edagotti Kalpana", 0, 20, 0, ""]
], columns=["Name", "F_max", "S_max", "N_max", "Skill"])

employees = employee_data["Name"].tolist()

# --- Nightshift Exempt ---
nightshift_exempt = st.multiselect("Nightshift-Exempt Employees", employees, default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Imran Khan"])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
# Default Tuesday-Wednesday for most employees
default_tue_wed = [
    "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan", "Ajay Chidipotu",
    "Imran Khan", "Sammeta Balachander", "Ramesh Polisetty", "Muppa Divya", "Anil Athkuri",
    "D Namithananda", "Srinivasu Cheedalla", "Gangavarapu Suneetha"
]
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=[])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=[])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=[])
tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday Off", employees, default=default_tue_wed)
thursday_friday_off = st.multiselect("Thursday-Friday Off", employees, default=[])
wednesday_thursday_off = st.multiselect("Wednesday-Thursday Off", employees, default=["Lakshmi Narayana Rao"])
monday_tuesday_off = st.multiselect("Monday-Tuesday Off", employees, default=["Abdul Mukthiyar Basha", "B Madhurusha", "Chinthalapudi Yaswanth", "Edagotti Kalpana"])

# --- Validate Overlaps ---
groups = [friday_saturday_off, sunday_monday_off, saturday_sunday_off, 
          tuesday_wednesday_off, thursday_friday_off, wednesday_thursday_off, monday_tuesday_off]
names = ["Fri-Sat", "Sun-Mon", "Sat-Sun", "Tue-Wed", "Thu-Fri", "Wed-Thu", "Mon-Tue"]
for i in range(len(groups)):
    for j in range(i + 1, len(groups)):
        overlap = set(groups[i]) & set(groups[j])
        if overlap:
            st.error(f"Employees in both {names[i]} & {names[j]}: {', '.join(overlap)}")
            st.stop()

# --- Month & Year ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Month", list(range(1, 13)), index=10, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days + 1)]

# --- Festival Days ---
festival_days = st.multiselect("Festival Days", list(range(1, num_days + 1)), default=[])

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in weekday_indices]

# Calculate weekdays for week-off preferences
fridays_saturdays = get_weekdays(year, month, [4, 5])
sundays_mondays = get_weekdays(year, month, [6, 0])
saturdays_sundays = get_weekdays(year, month, [5, 6])
tuesday_wednesday = get_weekdays(year, month, [1, 2])
thursday_friday = get_weekdays(year, month, [3, 4])
wednesday_thursday = get_weekdays(year, month, [2, 3])
monday_tuesday = get_weekdays(year, month, [0, 1])

# --- Off Days Assignment ---
def assign_off_days(emp_name, num_days):
    off_days = []
    if emp_name in friday_saturday_off: off_days += fridays_saturdays
    if emp_name in sunday_monday_off: off_days += sundays_mondays
    if emp_name in saturday_sunday_off: off_days += saturdays_sundays
    if emp_name in tuesday_wednesday_off: off_days += tuesday_wednesday
    if emp_name in thursday_friday_off: off_days += thursday_friday
    if emp_name in wednesday_thursday_off: off_days += wednesday_thursday
    if emp_name in monday_tuesday_off: off_days += monday_tuesday
    return set([d - 1 for d in off_days if d <= num_days])

# --- Generate Roster ---
def generate_roster():
    np.random.seed(42)
    roster = {emp: [''] * num_days for emp in employees}
    shift_counts = {emp: {'F': 0, 'S': 0, 'N': 0} for emp in employees}
    
    # Assign Offs
    for emp in employees:
        off_idx = assign_off_days(emp, num_days)
        for idx in off_idx:
            roster[emp][idx] = 'O'

    festival_set = set(festival_days)
    
    # Define shift rotation for Gopalakrishnan, Paneerselvam, and Rajesh
    special_employees = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
    shift_cycle = ['F', 'S', 'N']
    rotation_length = 5
    
    # Assign shifts for special employees
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_set:
            for emp in employees:
                roster[emp][day] = 'H'
            continue
        
        # Assign shifts for special employees
        cycle_index = (day // rotation_length) % 3
        shifts = [shift_cycle[cycle_index], shift_cycle[(cycle_index + 1) % 3], shift_cycle[(cycle_index + 2) % 3]]
        
        for i, emp in enumerate(special_employees):
            if roster[emp][day] == 'O':
                continue
            proposed_shift = shifts[i]
            if emp in nightshift_exempt and proposed_shift == 'N':
                continue
            if shift_counts[emp][proposed_shift] < employee_data.loc[employee_data['Name'] == emp, f"{proposed_shift}_max"].values[0]:
                roster[emp][day] = proposed_shift
                shift_counts[emp][proposed_shift] += 1
        
        # Assign shifts for remaining employees
        weekday_name = weekday(year, month, day_num)
        is_weekend = weekday_name >= 5
        
        # Define required shifts
        if is_weekend:
            F_req, S_req, N_req = 3, 3, 2
        else:
            F_req, S_req, N_req = 5, 5, 2
        
        # Count already assigned shifts
        assigned_shifts = {'F': 0, 'S': 0, 'N': 0}
        for emp in employees:
            if roster[emp][day] in assigned_shifts:
                assigned_shifts[roster[emp][day]] += 1
        
        # Adjust required shifts
        F_req -= assigned_shifts['F']
        S_req -= assigned_shifts['S']
        N_req -= assigned_shifts['N']
        
        available = [e for e in employees if roster[e][day] == '']
        
        # Check if enough employees are available
        if len(available) < (F_req + S_req + N_req):
            st.warning(f"Insufficient employees available on day {day_num} to meet shift requirements. Needed: {F_req}F, {S_req}S, {N_req}N. Available: {len(available)}")
        
        # Assign Night shifts (prioritize Ajay Chidipotu, Sammeta Balachander)
        n_candidates = [e for e in available if e not in nightshift_exempt]
        n_candidates = [e for e in n_candidates if shift_counts[e]['N'] < employee_data.loc[employee_data['Name'] == e, 'N_max'].values[0]]
        n_candidates.sort(key=lambda x: (x in ['Ajay Chidipotu', 'Sammeta Balachander'], employee_data.loc[employee_data['Name'] == x, 'N_max'].values[0]), reverse=True)
        n_assigned = 0
        for emp in n_candidates:
            if n_assigned >= N_req: break
            if day >= 3 and all(roster[emp][day - 3 + p] == 'N' for p in range(3)): continue
            roster[emp][day] = 'N'
            shift_counts[emp]['N'] += 1
            n_assigned += 1
            available.remove(emp)
        
        # Assign First Shift (prioritize Imran Khan, Sammeta Balachander, Ramesh Polisetty, etc.)
        f_candidates = [e for e in available if shift_counts[e]['F'] < employee_data.loc[employee_data['Name'] == e, 'F_max'].values[0]]
        f_candidates.sort(key=lambda x: (x in ['Imran Khan', 'Sammeta Balachander', 'Ramesh Polisetty', 'Muppa Divya', 'Srivastav Nitin', 'Kishore Khati Vaibhav', 'Rupan Venkatesan Anandha'], employee_data.loc[employee_data['Name'] == x, 'F_max'].values[0]), reverse=True)
        f_assigned = 0
        for emp in f_candidates:
            if f_assigned >= F_req: break
            roster[emp][day] = 'F'
            shift_counts[emp]['F'] += 1
            f_assigned += 1
            available.remove(emp)
        
        # Assign Second Shift (prioritize Anil Athkuri, D Namithananda, Srinivasu Cheedalla, etc.)
        s_candidates = [e for e in available if shift_counts[e]['S'] < employee_data.loc[employee_data['Name'] == e, 'S_max'].values[0]]
        s_candidates.sort(key=lambda x: (x in ['Anil Athkuri', 'D Namithananda', 'Srinivasu Cheedalla', 'Gangavarapu Suneetha', 'Chaudhari Kaustubh', 'Shejal Gawade', 'Vivek Kushwaha', 'M Naveen'], employee_data.loc[employee_data['Name'] == x, 'S_max'].values[0]), reverse=True)
        for emp in s_candidates:
            if S_req <= 0: break
            roster[emp][day] = 'S'
            shift_counts[emp]['S'] += 1
            S_req -= 1
    
    # Check shift limit violations
    for emp in employees:
        for shift in ['F', 'S', 'N']:
            max_shift = employee_data.loc[employee_data['Name'] == emp, f"{shift}_max"].values[0]
            if shift_counts[emp][shift] > max_shift:
                st.warning(f"Shift limit exceeded for {emp}: {shift} assigned {shift_counts[emp][shift]} times, limit is {max_shift}")
    
    return roster

# --- Generate & Display ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors = {'F': 'green', 'S': 'lightgreen', 'N': 'lightblue', 'O': 'lightgray', 'H': 'orange'}
    return f'background-color: {colors.get(val, "")}'
st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({
    s: [sum(1 for v in roster_dict[e] if v == s) for e in employees]
    for s in ['F', 'S', 'N', 'O', 'H']
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
