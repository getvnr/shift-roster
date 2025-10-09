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
    ["Rajesh Jayapalan", 5, 5, 5, "IIS"],
    ["Ajay Chidipotu", 5, 5, 10, "Websphere"],
    ["Imran Khan", 5, 15, 0, "Websphere"],
    ["Sammeta Balachander", 5, 5, 10, "Websphere"],
    ["Ramesh Polisetty", 20, 0, 0, ""],  # Always General shift
    ["Muppa Divya", 0, 20, 0, ""],  # Always Second shift
    ["Anil Athkuri", 0, 20, 0, ""],  # Always Second shift
    ["D Namithananda", 0, 20, 0, ""],  # Always Second shift
    ["Srinivasu Cheedalla", 0, 0, 20, ""],  # Always Evening shift
    ["Gangavarapu Suneetha", 20, 0, 0, ""],  # Always General shift
    ["Lakshmi Narayana Rao", 20, 0, 0, ""],  # Always General shift
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
], columns=["Name", "G_max", "S_max", "E_max", "Skill"])

employees = employee_data["Name"].tolist()

# --- Evening Shift Exempt ---
evening_shift_exempt = st.multiselect("Evening Shift-Exempt Employees", employees, default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Imran Khan"])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=["Muppa Divya", "Anil Athkuri", "D Namithananda"])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=["Gangavarapu Suneetha", "Lakshmi Narayana Rao"])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=["Pousali C", "Thorat Yashwant"])
tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday Off", employees, default=["Srivastav Nitin", "Kishore Khati Vaibhav"])
thursday_friday_off = st.multiselect("Thursday-Friday Off", employees, default=["Rupan Venkatesan Anandha", "Chaudhari Kaustubh"])
wednesday_thursday_off = st.multiselect("Wednesday-Thursday Off", employees, default=["Shejal Gawade", "Vivek Kushwaha"])
monday_tuesday_off = st.multiselect("Monday-Tuesday Off", employees, default=["Abdul Mukthiyar Basha", "M Naveen"])

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

# Calculate weekdays for week-off preferences and weekend counts
fridays_saturdays = get_weekdays(year, month, [4, 5])  # Friday=4, Saturday=5
sundays_mondays = get_weekdays(year, month, [6, 0])    # Sunday=6, Monday=0
saturdays_sundays = get_weekdays(year, month, [5, 6])  # Saturday=5, Sunday=6
tuesday_wednesday = get_weekdays(year, month, [1, 2])  # Tuesday=1, Wednesday=2
thursday_friday = get_weekdays(year, month, [3, 4])    # Thursday=3, Friday=4
wednesday_thursday = get_weekdays(year, month, [2, 3]) # Wednesday=2, Thursday=3
monday_tuesday = get_weekdays(year, month, [0, 1])     # Monday=0, Tuesday=1

# Calculate Saturdays and Sundays
saturdays = get_weekdays(year, month, [5])
sundays = get_weekdays(year, month, [6])
num_saturdays = len(saturdays)
num_sundays = len(sundays)
num_weekends = num_saturdays + num_sundays
num_working_days = num_days - num_weekends - len(festival_days)

# Display weekend and working days information
st.subheader("Month Summary")
st.write(f"Number of Saturdays: {num_saturdays}")
st.write(f"Number of Sundays: {num_sundays}")
st.write(f"Total Working Days (excluding weekends and festivals): {num_working_days}")

# --- Off Days Assignment ---
def assign_off_days(emp_name, num_days):
    off_days = []
    # Override week-off preferences for employees with no-weekend requirement
    no_weekend_employees = [
        "Ramesh Polisetty", "Muppa Divya", "Anil Athkuri", "D Namithananda",
        "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao",
        "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan",
        "Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"
    ]
    if emp_name in no_weekend_employees:
        off_days += saturdays_sundays
    else:
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
    
    # Assign Offs
    for emp in employees:
        off_idx = assign_off_days(emp, num_days)
        for idx in off_idx:
            roster[emp][idx] = 'O'

    festival_set = set(festival_days)
    
    # Define groups
    group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
    group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
    fixed_shift_employees = {
        "Ramesh Polisetty": 'G',
        "Muppa Divya": 'S',
        "Anil Athkuri": 'S',
        "D Namithananda": 'S',
        "Srinivasu Cheedalla": 'E',
        "Gangavarapu Suneetha": 'G',
        "Lakshmi Narayana Rao": 'G'
    }
    
    # Hardcode provided roster for Group 1 and Group 2 (01-11-2025 to 28-11-2025)
    provided_roster = {
        "Gopalakrishnan Selvaraj": ['O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E'],
        "Paneerselvam F": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'E', 'E', 'E', 'E', 'E'],
        "Rajesh Jayapalan": ['O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S'],
        "Ajay Chidipotu": ['O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E'],
        "Imran Khan": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S'],
        "Sammeta Balachander": ['O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'S', 'S', 'S', 'S', 'S']
    }
    
    # Apply provided roster for Group 1 and Group 2
    for emp in group1 + group2:
        for day in range(28):
            roster[emp][day] = provided_roster[emp][day]
    
    # Assign weekend days (29-30 Nov) as Off for Group 1, Group 2, and fixed-shift employees
    for day in range(28, num_days):
        if (day + 1) in saturdays_sundays:
            for emp in group1 + group2 + list(fixed_shift_employees.keys()):
                roster[emp][day] = 'O'
    
    # Assign fixed shifts for specified employees on working days
    working_days = [d for d in range(num_days) if (d + 1) not in saturdays_sundays and (d + 1) not in festival_set]
    for emp, shift in fixed_shift_employees.items():
        for day in working_days:
            if roster[emp][day] == 'O':  # Respect week-offs
                continue
            if emp in evening_shift_exempt and shift == 'E':
                continue
            max_shifts = employee_data.loc[employee_data['Name'] == emp, ['G_max', 'S_max', 'E_max']].iloc[0]
            roster[emp][day] = shift
    
    # Track shift counts
    shift_counts = {emp: {'G': 0, 'S': 0, 'E': 0} for emp in employees}
    for emp in employees:
        for day in range(num_days):
            shift = roster[emp][day]
            if shift in ['G', 'S', 'E']:
                shift_counts[emp][shift] += 1
    
    # Assign shifts for remaining employees
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_set:
            for emp in employees:
                roster[emp][day] = 'H'
            continue
        
        weekday_name = weekday(year, month, day_num)
        is_weekend = weekday_name >= 5
        
        # Define required shifts
        if is_weekend:
            G_req, S_req, E_req = 3, 3, 2
        else:
            G_req, S_req, E_req = 5, 5, 2
        
        # Count already assigned shifts
        assigned_shifts = {'G': 0, 'S': 0, 'E': 0}
        for emp in employees:
            if roster[emp][day] in assigned_shifts:
                assigned_shifts[roster[emp][day]] += 1
        
        G_req -= assigned_shifts['G']
        S_req -= assigned_shifts['S']
        E_req -= assigned_shifts['E']
        
        available = [e for e in employees if roster[e][day] == '' and e not in group1 + group2 + list(fixed_shift_employees.keys())]
        
        # Assign Evening shifts
        e_candidates = [e for e in available if e not in evening_shift_exempt]
        e_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'E_max'].values[0], reverse=True)
        e_assigned = 0
        for emp in e_candidates:
            if e_assigned >= E_req: break
            if day >= 5 and all(roster[emp][day - 5 + p] == 'E' for p in range(5)): continue
            if shift_counts[emp]['E'] < employee_data.loc[employee_data['Name'] == emp, 'E_max'].iloc[0]:
                roster[emp][day] = 'E'
                shift_counts[emp]['E'] += 1
                e_assigned += 1
                available.remove(emp)
        
        # Assign General Shift
        g_candidates = available.copy()
        g_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'G_max'].values[0], reverse=True)
        g_assigned = 0
        for emp in g_candidates:
            if g_assigned >= G_req: break
            if shift_counts[emp]['G'] < employee_data.loc[employee_data['Name'] == emp, 'G_max'].iloc[0]:
                roster[emp][day] = 'G'
                shift_counts[emp]['G'] += 1
                g_assigned += 1
                available.remove(emp)
        
        # Assign Second Shift to remaining
        for emp in available:
            if S_req > 0 and shift_counts[emp]['S'] < employee_data.loc[employee_data['Name'] == emp, 'S_max'].iloc[0]:
                roster[emp][day] = 'S'
                shift_counts[emp]['S'] += 1
                S_req -= 1
    
    return roster

# --- Generate & Display ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors = {'G': 'green', 'S': 'lightgreen', 'E': 'lightblue', 'O': 'lightgray', 'H': 'orange'}
    return f'background-color: {colors.get(val, "")}'
st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({
    s: [sum(1 for v in roster_dict[e] if v == s) for e in employees]
    for s in ['G', 'S', 'E', 'O', 'H']
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
