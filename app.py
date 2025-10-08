import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Weekly blocks)")

# --- Default Employees and Shift Limits ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", 5, 5, 10, "IIS"],
    ["Paneerselvam F", 5, 5, 10, "IIS"],
    ["Rajesh Jayapalan", 5, 5, 10, "IIS"],
    ["Ajay Chidipotu", 20, 20, 10, "Websphere"],
    ["Imran Khan", 20, 20, 0, "Websphere"],
    ["Sammeta Balachander", 20, 20, 10, "Websphere"],
    ["Ramesh Polisetty", 20, 20, 0, ""],
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

# --- Fixed Roster for Non-Special Employees ---
fixed_roster = {
    "Muppa Divya": ['O','O','F','F','F','F','F','O','O','F','F','F','F','F','O','O','F','F','F','F','F','O','O','F','F','F','F','F','O','O'],
    "Anil Athkuri": ['O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O'],
    "D Namithananda": ['O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O'],
    "Srinivasu Cheedalla": ['O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O'],
    "Gangavarapu Suneetha": ['O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O'],
    "Lakshmi Narayana Rao": ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'],
    "Pousali C": ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'],
    "Thorat Yashwant": ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'] + ['N','N'] + ['']*3 + ['O','O'],
    "Srivastav Nitin": ['F','F'] + ['']*5 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'],
    "Kishore Khati Vaibhav": ['F','F'] + ['']*5 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'],
    "Rupan Venkatesan Anandha": ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'] + ['F','F'] + ['']*3 + ['O','O'],
    "Chaudhari Kaustubh": ['S','S'] + ['']*3 + ['O','O'] + ['S','S'] + ['']*3 + ['O','O'] + ['S','S'] + ['']*3 + ['O','O'] + ['S','S'] + ['']*3 + ['O','O'],
    "Shejal Gawade": ['S','S','O','O'] + ['']*3 + ['S','S','O','O'] + ['']*3 + ['S','S','O','O'] + ['']*3 + ['S','S','O','O'] + ['']*3 + ['S','S'],
    "Vivek Kushwaha": ['O','S'] + ['']*5 + ['O','O','S'] + ['']*4 + ['O','O','S'] + ['']*4 + ['O','O','S'] + ['']*4 + ['O','O','S'],
    "Abdul Mukthiyar Basha": ['O'] + ['']*6 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*1,
    "M Naveen": ['S','O','O'] + ['']*4 + ['S','O','O'] + ['']*4 + ['S','O','O'] + ['']*4 + ['S','O','O'] + ['']*4 + ['S','O'],
    "B Madhurusha": ['']*2 + ['O','O'] + ['']*3 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O'],
    "Chinthalapudi Yaswanth": ['']*2 + ['O','O'] + ['']*3 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O'],
    "Edagotti Kalpana": ['O'] + ['']*6 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*5 + ['O','O'] + ['']*1
}

