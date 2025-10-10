import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Employee Leave Plan Generator")

# --- Default Employees and Shift Limits ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", 0, 15, 10, 15, 0, "IIS"],
    ["Paneerselvam F", 0, 15, 10, 15, 0, "IIS"],
    ["Rajesh Jayapalan", 0, 15, 10, 15, 0, "IIS"],
    ["Ajay Chidipotu", 0, 15, 10, 15, 0, "Websphere"],
    ["Imran Khan", 0, 25, 0, 15, 0, "Websphere"],
    ["Sammeta Balachander", 0, 15, 10, 15, 0, "Websphere"],
    ["Ramesh Polisetty", 25, 0, 0, 0, 0, ""],
    ["Muppa Divya", 0, 25, 0, 0, 0, ""],
    ["Anil Athkuri", 0, 25, 0, 0, 0, ""],
    ["D Namithananda", 0, 25, 0, 0, 0, ""],
    ["Srinivasu Cheedalla", 0, 0, 0, 0, 25, ""],
    ["Gangavarapu Suneetha", 25, 0, 0, 0, 0, ""],
    ["Lakshmi Narayana Rao", 25, 0, 0, 0, 0, ""],
    ["Pousali C", 10, 10, 5, 0, 0, ""],
    ["Thorat Yashwant", 10, 10, 5, 0, 0, ""],
    ["Srivastav Nitin", 10, 10, 5, 0, 0, ""],
    ["Kishore Khati Vaibhav", 10, 10, 5, 0, 0, ""],
    ["Rupan Venkatesan Anandha", 10, 10, 5, 0, 0, ""],
    ["Chaudhari Kaustubh", 10, 10, 5, 0, 0, ""],
    ["Shejal Gawade", 10, 10, 5, 0, 0, ""],
    ["Vivek Kushwaha", 10, 10, 5, 0, 0, ""],
    ["Abdul Mukthiyar Basha", 10, 10, 5, 0, 0, ""],
    ["M Naveen", 10, 10, 5, 0, 0, ""],
    ["B Madhurusha", 10, 10, 5, 0, 0, ""],
    ["Chinthalapudi Yaswanth", 10, 10, 5, 0, 0, ""],
    ["Edagotti Kalpana", 10, 10, 5, 0, 0, ""]
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
month = st.selectbox("Month", list(range(1, 13)), index=11, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
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
def generate_leave_plan():
    roster = {emp: [''] * num_days for emp in employees}
    
    # Assign Offs and Holidays
    festival_set = set([d - 1 for d in festival_days])
    for emp in employees:
        off_idx = set()
        no_weekend_employees = [
            "Ramesh Polisetty", "Muppa Divya", "Anil Athkuri", "D Namithananda",
            "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao",
            "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan",
            "Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"
        ]
        if emp in no_weekend_employees:
            off_idx.update([d - 1 for d in saturdays_sundays if d <= num_days])
        else:
            if emp in friday_saturday_off:
                off_idx.update([d - 1 for d in fridays_saturdays if d <= num_days])
            if emp in sunday_monday_off:
                off_idx.update([d - 1 for d in sundays_mondays if d <= num_days])
            if emp in saturday_sunday_off:
                off_idx.update([d - 1 for d in saturdays_sundays if d <= num_days])
            if emp in tuesday_wednesday_off:
                off_idx.update([d - 1 for d in tuesday_wednesday if d <= num_days])
            if emp in thursday_friday_off:
                off_idx.update([d - 1 for d in thursday_friday if d <= num_days])
            if emp in wednesday_thursday_off:
                off_idx.update([d - 1 for d in wednesday_thursday if d <= num_days])
            if emp in monday_tuesday_off:
                off_idx.update([d - 1 for d in monday_tuesday if d <= num_days])
        
        for idx in off_idx:
            roster[emp][idx] = 'O'
        for idx in festival_set:
            roster[emp][idx] = 'H'
    
    return roster

# --- Generate & Display ---
roster_dict = generate_leave_plan()
df_roster = pd.DataFrame(roster_dict, index=dates).T

# --- Color Coding ---
def color_leaves(val):
    colors = {
        'O': 'lightgray',  # Off
        'H': 'orange'      # Holiday
    }
    return f'background-color: {colors.get(val, "")}'

st.subheader("Employee Leave Plan")
st.dataframe(df_roster.style.applymap(color_leaves), height=600)

# --- Leave Summary ---
st.subheader("Leave Summary")
summary = pd.DataFrame({
    'O': [sum(1 for v in roster_dict[e] if v == 'O') for e in employees],
    'H': [sum(1 for v in roster_dict[e] if v == 'H') for e in employees]
}, index=employees)
st.dataframe(summary)

# --- Download CSV ---
csv = df_roster.to_csv().encode('utf-8')
st.download_button("Download Leave Plan CSV", csv, f"leave_plan_{year}_{month:02d}.csv")
