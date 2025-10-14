import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Employee Leave & Shift Plan Generator")

# --- Employee Data ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", "Group1"],
    ["Paneerselvam F", "Group1"],
    ["Rajesh Jayapalan", "Group1"],
    ["Ajay Chidipotu", "Group2"],
    ["Imran Khan", "Group2"],
    ["Sammeta Balachander", "Group2"],
    ["Ramesh Polisetty", "Group3"],
    ["Srinivasu Cheedalla", "Group3"],
    ["Gangavarapu Suneetha", "Group3"],
    ["Lakshmi Narayana Rao", "Group3"],
    ["Muppa Divya", "Group4"],
    ["Anil Athkuri", "Group4"],
    ["D Namithananda", "Group4"],
    ["Pousali C", "Coverage"],
    ["B Madhurusha", "Coverage"],
    ["Chinthalapudi Yaswanth", "Coverage"],
    ["Edagotti Kalpana", "Coverage"],
    ["Thorat Yashwant", "Coverage"],
    ["Srivastav Nitin", "Coverage"],
    ["Kishore Khati Vaibhav", "Coverage"],
    ["Rupan Venkatesan Anandha", "Coverage"],
    ["Chaudhari Kaustubh", "Coverage"],
    ["Shejal Gawade", "Coverage"],
    ["Vivek Kushwaha", "Coverage"]
], columns=["Name", "Group"])

employees = employee_data["Name"].tolist()

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
weekoff_options = ["Mon-Tue","Tue-Wed","Wed-Thu","Thu-Fri","Fri-Sat","Sat-Sun","Sun-Mon"]
weekoff_dict = {}
for wo in weekoff_options:
    weekoff_dict[wo] = st.multiselect(f"{wo} Off", employees, default=[])

# --- Individual Leaves ---
st.subheader("Individual Leaves")
individual_leaves = {}
for emp in employees:
    days = st.multiselect(f"{emp} Leave Dates (1-{monthrange(2025,11)[1]})", [], default=[])
    individual_leaves[emp] = days

# --- Month & Year ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Month", list(range(1,13)), index=10, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]

# --- Festival Days ---
festival_days = st.multiselect("Festival Days", list(range(1,num_days+1)), default=[])

# --- Helper Functions ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

# Precompute weekends
saturdays = get_weekdays(year, month, [5])
sundays = get_weekdays(year, month, [6])
weekends_set = set(saturdays + sundays)

# --- Generate Leave & Shift Plan ---
def generate_plan(target_offs=8):
    roster = {emp: ['']*num_days for emp in employees}
    festival_set = set([d-1 for d in festival_days])

    # Step 1: Apply individual leaves & festivals
    for emp in employees:
        for d in individual_leaves.get(emp, []):
            roster[emp][d-1] = 'O'
        for idx in festival_set:
            roster[emp][idx] = 'H'

    # Step 2: Apply group rules
    # Group1 shifts F/S/N rotation, max limits
    group1 = employee_data[employee_data.Group=="Group1"]["Name"].tolist()
    group2 = employee_data[employee_data.Group=="Group2"]["Name"].tolist()
    group3 = employee_data[employee_data.Group=="Group3"]["Name"].tolist()
    group4 = employee_data[employee_data.Group=="Group4"]["Name"].tolist()
    coverage = employee_data[employee_data.Group=="Coverage"]["Name"].tolist()

    shifts = ['F','S','N']
    group1_shifts = {emp: [] for emp in group1}
    group2_shifts = {emp: [] for emp in group2}
    
    # Apply Group1 rotation
    for i, day in enumerate(range(num_days)):
        for idx, emp in enumerate(group1):
            if roster[emp][day]=='':
                # rotate only if previous day was off
                if day>0 and roster[emp][day-1] in ['O','H']:
                    group1_shifts[emp].append(shifts[(day+idx)%3])
                elif day==0:
                    group1_shifts[emp].append(shifts[idx%3])
                else:
                    group1_shifts[emp].append(group1_shifts[emp][-1])
                roster[emp][day] = group1_shifts[emp][-1]

    # Apply Group2 rotation with Imran restriction (no N)
    for i, day in enumerate(range(num_days)):
        for idx, emp in enumerate(group2):
            if roster[emp][day]=='':
                if day>0 and roster[emp][day-1] in ['O','H']:
                    shift_idx = (day+idx)%3
                    s = shifts[shift_idx]
                    if emp=="Imran Khan" and s=='N':
                        s='F'
                    group2_shifts[emp].append(s)
                elif day==0:
                    s = shifts[idx%3]
                    if emp=="Imran Khan" and s=='N': s='F'
                    group2_shifts[emp].append(s)
                else:
                    group2_shifts[emp].append(group2_shifts[emp][-1])
                roster[emp][day]=group2_shifts[emp][-1]

    # Group3 & 4 fixed shifts
    for emp in group3:
        fixed = 'G' if emp!='Srinivasu Cheedalla' else 'E'
        for day in range(num_days):
            if roster[emp][day]=='':
                roster[emp][day] = fixed
    for emp in group4:
        for day in range(num_days):
            if roster[emp][day]=='':
                roster[emp][day]='S'

    # Coverage pool: distribute fair offs & ensure 24/7 coverage
    coverage_shifts=['F','S','N']
    max_nights=6
    offs_per_person = min(target_offs, num_days//3)  # adjust based on month
    # Initialize counters
    night_count = {emp:0 for emp in coverage}
    for day in range(num_days):
        day_roster=[roster[emp][day] for emp in employees if roster[emp][day] not in ['O','H']]
        # Assign shifts while respecting limits
        n_count=sum([1 for v in day_roster if v=='N'])
        f_count=sum([1 for v in day_roster if v=='F'])
        s_count=sum([1 for v in day_roster if v=='S'])
        # Assign to unassigned
        for emp in coverage:
            if roster[emp][day]=='':
                # Apply fair off
                if roster[emp].count('O')<offs_per_person and np.random.rand()<0.2:
                    roster[emp][day]='O'
                    continue
                # Night limit
                if night_count[emp]<max_nights and n_count<2:
                    roster[emp][day]='N'
                    night_count[emp]+=1
                    n_count+=1
                elif f_count<3:
                    roster[emp][day]='F'
                    f_count+=1
                else:
                    roster[emp][day]='S'
                    s_count+=1

    return roster

# --- Generate & Display ---
target_offs = st.slider("Target Off Days per Employee (Coverage)", min_value=6, max_value=10, value=8)
roster_dict = generate_plan(target_offs)
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_leaves(val):
    colors={'O':'lightgray','H':'orange','F':'lightblue','S':'lightgreen','N':'lightpink','G':'lightyellow','E':'violet'}
    return f'background-color: {colors.get(val,"")}'

st.subheader("Employee Leave & Shift Plan")
st.dataframe(df_roster.style.applymap(color_leaves), height=600)

# --- Leave Summary ---
st.subheader("Leave Summary")
summary=pd.DataFrame({
    'Off Days (O)':[sum(1 for v in roster_dict[e] if v=='O') for e in employees],
    'Holidays (H)':[sum(1 for v in roster_dict[e] if v=='H') for e in employees]
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download Leave Plan CSV", csv, f"leave_plan_{year}_{month:02d}.csv")
