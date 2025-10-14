import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Employee Leave & Shift Plan Generator (Equalized + Opposite Shifts)")

# --- Default Employees ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", "IIS"],
    ["Paneerselvam F", "IIS"],
    ["Rajesh Jayapalan", "IIS"],
    ["Ajay Chidipotu", "Websphere"],
    ["Imran Khan", "Websphere"],
    ["Sammeta Balachander", "Websphere"],
    ["Ramesh Polisetty", ""],
    ["Muppa Divya", ""],
    ["Anil Athkuri", ""],
    ["D Namithananda", ""],
    ["Srinivasu Cheedalla", ""],
    ["Gangavarapu Suneetha", ""],
    ["Lakshmi Narayana Rao", ""],
    ["Pousali C", ""],
    ["Thorat Yashwant", ""],
    ["Srivastav Nitin", ""],
    ["Kishore Khati Vaibhav", ""],
    ["Rupan Venkatesan Anandha", ""],
    ["Chaudhari Kaustubh", ""],
    ["Shejal Gawade", ""],
    ["Vivek Kushwaha", ""],
    ["Abdul Mukthiyar Basha", ""],
    ["M Naveen", ""],
    ["B Madhurusha", ""],
    ["Chinthalapudi Yaswanth", ""],
    ["Edagotti Kalpana", ""]
], columns=["Name", "Skill"])

employees = employee_data["Name"].tolist()

# --- Weekoff Preferences ---
st.subheader("Weekoff Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday Off", employees, default=[])
sunday_monday_off = st.multiselect("Sunday-Monday Off", employees, default=[])
saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees, default=[])
tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday Off", employees, default=[])
thursday_friday_off = st.multiselect("Thursday-Friday Off", employees, default=[])
wednesday_thursday_off = st.multiselect("Wednesday-Thursday Off", employees, default=[])
monday_tuesday_off = st.multiselect("Monday-Tuesday Off", employees, default=[])

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
month = st.selectbox("Month", list(range(1, 13)), index=9, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days + 1)]

# --- Festival Days ---
festival_days = st.multiselect("Festival Days", list(range(1, num_days + 1)), default=[])

# --- Helper Function ---
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in weekday_indices]

# Weekday mapping
fridays_saturdays = get_weekdays(year, month, [4, 5])
sundays_mondays = get_weekdays(year, month, [6, 0])
saturdays_sundays = get_weekdays(year, month, [5, 6])
tuesday_wednesday = get_weekdays(year, month, [1, 2])
thursday_friday = get_weekdays(year, month, [3, 4])
wednesday_thursday = get_weekdays(year, month, [2, 3])
monday_tuesday = get_weekdays(year, month, [0, 1])

# Calculate weekends & working days
saturdays = get_weekdays(year, month, [5])
sundays = get_weekdays(year, month, [6])
num_saturdays = len(saturdays)
num_sundays = len(sundays)
num_weekends = num_saturdays + num_sundays
num_working_days = num_days - num_weekends - len(festival_days)

# --- Month Summary ---
st.subheader("Month Summary")
st.write(f"Number of Saturdays: {num_saturdays}")
st.write(f"Number of Sundays: {num_sundays}")
st.write(f"Total Working Days (excluding weekends and festivals): {num_working_days}")

# --- Leave Plan Generation ---
def generate_leave_plan(target_offs=8):
    roster = {emp: [''] * num_days for emp in employees}
    festival_set = set([d - 1 for d in festival_days])

    for emp in employees:
        off_idx = set()
        if emp in friday_saturday_off:
            off_idx.update([d - 1 for d in fridays_saturdays])
        if emp in sunday_monday_off:
            off_idx.update([d - 1 for d in sundays_mondays])
        if emp in saturday_sunday_off:
            off_idx.update([d - 1 for d in saturdays_sundays])
        if emp in tuesday_wednesday_off:
            off_idx.update([d - 1 for d in tuesday_wednesday])
        if emp in thursday_friday_off:
            off_idx.update([d - 1 for d in thursday_friday])
        if emp in wednesday_thursday_off:
            off_idx.update([d - 1 for d in wednesday_thursday])
        if emp in monday_tuesday_off:
            off_idx.update([d - 1 for d in monday_tuesday])

        for idx in off_idx:
            if 0 <= idx < num_days:
                roster[emp][idx] = 'O'
        for idx in festival_set:
            roster[emp][idx] = 'H'

    # Equalize total offs
    for emp, days in roster.items():
        current_offs = [i for i, v in enumerate(days) if v == 'O']
        diff = len(current_offs) - target_offs

        if diff > 0:
            for idx in current_offs[-diff:]:
                roster[emp][idx] = ''
        elif diff < 0:
            working_days = [i for i, v in enumerate(days) if v == '']
            if len(working_days) >= abs(diff):
                add_days = np.random.choice(working_days, abs(diff), replace=False)
                for idx in add_days:
                    roster[emp][idx] = 'O'

    return roster

# --- Generate Leave Plan ---
target_offs = st.slider("Target Off Days per Employee", min_value=6, max_value=12, value=8)
roster_dict = generate_leave_plan(target_offs)

# --- Opposite Shift Logic for Group1 ---
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
shifts = ['F', 'S', 'N']
shift_counts = {emp: {'F': 0, 'S': 0, 'N': 0} for emp in group1}

for day in range(num_days):
    # Skip if any has off/holiday that day
    skip_day = any(roster_dict[emp][day] in ['O', 'H'] for emp in group1)
    if skip_day:
        continue

    np.random.shuffle(shifts)
    for emp, shift in zip(group1, shifts):
        # Respect max limits
        if shift == 'N' and shift_counts[emp]['N'] >= 10:
            shift = np.random.choice(['F', 'S'])
        elif shift == 'F' and shift_counts[emp]['F'] >= 10:
            shift = np.random.choice(['S', 'N'])
        elif shift == 'S' and shift_counts[emp]['S'] >= 10:
            shift = np.random.choice(['F', 'N'])

        roster_dict[emp][day] = shift
        shift_counts[emp][shift] += 1

# Adjust if minimums not met
for emp in group1:
    for shift_type in ['F', 'S']:
        while shift_counts[emp][shift_type] < 5:
            for day in range(num_days):
                if roster_dict[emp][day] == '':
                    roster_dict[emp][day] = shift_type
                    shift_counts[emp][shift_type] += 1
                    break

# --- Convert to DataFrame ---
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_leaves(val):
    colors = {
        'O': 'lightgray', 
        'H': 'orange',
        'F': '#90EE90',   # Light green
        'S': '#ADD8E6',   # Light blue
        'N': '#DDA0DD'    # Light purple
    }
    return f'background-color: {colors.get(val, "")}'

st.subheader("Employee Leave & Shift Plan")
st.dataframe(df_roster.style.applymap(color_leaves), height=600)

# --- Leave Summary ---
st.subheader("Leave & Shift Summary")
summary = pd.DataFrame({
    'Off Days (O)': [sum(1 for v in roster_dict[e] if v == 'O') for e in employees],
    'Holidays (H)': [sum(1 for v in roster_dict[e] if v == 'H') for e in employees],
    'F Days': [sum(1 for v in roster_dict[e] if v == 'F') for e in employees],
    'S Days': [sum(1 for v in roster_dict[e] if v == 'S') for e in employees],
    'N Days': [sum(1 for v in roster_dict[e] if v == 'N') for e in employees]
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download Leave & Shift Plan CSV", csv, f"leave_shift_plan_{year}_{month:02d}.csv")