# --- Nightshift Exempt ---
nightshift_exempt = st.multiselect("Nightshift-Exempt Employees", employees, default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Imran Khan"])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
default_tue_wed = [
    "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan", "Ajay Chidipotu",
    "Imran Khan", "Sammeta Balachander", "Ramesh Polisetty", "Muppa Divya", "Anil Athkuri",
    "D Namithananda", "Srinivasu Cheedalla", "Gangavarapu Suneetha"
]
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=[])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=[])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=["Shejal Gawade"])
tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday Off", employees, default=default_tue_wed)
thursday_friday_off = st.multiselect("Thursday-Friday Off", employees, default=[])
wednesday_thursday_off = st.multiselect("Wednesday-Thursday Off", employees, default=["Lakshmi Narayana Rao", "Pousali C", "Thorat Yashwant", "Srivastav Nitin", "Kishore Khati Vaibhav", "Rupan Venkatesan Anandha", "Chaudhari Kaustubh"])
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
    
    # Assign provided roster for Ajay, Imran, Sammeta
    provided_roster = {
        "Ajay Chidipotu": ['O','O','N','N','N','N','N','O','O','F','F','F','F','F','O','O','S','S','S','S','S','O','O','N','N','N','N','N','O','O'],
        "Imran Khan": ['O','O','S','S','S','S','S','O','O','S','S','S','S','S','O','O','F','F','F','F','F','O','O','S','S','S','S','S','O','O'],
        "Sammeta Balachander": ['O','O','F','F','F','F','F','O','O','N','N','N','N','N','O','O','N','N','N','N','N','O','O','S','S','S','S','S','O','O']
    }
    
    special_employees_2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
    for emp in special_employees_2:
        for day in range(num_days):
            if day < len(provided_roster[emp]) and provided_roster[emp][day] in ['F', 'S', 'N', 'O']:
                roster[emp][day] = provided_roster[emp][day]
                if roster[emp][day] in ['F', 'S', 'N']:
                    shift_counts[emp][roster[emp][day]] += 1

    # Assign fixed roster for other non-special employees
    special_employees_1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
    for emp in employees:
        if emp not in special_employees_1 and emp not in special_employees_2:
            for day in range(num_days):
                if emp in fixed_roster and day < len(fixed_roster[emp]) and fixed_roster[emp][day] in ['F', 'S', 'N', 'O']:
                    roster[emp][day] = fixed_roster[emp][day]
                    if roster[emp][day] in ['F', 'S', 'N']:
                        shift_counts[emp][roster[emp][day]] += 1

    # Override with festival days
    festival_set = set(festival_days)
    for day in range(num_days):
        if day + 1 in festival_set:
            for emp in employees:
                roster[emp][day] = 'H'
                if emp in shift_counts and roster[emp][day] in ['F', 'S', 'N']:
                    shift_counts[emp][roster[emp][day]] -= 1

    # Assign shifts for Group 1 (Gopalakrishnan, Paneerselvam, Rajesh) - 5-day opposite shifts
    shift_cycle_1 = ['F', 'S', 'N']
    rotation_length_1 = 5
    
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_set:
            continue
        
        off_idx = assign_off_days(special_employees_1[0], num_days)
        if day in off_idx:
            for emp in special_employees_1:
                roster[emp][day] = 'O'
            continue
        
        cycle_index = (day // rotation_length_1) % 3
        shifts = [shift_cycle_1[cycle_index], shift_cycle_1[(cycle_index + 1) % 3], shift_cycle_1[(cycle_index + 2) % 3]]
        
        for i, emp in enumerate(special_employees_1):
            if roster[emp][day] == 'O':
                continue
            proposed_shift = shifts[i]
            if emp in nightshift_exempt and proposed_shift == 'N':
                continue
            if shift_counts[emp][proposed_shift] < employee_data.loc[employee_data['Name'] == emp, f"{proposed_shift}_max"].values[0]:
                roster[emp][day] = proposed_shift
                shift_counts[emp][proposed_shift] += 1

    # Verify shift requirements
    for day in range(num_days):
        day_num = day + 1
        weekday_name = weekday(year, month, day_num)
        is_weekend = weekday_name >= 5
        F_req, S_req, N_req = (3, 3, 2) if is_weekend else (5, 5, 2)
        
        assigned_shifts = {'F': 0, 'S': 0, 'N': 0}
        for emp in employees:
            if roster[emp][day] in assigned_shifts:
                assigned_shifts[roster[emp][day]] += 1
        
        if assigned_shifts['F'] < F_req or assigned_shifts['S'] < S_req or assigned_shifts['N'] < N_req:
            st.warning(f"Day {day_num}: Shift requirements not met. Assigned: {assigned_shifts['F']}F, {assigned_shifts['S']}S, {assigned_shifts['N']}N. Required: {F_req}F, {S_req}S, {N_req}N")
    
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
    colors = {'F': 'green', 'S': 'lightgreen', 'N': 'lightblue', 'O': 'lightgray', 'H': 'orange', '': 'white'}
    return f'background-color: {colors.get(val, "")}'
st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({
    s: [sum(1 for v in roster_dict[e] if v == s) for e in employees]
    for s in ['F', 'S', 'N', 'O', 'H', '']
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
