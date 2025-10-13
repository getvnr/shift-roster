import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Employee Leave Plan Generator (Equalized Off Days)")

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

# --- Helper Functions ---
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

    # Step 1: assign offs based on selected weekdays
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

    # Step 2: Equalize total offs for each employee
    for emp, days in roster.items():
        current_offs = [i for i, v in enumerate(days) if v == 'O']
        diff = len(current_offs) - target_offs

        # Remove extra offs
        if diff > 0:
            for idx in current_offs[-diff:]:
                roster[emp][idx] = ''

        # Add missing offs randomly
        elif diff < 0:
            working_days = [i for i, v in enumerate(days) if v == '']
            if len(working_days) >= abs(diff):
                add_days = np.random.choice(working_days, abs(diff), replace=False)
                for idx in add_days:
                    roster[emp][idx] = 'O'

    return roster

# --- Generate & Display ---
target_offs = st.slider("Target Off Days per Employee", min_value=6, max_value=12, value=8)
roster_dict = generate_leave_plan(target_offs)
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_leaves(val):
    colors = {'O': 'lightgray', 'H': 'orange'}
    return f'background-color: {colors.get(val, "")}'

st.subheader("Employee Leave Plan")
st.dataframe(df_roster.style.applymap(color_leaves), height=600)

# --- Leave Summary ---
st.subheader("Leave Summary")
summary = pd.DataFrame({
    'Off Days (O)': [sum(1 for v in roster_dict[e] if v == 'O') for e in employees],
    'Holidays (H)': [sum(1 for v in roster_dict[e] if v == 'H') for e in employees]
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download Leave Plan CSV", csv, f"leave_plan_{year}_{month:02d}.csv")
