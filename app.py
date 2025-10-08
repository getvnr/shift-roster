import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator")

# --- Default Employees ---
default_employees = [
    "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan","Ajay Chidipotu",
    "Imran Khan","Sammeta Balachander","Ramesh Polisetty","Muppa Divya",
    "Anil Athkuri","D Namithananda"
]

# --- Employee Input ---
employees = st.text_area("Employee Names (comma separated):", value=", ".join(default_employees))
employees = [e.strip() for e in employees.split(",") if e.strip()]
if not employees:
    st.error("Provide at least one employee.")
    st.stop()

# --- Nightshift Exempt ---
nightshift_exempt = st.multiselect("Nightshift-Exempt Employees", employees, default=["Ramesh Polisetty","Muppa Divya"])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=["Gopalakrishnan Selvaraj"])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=["Ajay Chidipotu"])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=["Muppa Divya"])

# --- Validate Overlaps ---
groups = [friday_saturday_off, sunday_monday_off, saturday_sunday_off]
names = ["Fri-Sat","Sun-Mon","Sat-Sun"]
for i in range(len(groups)):
    for j in range(i+1, len(groups)):
        overlap = set(groups[i]) & set(groups[j])
        if overlap:
            st.error(f"Employees in both {names[i]} & {names[j]}: {', '.join(overlap)}")
            st.stop()

# --- Month & Year ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Month", list(range(1,13)), index=10, format_func=lambda x: pd.Timestamp(year,x,1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1,num_days+1)]

# --- Employee Shift Limits ---
st.subheader("Max Shifts Per Employee")
default_shift_data = {
    "Name": employees,
    "First Shift": [5]*len(employees),
    "Second Shift": [10]*len(employees),
    "Night": [5]*len(employees)
}
df = pd.DataFrame(default_shift_data)
df = st.data_editor(df, num_rows="dynamic")

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

fridays_saturdays = get_weekdays(year, month, [4,5])
sundays_mondays = get_weekdays(year, month, [6,0])
saturdays_sundays = get_weekdays(year, month, [5,6])

# --- Assign Off Days ---
def assign_off_days(num_days, total_off, must_off):
    off_set = set(d-1 for d in must_off)
    if len(off_set) >= total_off:
        return sorted(list(off_set))[:total_off]
    remaining = total_off - len(off_set)
    candidates = [i for i in range(num_days) if i not in off_set]
    step = max(1, len(candidates)//remaining) if remaining>0 else len(candidates)
    chosen=[]
    idx=0
    while len(chosen)<remaining and idx<len(candidates):
        chosen.append(candidates[idx])
        idx+=step
    for i in range(len(candidates)):
        if len(chosen)>=remaining: break
        if candidates[i] not in chosen:
            chosen.append(candidates[i])
    off_set.update(chosen)
    return sorted(off_set)

# --- Generate Roster ---
def generate_roster():
    np.random.seed(42)
    roster = {emp:['']*num_days for emp in employees}
    shift_count = {emp:{'F':0,'S':0,'N':0,'O':0} for emp in employees}
    
    # Assign Offs
    for emp in employees:
        weekoff=[]
        if emp in friday_saturday_off: weekoff=fridays_saturdays
        elif emp in sunday_monday_off: weekoff=sundays_mondays
        elif emp in saturday_sunday_off: weekoff=saturdays_sundays
        total_off_days = 8  # example: adjust as needed
        off_idx = assign_off_days(num_days,total_off_days,weekoff)
        for idx in off_idx:
            roster[emp][idx]='O'
            shift_count[emp]['O']+=1

    # Assign Shifts in 5-day continuous blocks
    block_size = 5
    for day in range(0, num_days, block_size):
        block_days = list(range(day, min(day+block_size, num_days)))
        available = [emp for emp in employees if all(roster[emp][d]=='' for d in block_days)]

        # Night shift (2 per block)
        night_candidates = [e for e in available if e not in nightshift_exempt and shift_count[e]['N'] < df.loc[df['Name']==e,'Night'].values[0]]
        night_candidates.sort(key=lambda e: shift_count[e]['N'])
        n_needed = min(2,len(night_candidates))
        assigned = night_candidates[:n_needed]
        for emp in assigned:
            for d in block_days:
                roster[emp][d]='N'
                shift_count[emp]['N']+=1
            available.remove(emp)

        # First shift (3 per block)
        f_candidates = [e for e in available if shift_count[e]['F'] < df.loc[df['Name']==e,'First Shift'].values[0]]
        f_candidates.sort(key=lambda e: shift_count[e]['F'])
        f_needed = min(3,len(f_candidates))
        assigned = f_candidates[:f_needed]
        for emp in assigned:
            for d in block_days:
                roster[emp][d]='F'
                shift_count[emp]['F']+=1
            available.remove(emp)

        # Remaining -> Second shift
        for emp in available:
            for d in block_days:
                roster[emp][d]='S'
                shift_count[emp]['S']+=1

    return roster

# --- Generate & Display ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors={'F':'green','S':'lightgreen','N':'lightblue','O':'lightgray'}
    return f'background-color:{colors.get(val,"")}'
st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({s:[sum(1 for v in roster_dict[e] if v==s) for e in employees] for s in ['F','S','N','O']}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
