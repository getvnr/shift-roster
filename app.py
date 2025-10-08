import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import math

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator")

# --- Default Employees ---
default_employees = [
    "Ramesh Polisetty","Ajay Chidipotu","Srinivasu Cheedalla","Imran Khan",
    "Sammeta Balachander","Muppa Divya","Anil Athkuri","Gangavarapu Suneetha",
    "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan","Lakshmi Narayana Rao",
    "Pousali C","D Namithananda","Thorat Yashwant","Srivastav Nitin",
    "Kishore Khati Vaibhav","Rupan Venkatesan Anandha","Chaudhari Kaustubh",
    "Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen",
    "B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana"
]

# --- Employee Input ---
employees = st.text_area("Employee Names (comma separated):", value=", ".join(default_employees))
employees = [e.strip() for e in employees.split(",") if e.strip()]
if not employees:
    st.error("Provide at least one employee.")
    st.stop()

# --- Nightshift Exempt ---
nightshift_exempt = st.multiselect(
    "Nightshift-Exempt Employees", employees,
    default=["Ramesh Polisetty","Srinivasu Cheedalla"]
)

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=["Gangavarapu Suneetha","Lakshmi Narayana Rao"])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=["Ajay Chidipotu","Imran Khan"])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=["Muppa Divya","Anil Athkuri"])

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
month = st.selectbox("Month", list(range(1,13)), index=10,
                     format_func=lambda x: pd.Timestamp(year,x,1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1,num_days+1)]

working_days_per_emp = st.number_input("Working days per employee", 1, num_days, 21)
festival_days = st.multiselect("Festival Days", list(range(1,num_days+1)), default=[])

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

fridays_saturdays = get_weekdays(year, month, [4,5])
sundays_mondays = get_weekdays(year, month, [6,0])
saturdays_sundays = get_weekdays(year, month, [5,6])

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

# --- Roster Generation ---
def generate_roster():
    np.random.seed(42)
    roster = {emp:['']*num_days for emp in employees}
    shift_count = {emp:{s:0 for s in ['F','G1','N','S','O','H']} for emp in employees}
    total_off_days = num_days - working_days_per_emp
    festival_set = set(festival_days)
    g1_specials = ["Ramesh Polisetty","Srinivasu Cheedalla","Gangavarapu Suneetha","Lakshmi Narayana Rao"]

    # Assign Off Days
    for emp in employees:
        weekoff=[]
        if emp in friday_saturday_off: weekoff=fridays_saturdays
        elif emp in sunday_monday_off: weekoff=sundays_mondays
        elif emp in saturday_sunday_off: weekoff=saturdays_sundays
        off_idx = assign_off_days(num_days, total_off_days, weekoff)
        for idx in off_idx:
            roster[emp][idx]='O'
            shift_count[emp]['O']+=1

    # Assign Shifts
    for day in range(num_days):
        day_num = day+1
        wd = weekday(year, month, day_num)
        if day_num in festival_set:
            for emp in employees:
                roster[emp][day]='H'
            continue

        available = [e for e in employees if roster[e][day]=='']

        # Weekend coverage
        is_weekend = wd>=5
        n_required = 2 if is_weekend else 2
        f_required = 3 if is_weekend else 3
        s_required = 3 if is_weekend else len(available)

        # --- Night shifts ---
        non_exempt = [e for e in available if e not in nightshift_exempt]
        non_exempt.sort(key=lambda e: shift_count[e]['N'])
        n_assigned=0
        for emp in non_exempt:
            if n_assigned>=n_required: break
            cons=0
            for p in range(day-1,max(-1,day-6),-1):
                if roster[emp][p]=='N': cons+=1
                else: break
            if cons>=5: continue
            roster[emp][day]='N'
            shift_count[emp]['N']+=1
            n_assigned+=1
            available.remove(emp)

        # --- G1 shifts ---
        g1_avail = [e for e in available if e in g1_specials]
        g1_avail.sort(key=lambda e: shift_count[e]['G1'])
        g1_assigned=0
        for emp in g1_avail:
            roster[emp][day]='G1'
            shift_count[emp]['G1']+=1
            g1_assigned+=1
            available.remove(emp)

        # --- F shifts ---
        f_needed = max(0, f_required - g1_assigned)
        available.sort(key=lambda e: shift_count[e]['F'])
        f_assigned=0
        for emp in available:
            if f_assigned>=f_needed: break
            roster[emp][day]='F'
            shift_count[emp]['F']+=1
            f_assigned+=1
            available.remove(emp)

        # --- S shifts ---
        s_needed = max(0, s_required)
        s_assigned=0
        for emp in available:
            if s_assigned>=s_needed: break
            roster[emp][day]='S'
            shift_count[emp]['S']+=1
            s_assigned+=1
            available.remove(emp)

        # Assign remaining to S
        for emp in available:
            roster[emp][day]='S'
            shift_count[emp]['S']+=1

    return roster

# --- Generate Roster ---
roster_dict = generate_roster()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    colors={'G1':'limegreen','F':'green','N':'lightblue','S':'lightgreen','O':'lightgray','H':'orange'}
    return f'background-color:{colors.get(val,"")}'

st.subheader("Generated Roster")
st.dataframe(df_roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary = pd.DataFrame({s:[sum(1 for v in roster_dict[e] if v==s) for e in employees]
                        for s in ['G1','F','N','S','O','H']}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
