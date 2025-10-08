import streamlit as st
import pandas as pd
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (5-Day Blocks + 2-Day Offs)")

# --- Employee Data ---https://github.com/getvnr/shift-roster/blob/main/app.py
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

# --- Festival Days ---
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

# --- Helper ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

def assign_off_days(num_days, block_size, weekoff_days):
    """Assign 2-day offs after each 5-day block."""
    offs = []
    day = 0
    while day < num_days:
        # After 5-day block, assign 2 days off
        start_block = day
        end_block = min(day + block_size, num_days)
        day = end_block
        # 2 days off
        for o in range(day, min(day+2, num_days)):
            offs.append(o)
        day += 2
    # Ensure weekoff_days are included
    offs.extend([d-1 for d in weekoff_days if d-1 not in offs])
    return sorted(list(set(offs)))

# --- Generate Roster ---
def generate_roster(df):
    roster = {emp:['']*num_days for emp in df['Name']}
    shift_count = {emp:{'F':0,'S':0,'N':0,'O':0,'H':0} for emp in df['Name']}
    festival_set = set(festival_days)

    # Assign offs
    for idx, row in df.iterrows():
        emp = row['Name']
        pattern = employee_weekoff.get(emp)
        weekoff_days = get_weekdays(year, month, weekoff_options[pattern]) if pattern else []
        off_idx = assign_off_days(num_days, 5, weekoff_days)
        for d in off_idx:
            roster[emp][d]='O'
            shift_count[emp]['O']+=1

    # Assign shifts in 5-day blocks
    for day in range(0, num_days, 5):
        block_days = list(range(day, min(day+5, num_days)))
        available = [emp for emp in df['Name'] if all(roster[emp][d]=='' for d in block_days)]
        np.random.shuffle(available)

        # Assign Night first, then F, then S
        for emp in available:
            emp_night_remaining = df.loc[df['Name']==emp,'Night'].values[0] - shift_count[emp]['N']
            emp_first_remaining = df.loc[df['Name']==emp,'First Shift'].values[0] - shift_count[emp]['F']
            emp_second_remaining = df.loc[df['Name']==emp,'Second Shift'].values[0] - shift_count[emp]['S']

            # Night block
            if emp_night_remaining >= len(block_days):
                for d in block_days:
                    roster[emp][d]='N'
                    shift_count[emp]['N']+=1
                continue

            # First block
            if emp_first_remaining >= len(block_days):
                for d in block_days:
                    roster[emp][d]='F'
                    shift_count[emp]['F']+=1
                continue

            # Second block
            if emp_second_remaining >= len(block_days):
                for d in block_days:
                    roster[emp][d]='S'
                    shift_count[emp]['S']+=1
                continue

        # Fill remaining empty with Second shift
        for d in block_days:
            for emp in df['Name']:
                if roster[emp][d]=='':
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
st.download_button("Download CSV", csv, f"roster_{year}_{month:02d}.csv")
