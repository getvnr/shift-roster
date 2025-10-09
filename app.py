import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (5-day blocks)")

# --- Default Employees and Shift Limits ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", 5, 5, 10, 5, 5, "IIS"],
    ["Paneerselvam F", 5, 5, 10, 5, 5, "IIS"],
    ["Rajesh Jayapalan", 5, 5, 5, 5, 5, "IIS"],
    ["Ajay Chidipotu", 5, 5, 10, 5, 5, "Websphere"],
    ["Imran Khan", 5, 15, 0, 5, 5, "Websphere"],
    ["Sammeta Balachander", 5, 5, 10, 5, 5, "Websphere"],
    ["Ramesh Polisetty", 20, 0, 0, 0, 0, ""],  # Always General shift
    ["Muppa Divya", 0, 20, 0, 0, 0, ""],  # Always Second shift
    ["Anil Athkuri", 0, 20, 0, 0, 0, ""],  # Always Second shift
    ["D Namithananda", 0, 20, 0, 0, 0, ""],  # Always Second shift
    ["Srinivasu Cheedalla", 0, 0, 0, 0, 20, ""],  # Always Evening shift
    ["Gangavarapu Suneetha", 20, 0, 0, 0, 0, ""],  # Always General shift
    ["Lakshmi Narayana Rao", 20, 0, 0, 0, 0, ""],  # Always General shift
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
            roster[emp][day] = 'O'

    festival_set = set(festival_days)
    
    # Define provided roster for listed employees (01-11-2025 to 30-11-2025, 30 days)
    provided_roster = {
        "Gopalakrishnan Selvaraj": ['O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O'],
        "Paneerselvam F": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O'],
        "Rajesh Jayapalan": ['O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O'],
        "Ajay Chidipotu": ['O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O'],
        "Imran Khan": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O'],
        "Sammeta Balachander": ['O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'N', 'N', 'N', 'N', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O', 'M', 'M', 'M', 'M', 'M', 'O', 'O'],
        "Ramesh Polisetty": ['O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O'],
        "Muppa Divya": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O'],
        "Anil Athkuri": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O'],
        "D Namithananda": ['O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O', 'S', 'S', 'S', 'S', 'S', 'O', 'O'],
        "Srinivasu Cheedalla": ['O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O', 'E', 'E', 'E', 'E', 'E', 'O', 'O'],
        "Gangavarapu Suneetha": ['O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O'],
        "Lakshmi Narayana Rao": ['O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O', 'G', 'G', 'G', 'G', 'G', 'O', 'O']
    }
    
    # Track shift counts to enforce maximums
    shift_counts = {emp: {'G': 0, 'S': 0, 'N': 0, 'M': 0, 'E': 0} for emp in employees}
    
    # Define fixed shift employees for fallback (used for days beyond provided roster or other months)
    fixed_shift_employees = {
        "Ramesh Polisetty": 'G',
        "Muppa Divya": 'S',
        "Anil Athkuri": 'S',
        "D Namithananda": 'S',
        "Srinivasu Cheedalla": 'E',
        "Gangavarapu Suneetha": 'G',
        "Lakshmi Narayana Rao": 'G'
    }
    
    # Apply provided roster for listed employees, respecting month length
    provided_roster_length = 30  # Length of provided roster (November 2025)
    for emp in provided_roster.keys():
        for day in range(num_days):
            if day < provided_roster_length and (year == 2025 and month == 11):
                roster[emp][day] = provided_roster[emp][day]
                shift = roster[emp][day]
                if shift in ['G', 'S', 'N', 'M', 'E']:
                    shift_counts[emp][shift] += 1
            else:
                # Fallback for days beyond provided roster or other months
                if emp in fixed_shift_employees and day not in assign_off_days(emp, num_days):
                    if emp not in nightshift_exempt or fixed_shift_employees[emp] != 'N':
                        max_shifts = employee_data.loc[employee_data['Name'] == emp, ['G_max', 'S_max', 'N_max', 'M_max', 'E_max']].iloc[0]
                        shift = fixed_shift_employees[emp]
                        if shift_counts[emp][shift] < max_shifts[f"{shift}_max"]:
                            roster[emp][day] = shift
                            shift_counts[emp][shift] += 1
    
    # Assign shifts for remaining employees and any unassigned days
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
