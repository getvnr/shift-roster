import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (5-Day Continuous Shifts)")

# --- Sample Employee Data ---
default_data = {
    "Name": [
        "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan","Ajay Chidipotu",
        "Imran Khan","Sammeta Balachander","Ramesh Polisetty","Muppa Divya",
        "Anil Athkuri","D Namithananda"
    ],
    "First Shift":[5,5,5,5,0,5,0,0,0,0],
    "Second Shift":[5,5,5,5,15,5,20,20,20,20],
    "Night":[10,10,10,10,0,10,0,0,0,0],
    "Comments":["Not come in same shift"]*6 + [""]*4,
    "Skill":["IIS","IIS","IIS","Websphere","Websphere","Websphere","","","",""]
}

df_employees = pd.DataFrame(default_data)
st.subheader("Employee Shift Capacities & Skills")
st.dataframe(df_employees)

# --- Month & Year ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Month", list(range(1,13)), index=10,
                     format_func=lambda x: pd.Timestamp(year,x,1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1,num_days+1)]

festival_days = st.multiselect("Festival Days", list(range(1,num_days+1)), default=[])

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
weekoff_options = {
    "Fri-Sat": [4,5],
    "Sat-Sun": [5,6],
    "Sun-Mon": [6,0],
    "Tue-Wed": [1,2],
    "Thu-Fri": [3,4]
}

employee_weekoff = {}
for key in weekoff_options:
    selected = st.multiselect(f"{key} Off", df_employees['Name'].tolist())
    for emp in selected:
        if emp in employee_weekoff:
            st.error(f"{emp} selected for multiple week-off patterns! Assign only one.")
            st.stop()
        employee_weekoff[emp] = key

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

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

# --- Generate Roster with 5-Day Shift Blocks ---
def generate_roster(df):
    np.random.seed(42)
    roster = {emp:['']*num_days for emp in df['Name']}
    shift_count = {emp:{'F':0,'S':0,'N':0,'O':0,'H':0} for emp in df['Name']}
    festival_set = set(festival_days)

    # Assign Offs
    for idx, row in df.iterrows():
        emp = row['Name']
        total_off_days = num_days - (row['First Shift']+row['Second Shift']+row['Night'])
        pattern = employee_weekoff.get(emp)
        must_off = []
        if pattern:
            wd_indices = weekoff_options[pattern]
            must_off = get_weekdays(year, month, wd_indices)
        off_idx = assign_off_days(num_days, total_off_days, must_off)
        for d in off_idx:
            roster[emp][d]='O'
            shift_count[emp]['O']+=1

    # Assign Shifts in 5-Day Continuous Blocks
    for day in range(0, num_days, 5):
        block_days = list(range(day, min(day+5, num_days)))
        available = [emp for emp in df['Name'] if all(roster[emp][d]=='' for d in block_days)]
        # Assign Night
        night_candidates = [e for e in available if shift_count[e]['N'] < df.loc[df['Name']==e,'Night'].values[0]]
        night_candidates.sort(key=lambda e: shift_count[e]['N'])
        n_needed = 2  # Night coverage
        for emp in night_candidates[:n_needed]:
            for d in block_days:
                roster[emp][d]='N'
                shift_count[emp]['N']+=1
            available.remove(emp)

        # Assign First
        f_candidates = [e for e in available if shift_count[e]['F'] < df.loc[df['Name']==e,'First Shift'].values[0]]
        f_candidates.sort(key=lambda e: shift_count[e]['F'])
        f_needed = 3  # First shift coverage
        for emp in f_candidates[:f_needed]:
            for d in block_days:
                roster[emp][d]='F'
                shift_count[emp]['F']+=1
            available.remove(emp)

        # Assign Second
        s_candidates = [e for e in available if shift_count[e]['S'] < df.loc[df['Name']==e,'Second Shift'].values[0]]
        s_candidates.sort(key=lambda e: shift_count[e]['S'])
        for emp in s_candidates:
            for d in block_days:
                roster[emp][d]='S'
                shift_count[emp]['S']+=1

        # Festival override
        for d in block_days:
            if d+1 in festival_set:
                for emp in df['Name']:
                    roster[emp][d]='H'
                    shift_count[emp]['H']+=1

    return roster

# --- Generate & Display ---
roster_dict = generate_roster(df_employees)
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors={'F':'green','S':'lightgreen','N':'lightblue','O':'lightgray','H':'orange'}
    return f'background-color:{colors.get(val,"")}'

st.subheader("Generated 5-Day Block Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

st.subheader("Shift Summary")
summary = pd.DataFrame({s:[sum(1 for v in roster_dict[e] if v==s) for e in df_employees['Name']] 
                        for s in ['F','S','N','O','H']}, index=df_employees['Name'])
st.dataframe(summary)

csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"5day_block_roster_{year}_{month:02d}.csv")
