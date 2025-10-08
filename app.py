import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import uuid

# Set page configuration
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Updated Shift Minimums)")

# --- Employee Input ---
st.subheader("Employee List")
default_employees = [
    "Ramesh Polisetty", "Ajay Chidipotu", "Srinivasu Cheedalla", "Imran Khan",
    "Sammeta Balachander", "Muppa Divya", "Anil Athkuri", "Gangavarapu Suneetha",
    "Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan", "Lakshmi Narayana Rao",
    "Gayatri Ruttala", "Pousali C", "D Namithananda", "Thorat Yashwant",
    "Srivastav Nitin", "Kishore Khati Vaibhav", "Rupan Venkatesan Anandha",
    "Chaudhari Kaustubh", "Shejal Gawade", "Vivek Kushwaha", "Abdul Mukthiyar Basha",
    "M Naveen", "B Madhurusha", "Chinthalapudi Yaswanth", "Edagotti Kalpana"
]
employees = st.text_area("Enter employee names (comma separated):", value=", ".join(default_employees))
employees = [e.strip() for e in employees.split(",") if e.strip()]
if not employees:
    st.error("Please provide at least one employee name.")
    st.stop()

# --- Nightshift-Exempt Employees ---
st.subheader("Nightshift-Exempt Employees")
nightshift_exempt = st.multiselect(
    "Select employees who won't work night shifts (no 'N' shifts):",
    options=employees,
    default=["Ramesh Polisetty", "Srinivasu Cheedalla"]
)

# --- Week-off Groups ---
st.subheader("Week-off Preferences")
tab1, tab2, tab3 = st.tabs(["Friday-Saturday Off", "Sunday-Monday Off", "Saturday-Sunday Off"])

with tab1:
    friday_saturday_off = st.multiselect(
        "Select employees with Friday-Saturday week-offs:",
        options=employees,
        default=["Gangavarapu Suneetha", "Lakshmi Narayana Rao"],
        key="friday_saturday_off"
    )

with tab2:
    sunday_monday_off = st.multiselect(
        "Select employees with Sunday-Monday week-offs:",
        options=employees,
        default=["Ajay Chidipotu", "Imran Khan"],
        key="sunday_monday_off"
    )

with tab3:
    saturday_sunday_off = st.multiselect(
        "Select employees with Saturday-Sunday week-offs:",
        options=employees,
        default=["Muppa Divya", "Anil Athkuri"],
        key="saturday_sunday_off"
    )

# Validate no employee is in multiple week-off groups
weekoff_groups = [friday_saturday_off, sunday_monday_off, saturday_sunday_off]
group_names = ["Friday-Saturday", "Sunday-Monday", "Saturday-Sunday"]
overlap_issues = []
for i in range(len(weekoff_groups)):
    for j in range(i + 1, len(weekoff_groups)):
        overlap = set(weekoff_groups[i]).intersection(set(weekoff_groups[j]))
        if overlap:
            overlap_issues.append(f"Employees in both {group_names[i]} and {group_names[j]}: {', '.join(overlap)}")
if overlap_issues:
    st.error("\n".join(overlap_issues))
    st.stop()

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), index=10, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month:02d}-{year}" for day in range(1, num_days+1)]

# --- Working Days ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
total_off_days = num_days - working_days_per_emp
if total_off_days < 0:
    st.error("Working days cannot exceed the number of days in the month.")
    st.stop()

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days:", options=list(range(1, num_days+1)), default=[2])

# --- Leaves / Special Codes ---
st.subheader("Add Employee Leaves or Special Codes")
leave_data = {}
for emp in employees:
    st.write(f"{emp} Leaves/Special Codes")
    cols = st.columns(3)
    with cols[0]:
        leave_days = st.multiselect(f"Leave/Special Days for {emp}:", options=list(range(1, num_days+1)), key=f"leave_{emp}")
    with cols[1]:
        codes = [''] * len(leave_days)
        for i in range(len(leave_days)):
            codes[i] = st.selectbox(f"Code for day {leave_days[i]}:", ['L', 'H', 'CO'], key=f"code_{emp}_{i}")
    leave_data[emp] = dict(zip(leave_days, codes))

# --- Get Specific Days ---
def get_specific_days(year, month, target_days):
    days = []
    for day in range(1, monthrange(year, month)[1]+1):
        if weekday(year, month, day) in target_days:
            days.append(day)
    return days

fridays_saturdays = get_specific_days(year, month, [4, 5])  # 4=Friday, 5=Saturday
sundays_mondays = get_specific_days(year, month, [6, 0])    # 6=Sunday, 0=Monday
saturdays_sundays = get_specific_days(year, month, [5, 6])  # 5=Saturday, 6=Sunday

# --- Assign Off Days ---
def assign_off_days(num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, is_friday_saturday, is_sunday_monday, is_saturday_sunday):
    total_off = num_days - working_days
    off_days_positions = []
    
    if is_friday_saturday:
        off_days_positions.extend([d-1 for d in fridays_saturdays])
    elif is_sunday_monday:
        off_days_positions.extend([d-1 for d in sundays_mondays])
    elif is_saturday_sunday:
        off_days_positions.extend([d-1 for d in saturdays_sundays])
    
    remaining_off = total_off - len(off_days_positions)
    if remaining_off < 0:
        return off_days_positions
    
    cycle_length = 7  # 5 working + 2 off
    num_cycles = remaining_off // 2
    for cycle in range(num_cycles):
        start = cycle * cycle_length + 5
        if start + 1 < num_days:
            off_days_positions.extend([start, start + 1])
    
    if remaining_off % 2 == 1 and len(off_days_positions) + 1 < num_days:
        last_off = min(num_days - 1, off_days_positions[-1] + cycle_length + 1 if off_days_positions else 5)
        off_days_positions.append(last_off)
    
    return sorted(set(off_days_positions))

