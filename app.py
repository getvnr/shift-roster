import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Continuous Shifts)")

# --- Default Employees and Shift Limits ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", 10, 10, 10, 10, 5, "IIS"],
    ["Paneerselvam F", 10, 10, 10, 10, 5, "IIS"],
    ["Rajesh Jayapalan", 10, 15, 5, 10, 5, "IIS"],
    ["Ajay Chidipotu", 10, 10, 10, 10, 5, "Websphere"],
    ["Imran Khan", 10, 25, 0, 10, 5, "Websphere"],
    ["Sammeta Balachander", 10, 10, 10, 10, 5, "Websphere"],
    ["Ramesh Polisetty", 25, 0, 0, 0, 0, ""],  # Always General shift
    ["Muppa Divya", 0, 25, 0, 0, 0, ""],  # Always Second shift
    ["Anil Athkuri", 0, 25, 0, 0, 0, ""],  # Always Second shift
    ["D Namithananda", 0, 25, 0, 0, 0, ""],  # Always Second shift
    ["Srinivasu Cheedalla", 0, 0, 0, 0, 25, ""],  # Always Evening shift
    ["Gangavarapu Suneetha", 25, 0, 0, 0, 0, ""],  # Always General shift
    ["Lakshmi Narayana Rao", 25, 0, 0, 0, 0, ""],  # Always General shift
    ["Pousali C", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Thorat Yashwant", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Srivastav Nitin", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Kishore Khati Vaibhav", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Rupan Venkatesan Anandha", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Chaudhari Kaustubh", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Shejal Gawade", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Vivek Kushwaha", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Abdul Mukthiyar Basha", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["M Naveen", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["B Madhurusha", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Chinthalapudi Yaswanth", 10, 10, 5, 0, 0, ""],  # Max 5 Night shifts
    ["Edagotti Kalpana", 10, 10, 5, 0, 0, ""]  # Max 5 Night shifts
], columns=["Name", "G_max", "S_max", "N_max", "M_max", "E_max", "Skill"])

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
month = st.selectbox("Month", list(range(1, 13)), index=11, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
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
    
    # Assign Offs and Holidays
    festival_set = set([d - 1 for d in festival_days])
    for emp in employees:
        off_idx = assign_off_days(emp, num_days)
        for idx in off_idx:
            roster[emp][idx] = 'O'
        for idx in festival_set:
            roster[emp][idx] = 'H'

    # Define shift patterns for employees with rotating shifts
    rotating_shift_employees = {
        "Gopalakrishnan Selvaraj": ['M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N'],
        "Paneerselvam F": ['M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N'],
        "Rajesh Jayapalan": ['M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'N', 'N', 'N', 'N', 'N'],
        "Ajay Chidipotu": ['M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N'],
        "Imran Khan": ['S', 'S', 'S', 'S', 'S', 'M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'],
        "Sammeta Balachander": ['M', 'M', 'M', 'M', 'M', 'S', 'S', 'S', 'S', 'S', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'N']
    }
    
    # Define fixed shift employees
    fixed_shift_employees = {
        "Ramesh Polisetty": 'G',
        "Muppa Divya": 'S',
        "Anil Athkuri": 'S',
        "D Namithananda": 'S',
        "Srinivasu Cheedalla": 'E',
        "Gangavarapu Suneetha": 'G',
        "Lakshmi Narayana Rao": 'G'
    }
    
    # Track shift counts to enforce maximums
    shift_counts = {emp: {'G': 0, 'S': 0, 'N': 0, 'M': 0, 'E': 0} for emp in employees}
    
    # Track global working day index for rotating employees to ensure shift continuity
    working_day_index = {emp: 0 for emp in rotating_shift_employees}
    
    # Apply shifts for listed employees based on pattern
    listed_employees = list(rotating_shift_employees.keys()) + list(fixed_shift_employees.keys())
    for emp in listed_employees:
        pattern = rotating_shift_employees.get(emp, [fixed_shift_employees.get(emp)])
        pattern_length = len(pattern)
        for day in range(num_days):
            if day in assign_off_days(emp, num_days) or day in festival_set:
                continue  # Skip offs and holidays
            # For fixed shift employees, use the single shift
            if emp in fixed_shift_employees:
                shift = pattern[0]
            else:
                # For rotating employees, use working_day_index
                shift = pattern[working_day_index[emp] % pattern_length]
                working_day_index[emp] += 1
            if shift_counts[emp][shift] < employee_data.loc[employee_data['Name'] == emp, f"{shift}_max"].iloc[0]:
                roster[emp][day] = shift
                shift_counts[emp][shift] += 1
            else:
                # Fallback to an alternative shift if max is reached
                for alt_shift in ['G', 'S', 'N', 'M', 'E']:
                    if alt_shift != shift and shift_counts[emp][alt_shift] < employee_data.loc[employee_data['Name'] == emp, f"{alt_shift}_max"].iloc[0]:
                        roster[emp][day] = alt_shift
                        shift_counts[emp][alt_shift] += 1
                        break
    
    # Assign shifts for remaining employees and any unassigned days
    for day in range(num_days):
        if day in festival_set:
            continue  # Already assigned 'H'
        
        weekday_name = weekday(year, month, day + 1)
        is_weekend = weekday_name >= 5
        
        # Define required shifts
        if is_weekend:
            G_req, S_req, N_req, M_req, E_req = 3, 3, 2, 0, 0
        else:
            G_req, S_req, N_req, M_req, E_req = 5, 5, 2, 0, 0
        
        # Count already assigned shifts
        assigned_shifts = {'G': 0, 'S': 0, 'N': 0, 'M': 0, 'E': 0}
        for emp in employees:
            if roster[emp][day] in assigned_shifts:
                assigned_shifts[roster[emp][day]] += 1
        
        G_req -= assigned_shifts['G']
        S_req -= assigned_shifts['S']
        N_req -= assigned_shifts['N']
        M_req -= assigned_shifts['M']
        E_req -= assigned_shifts['E']
        
        available = [e for e in employees if roster[e][day] == '']
        
        # Assign Night shifts (max 5 per employee)
        n_candidates = [e for e in available if e not in nightshift_exempt and shift_counts[e]['N'] < employee_data.loc[employee_data['Name'] == e, 'N_max'].iloc[0]]
        n_candidates.sort(key=lambda x: shift_counts[x]['N'])  # Prioritize employees with fewer night shifts
        n_assigned = 0
        for emp in n_candidates:
            if n_assigned >= N_req: break
            if day >= 5 and all(roster[emp][day - 5 + p] == 'N' for p in range(5)): continue
            roster[emp][day] = 'N'
            shift_counts[emp]['N'] += 1
            n_assigned += 1
            available.remove(emp)
        
        # Assign General Shift
        g_candidates = [e for e in available if shift_counts[e]['G'] < employee_data.loc[employee_data['Name'] == e, 'G_max'].iloc[0]]
        g_candidates.sort(key=lambda x: shift_counts[x]['G'])
        g_assigned = 0
        for emp in g_candidates:
            if g_assigned >= G_req: break
            roster[emp][day] = 'G'
            shift_counts[emp]['G'] += 1
            g_assigned += 1
            available.remove(emp)
        
        # Assign Second Shift to remaining
        s_candidates = [e for e in available if shift_counts[e]['S'] < employee_data.loc[employee_data['Name'] == e, 'S_max'].iloc[0]]
        for emp in s_candidates:
            if S_req > 0:
                roster[emp][day] = 'S'
                shift_counts[emp]['S'] += 1
                S_req -= 1
    
    return roster

# --- Generate & Display ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors = {
        'G': 'lightcoral',  # General shift
        'S': 'lightgreen',  # Second shift
        'N': 'lightblue',   # Night shift
        'M': 'yellow',      # Morning shift
        'E': 'purple',      # Evening shift
        'O': 'lightgray',   # Off
        'H': 'orange'       # Holiday
    }
    return f'background-color: {colors.get(val, "")}'

st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({
    s: [sum(1 for v in roster_dict[e] if v == s) for e in employees]
    for s in ['G', 'S', 'N', 'M', 'E', 'O', 'H']
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
