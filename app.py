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
nightshift_exempt = st.multiselect("Nightshift-Exempt Employees", employees, default=["Ramesh Polisetty", "Srinivasu Cheedalla"])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=[])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=[])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=[])

# --- Validate Overlaps ---
groups = [friday_saturday_off, sunday_monday_off, saturday_sunday_off]
names = ["Fri-Sat", "Sun-Mon", "Sat-Sun"]
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

fridays_saturdays = get_weekdays(year, month, [4, 5])
sundays_mondays = get_weekdays(year, month, [6, 0])
saturdays_sundays = get_weekdays(year, month, [5, 6])

# --- Off Days Assignment ---
def assign_off_days(emp_name, num_days):
    off_days = []
    if emp_name in friday_saturday_off: off_days += fridays_saturdays
    if emp_name in sunday_monday_off: off_days += sundays_mondays
    if emp_name in saturday_sunday_off: off_days += saturdays_sundays
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
    
    # Assign Shifts in 5-day blocks
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
            F_req, S_req, N_req = 3, 3, 2
        else:
            F_req, S_req, N_req = 5, 5, 2
        
        available = [e for e in employees if roster[e][day] == '']
        
        # Assign Night shifts first (avoid nightshift exempt)
        n_candidates = [e for e in available if e not in nightshift_exempt]
        n_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'N_max'].values[0], reverse=True)
        n_assigned = 0
        for emp in n_candidates:
            # Check 5-day continuity
            if n_assigned >= N_req: break
            if day >= 5 and all(roster[emp][day - 5 + p] == 'N' for p in range(5)): continue
            roster[emp][day] = 'N'
            n_assigned += 1
            available.remove(emp)
        
        # Assign First Shift
        f_candidates = available.copy()
        f_candidates.sort(key=lambda x: employee_data.loc[employee_data['Name'] == x, 'F_max'].values[0], reverse=True)
        f_assigned = 0
        for emp in f_candidates:
            if f_assigned >= F_req: break
            roster[emp][day] = 'F'
            f_assigned += 1
            available.remove(emp)
        
        # Assign Second Shift to remaining
        for emp in available:
            roster[emp][day] = 'S'
    
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