# --- Assign Night Shifts in Blocks ---
def assign_night_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, emp_off_days):
    max_night_shifts = 5
    for emp in employees:
        if emp in nightshift_exempt:
            continue
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO']]
        if not available_days:
            continue
        num_nights = min(np.random.randint(1, max_night_shifts + 1), len(available_days))
        start_idx = np.random.choice([i for i in range(len(available_days) - num_nights + 1)])
        night_days = available_days[start_idx:start_idx + num_nights]
        for day in night_days:
            roster_dict[emp][day] = 'N'
    return roster_dict

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data):
    np.random.seed(42)
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    
    # Pre-assign off days
    emp_off_days = {}
    g1_employees = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
    for emp in employees:
        is_friday_saturday = emp in friday_saturday_off
        is_sunday_monday = emp in sunday_monday_off
        is_saturday_sunday = emp in saturday_sunday_off
        emp_off_days[emp] = assign_off_days(num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, is_friday_saturday, is_sunday_monday, is_saturday_sunday)
    
    # Apply leaves first
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
    
    # Pre-assign night shifts in blocks
    roster_dict = assign_night_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, emp_off_days)
    
    for day in range(num_days):
        day_num = day + 1
        is_festival = day_num in festival_days
        is_special = day_num in fridays_saturdays or day_num in sundays_mondays or day_num in saturdays_sundays or is_festival
        
        # Festival: All H
        if is_festival:
            for emp in employees:
                roster_dict[emp][day] = 'H'
            continue
        
        # Coverage requirements
        min_fg1 = 3  # Minimum F or G1 (Morning)
        min_n = 2   # Minimum N (Night)
        min_s = 3   # Minimum S (Second)
        
        # Available employees
        available_emps = [emp for emp in employees 
                         if day not in emp_off_days[emp] 
                         and roster_dict[emp][day] not in ['L', 'H', 'CO', 'O']]
        
        # Count current shifts
        f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
        g1_count = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
        n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
        s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
        
        # Ensure minimum night shifts
        non_exempt_available = [emp for emp in available_emps if emp not in nightshift_exempt]
        np.random.shuffle(non_exempt_available)
        for emp in non_exempt_available:
            if n_count < min_n and roster_dict[emp][day] not in ['F', 'G1', 'S']:
                roster_dict[emp][day] = 'N'
                n_count += 1
                if emp in available_emps:
                    available_emps.remove(emp)
        
        # Assign G1 to eligible employees
        g1_available = [emp for emp in available_emps if emp in g1_employees]
        np.random.shuffle(g1_available)
        for emp in g1_available:
            if f_count + g1_count < min_fg1:
                roster_dict[emp][day] = 'G1'
                g1_count += 1
                if emp in available_emps:
                    available_emps.remove(emp)
        
        # Assign F to meet min_fg1
        np.random.shuffle(available_emps)
        for emp in available_emps:
            if f_count + g1_count < min_fg1:
                roster_dict[emp][day] = 'F'
                f_count += 1
                if emp in available_emps:
                    available_emps.remove(emp)
            else:
                break
        
        # Assign S to meet min_s
        np.random.shuffle(available_emps)
        for emp in available_emps:
            if s_count < min_s:
                roster_dict[emp][day] = 'S'
                s_count += 1
                if emp in available_emps:
                    available_emps.remove(emp)
            else:
                break
        
        # Apply off days
        for emp in employees:
            if day in emp_off_days[emp]:
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data)

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    g1_count = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    is_festival = day_num in festival_days
    min_fg1 = 0 if is_festival else 3
    min_n = 0 if is_festival else 2
    min_s = 0 if is_festival else 3
    
    if f_count + g1_count < min_fg1 or n_count < min_n or s_count < min_s:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count + g1_count} F/G1, {n_count} N, {s_count} S (need {min_fg1} F/G1, {min_n} N, {min_s} S)")

# Validate maximum 5 consecutive night shifts
night_shift_issues = []
for emp in employees:
    if emp in nightshift_exempt:
        continue
    consecutive_n = 0
    max_consecutive_n = 0
    for day in range(num_days):
        if roster_dict[emp][day] == 'N':
            consecutive_n += 1
            max_consecutive_n = max(max_consecutive_n, consecutive_n)
        else:
            consecutive_n = 0
    if max_consecutive_n > 5:
        night_shift_issues.append(f"⚠️ {emp} has {max_consecutive_n} consecutive night shifts (max 5 allowed)")

if coverage_issues or night_shift_issues:
    if coverage_issues:
        st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
    if night_shift_issues:
        st.warning("Night Shift Issues:\n" + "\n".join(night_shift_issues))
else:
    st.success("✅ Full 24/7 coverage achieved with updated shift constraints!")

# --- Color Coding ---
def color_shifts(val):
    colors = {'G1': 'limegreen', 'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple'}
    return f'background-color: {colors.get(val, "")}'

# --- Display Roster ---
st.subheader("Generated Roster")
roster = pd.DataFrame(roster_dict, index=dates).T
st.dataframe(roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary_data = {shift: [sum(1 for s in roster_dict[emp] if s == shift) for emp in employees] for shift in ['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO']}
summary = pd.DataFrame(summary_data, index=employees)
st.dataframe(summary)

# --- Download Roster ---
csv = roster.to_csv().encode('utf-8')
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv")
