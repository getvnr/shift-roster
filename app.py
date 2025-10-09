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
    ["Rajesh Jayapalan", 5, 5, 5, "IIS"],  # One employee with 5 fewer night shifts
    ["Ajay Chidipotu", 5, 5, 10, "Websphere"],
    ["Imran Khan", 5, 15, 0, "Websphere"],  # Updated for 5F, 15S, 0N
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
    
    # Hardcode provided roster for 01-11-2025 to 28-11-2025
    provided_roster = {
        "Gopalakrishnan Selvaraj": ['O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'N', 'N', 'N', 'N'],
        "Paneerselvam F": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'N', 'N', 'N', 'N', 'N'],
        "Rajesh Jayapalan": ['O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S'],
        "Ajay Chidipotu": ['O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'N', 'N', 'N', 'N'],
        "Imran Khan": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S'],
        "Sammeta Balachander": ['O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'F', 'F', 'F', 'F', 'F', 'O', 'O', 'S', 'S', 'S', 'S', 'S']
    }
    
    # Apply provided roster
    for emp in group1 + group2:
        for day in range(28):
            roster[emp][day] = provided_roster[emp][day]
    
    # Assign weekend days (29-30 Nov) as Off
    for day in range(28, num_days):
        if (day + 1) in saturdays_sundays:
            for emp in group1 + group2:
                roster[emp][day] = 'O'
    
    # Track shift counts to enforce quotas
    shift_counts = {emp: {'F': 0, 'S': 0, 'N': 0} for emp in employees}
    for emp in employees:
        for day in range(num_days):
            shift = roster[emp][day]
            if shift in ['F', 'S', 'N']:
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
        
        # Assign Off for group1 and group2 on weekends
        if is_weekend:
            for emp in group1 + group2:
                if roster[emp][day] == '':
                    roster[emp][day] = 'O'
            continue
        
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
        
        F_req -= assigned_shifts['F']
        S_req -= assigned_shifts['S']
        N_req -= assigned_shifts['N']
        
        available = [e for e in employees if roster[e][day] == '' and e not in group1 + group2]
        
        # Assign Night shifts
        n_candidates = [e for e in available if e not in nightshift_exempt]
        n_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'N_max'].values[0], reverse=True)
        n_assigned = 0
        for emp in n_candidates:
            if n_assigned >= N_req: break
            if day >= 5 and all(roster[emp][day - 5 + p] == 'N' for p in range(5)): continue
            if shift_counts[emp]['N'] < employee_data.loc[employee_data['Name'] == emp, 'N_max'].iloc[0]:
                roster[emp][day] = 'N'
                shift_counts[emp]['N'] += 1
                n_assigned += 1
                available.remove(emp)
        
        # Assign First Shift
        f_candidates = available.copy()
        f_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'F_max'].values[0], reverse=True)
        f_assigned = 0
        for emp in f_candidates:
            if f_assigned >= F_req: break
            if shift_counts[emp]['F'] < employee_data.loc[employee_data['Name'] == emp, 'F_max'].iloc[0]:
                roster[emp][day] = 'F'
                shift_counts[emp]['F'] += 1
                f_assigned += 1
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
