import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (5-Day Shift Blocks)")

# --- Employees ---
employees = [
    "Ajay Chidipotu","Imran Khan","Sammeta Balachander","Gopalakrishnan Selvaraj",
    "Paneerselvam F","Rajesh Jayapalan","Ramesh Polisetty","Srinivasu Cheedalla",
    "Muppa Divya","Anil Athkuri","Gangavarapu Suneetha","Lakshmi Narayana Rao",
    "Pousali C","D Namithananda","Thorat Yashwant","Srivastav Nitin",
    "Kishore Khati Vaibhav","Rupan Venkatesan Anandha","Chaudhari Kaustubh",
    "Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen",
    "B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana"
]

# --- Nightshift Exempt ---
nightshift_exempt = st.multiselect(
    "Nightshift-Exempt Employees", employees, 
    default=["Ramesh Polisetty","Srinivasu Cheedalla","Muppa Divya","Anil Athkuri"]
)

# --- Weekoff Preferences ---
st.subheader("Weekend Off Preferences")
fri_sat_off = st.multiselect("Friday-Saturday Off", employees, default=[])
sun_mon_off = st.multiselect("Sunday-Monday Off", employees, default=[])
sat_sun_off = st.multiselect("Saturday-Sunday Off", employees, default=[])

# --- Month & Year ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox(
    "Month", list(range(1,13)), index=10,
    format_func=lambda x: pd.Timestamp(year,x,1).strftime('%B')
)
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]
festival_days = st.multiselect("Festival Days (Dates)", list(range(1,num_days+1)), default=[])

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

def assign_off_days(emp, total_off, must_off):
    off_set = set(d-1 for d in must_off)
    remaining = total_off - len(off_set)
    candidates = [i for i in range(num_days) if i not in off_set]
    step = max(1, len(candidates)//remaining) if remaining>0 else len(candidates)
    chosen=[]
    idx=0
    while len(chosen)<remaining and idx<len(candidates):
        chosen.append(candidates[idx])
        idx+=step
    off_set.update(chosen)
    return sorted(off_set)

# --- Generate Roster ---
def generate_roster():
    np.random.seed(42)
    roster = {emp:['']*num_days for emp in employees}
    shift_count = {emp:{s:0 for s in ['F','S','N','O','H']} for emp in employees}
    working_days_per_emp = num_days - 8  # example 8 off days per month

    fridays_saturdays = get_weekdays(year, month, [4,5])
    sundays_mondays = get_weekdays(year, month, [6,0])
    saturdays_sundays = get_weekdays(year, month, [5,6])
    
    # Assign Offs
    for emp in employees:
        weekoff=[]
        if emp in fri_sat_off: weekoff=fridays_saturdays
        elif emp in sun_mon_off: weekoff=sundays_mondays
        elif emp in sat_sun_off: weekoff=saturdays_sundays
        off_idx = assign_off_days(emp, total_off=8, must_off=weekoff)
        for idx in off_idx:
            roster[emp][idx]='O'
            shift_count[emp]['O']+=1

    festival_set = set(festival_days)

    # Assign shifts in 5-day blocks
    shifts_order = ['F','S','N']  # can customize per employee
    block_size = 5

    for day in range(num_days):
        if (day+1) in festival_set:
            for emp in employees:
                roster[emp][day]='H'
            continue
        available = [e for e in employees if roster[e][day]=='']
        for emp in available:
            # Determine 5-day shift block
            last_shift = None
            for prev_day in range(day-1, -1, -1):
                if roster[emp][prev_day] in ['F','S','N']:
                    last_shift = roster[emp][prev_day]
                    break
            if last_shift is None:
                shift = np.random.choice(shifts_order)
            else:
                shift = last_shift
            # Assign for consecutive 5 days
            for b in range(block_size):
                if day+b < num_days and roster[emp][day+b]=='':
                    if shift=='N' and emp in nightshift_exempt:
                        shift='S'
                    roster[emp][day+b]=shift
                    shift_count[emp][shift]+=1
            day += block_size-1  # skip assigned block

    return roster

# --- Generate & Display ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors={'F':'lightgreen','S':'lightblue','N':'lightpink','O':'lightgray','H':'orange'}
    return f'background-color:{colors.get(val,"")}'
st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({s:[sum(1 for v in roster_dict[e] if v==s) for e in employees] for s in ['F','S','N','O','H']}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
