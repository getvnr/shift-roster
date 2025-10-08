import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (October 2025, 14 Employees)")

# --- Employee Input ---
st.subheader("Employee List")
default_employees = [
    "Pousali C", "D Namithananda", "Thorat Yashwant", "Srivastav Nitin",
    "Kishore Khati Vaibhav", "Rupan Venkatesan Anandha", "Chaudhari Kaustubh",
    "Shejal Gawade", "Vivek Kushwaha", "Abdul Mukthiyar Basha", "M Naveen",
    "B Madhurusha", "Chinthalapudi Yaswanth", "Edagotti Kalpana"
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
    default=[]  # No nightshift-exempt by default
)

# --- Friday-Saturday Off Employees ---
st.subheader("Friday-Saturday Off Employees")
friday_saturday_off = st.multiselect(
    "Select employees with Friday-Saturday off:",
    options=employees,
    default=["Chaudhari Kaustubh", "Shejal Gawade"]  # Example few employees
)

# --- Sunday-Monday Off Employees ---
st.subheader("Sunday-Monday Off Employees")
sunday_monday_off = st.multiselect(
    "Select employees with Sunday-Monday off:",
    options=employees,
    default=["Vivek Kushwaha", "Abdul Mukthiyar Basha"]  # Example few employees
)

# Validate no overlap
overlap = set(friday_saturday_off).intersection(sunday_monday_off)
if overlap:
    st.error(f"Employees cannot have both Friday-Saturday and Sunday-Monday off: {', '.join(overlap)}")
    st.stop()

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'), index=9)
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

# --- Working Days ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=20)
total_off_days = num_days - working_days_per_emp

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
sundays_mondays = get_specific_days(year, month, [6, 0])  # 6=Sunday, 0=Monday

# --- Assign Fixed Off Days ---
def assign_fixed_off_days(is_friday_saturday, is_sunday_monday):
    off_days_positions = []
    if is_friday_saturday:
        off_days_positions.extend([d-1 for d in fridays_saturdays])
    if is_sunday_monday:
        off_days_positions.extend([d-1 for d in sundays_mondays])
    return sorted(set(off_days_positions))

# --- Assign Shift Blocks ---
def assign_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, leave_data):
    debug_info = []
    n_shifts_per_day = [0] * num_days
    f_shifts_per_day = [0] * num_days
    s_shifts_per_day = [0] * num_days
    emp_off_days = {emp: assign_fixed_off_days(emp in friday_saturday_off, emp in sunday_monday_off) for emp in employees}
    emp_shift_counts = {emp: {'F': 0, 'S': 0, 'N': 0} for emp in employees}
    
    # Function to get available consecutive periods
    def get_available_periods(available_days, min_length):
        periods = []
        start = available_days[0]
        for i in range(1, len(available_days)):
            if available_days[i] != available_days[i-1] + 1:
                if available_days[i-1] - start + 1 >= min_length:
                    periods.append((start, available_days[i-1]))
                start = available_days[i]
        if available_days[-1] - start + 1 >= min_length:
            periods.append((start, available_days[-1]))
        return periods
    
    # Assign N blocks (5N + 2O)
    block_length = 7
    for idx, emp in enumerate(employees):
        if emp in nightshift_exempt:
            debug_info.append(f"{emp}: Skipped (nightshift-exempt)")
            continue
        # Available days (not fixed off, not leave/H/CO)
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO']]
        if len(available_days) < block_length:
            debug_info.append(f"{emp}: Not enough days for 5N+2O block")
            continue
        # Find valid periods for N block
        periods = get_available_periods(available_days, block_length)
        if not periods:
            debug_info.append(f"{emp}: No 7-day consecutive period available for N")
            continue
        # Choose start day, staggered by employee index
        period = periods[idx % len(periods)]
        start_day = period[0]
        for i in range(5):
            roster_dict[emp][start_day + i] = 'N'
            n_shifts_per_day[start_day + i] += 1
            emp_shift_counts[emp]['N'] += 1
        roster_dict[emp][start_day + 5] = 'O'
        roster_dict[emp][start_day + 6] = 'O'
        emp_off_days[emp].extend([start_day + 5, start_day + 6])
        emp_off_days[emp] = sorted(set(emp_off_days[emp]))
        debug_info.append(f"{emp}: Assigned 5N+2O block starting day {start_day + 1}")

    # Assign F blocks (5 F consecutive)
    for idx, emp in enumerate(employees):
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O']]
        if len(available_days) < 5:
            debug_info.append(f"{emp}: Not enough days for 5F block")
            continue
        periods = get_available_periods(available_days, 5)
        if not periods:
            debug_info.append(f"{emp}: No 5-day consecutive period available for F")
            continue
        period = periods[idx % len(periods)]
        start_day = period[0]
        for i in range(5):
            roster_dict[emp][start_day + i] = 'F'
            f_shifts_per_day[start_day + i] += 1
            emp_shift_counts[emp]['F'] += 1
        debug_info.append(f"{emp}: Assigned 5F block starting day {start_day + 1}")

    # Assign S blocks (two 5 S consecutive)
    for idx, emp in enumerate(employees):
        for block_num in range(2):
            available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O', 'F']]
            if len(available_days) < 5:
                debug_info.append(f"{emp}: Not enough days for S block {block_num + 1}")
                break
            periods = get_available_periods(available_days, 5)
            if not periods:
                debug_info.append(f"{emp}: No 5-day consecutive period available for S block {block_num + 1}")
                break
            period = periods[(idx + block_num) % len(periods)]
            start_day = period[0]
            for i in range(5):
                roster_dict[emp][start_day + i] = 'S'
                s_shifts_per_day[start_day + i] += 1
                emp_shift_counts[emp]['S'] += 1
            debug_info.append(f"{emp}: Assigned 5S block {block_num + 1} starting day {start_day + 1}")

    # Assign remaining available days to O
    for emp in employees:
        for day in range(num_days):
            if roster_dict[emp][day] == 'S' and emp_shift_counts[emp]['F'] + emp_shift_counts[emp]['S'] + emp_shift_counts[emp]['N'] > 20:
                roster_dict[emp][day] = 'O'
                emp_off_days[emp].append(day)
    
    return roster_dict, emp_off_days, debug_info

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, weekends, festival_days, nightshift_exempt, leave_data):
    np.random.seed(42)
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    
    # Apply leaves first
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
    
    # Assign shift blocks
    roster_dict, emp_off_days, debug_info = assign_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, leave_data)
    
    # Display debug info
    st.subheader("Shift Assignment Debug Info")
    st.text("\n".join(debug_info))
    
    for day in range(num_days):
        day_num = day + 1
        is_festival = day_num in festival_days
        is_weekend = day_num in weekends
        is_special = is_weekend or is_festival
        
        # Festival: All H
        if is_festival:
            for emp in employees:
                roster_dict[emp][day] = 'H'
            continue
        
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekends, festival_days, nightshift_exempt, leave_data)

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    is_special = day_num in weekends or day_num in festival_days
    min_f = 3 if is_special else 2
    min_n = 3 if is_special else 2
    min_s = 2
    
    if f_count < min_f or n_count < min_n or s_count < min_s:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count} F, {n_count} N, {s_count} S (need {min_f} F, {min_n} N, {min_s} S)")

if coverage_issues:
    st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
    st.info("To resolve coverage issues, adjust off groups or leaves to ensure enough available staff on weekends.")
else:
    st.success("✅ Full 24/7 coverage achieved!")

# --- Color Coding ---
def color_shifts(val):
    colors = {'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple'}
    return f'background-color: {colors.get(val, "")}'

# --- Display Roster ---
st.subheader("Generated Roster")
roster = pd.DataFrame(roster_dict, index=dates).T
st.dataframe(roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary_data = {shift: [sum(1 for s in roster_dict[emp] if s == shift) for emp in employees] for shift in ['F', 'N', 'S', 'O', 'L', 'H', 'CO']}
summary = pd.DataFrame(summary_data, index=employees)
st.dataframe(summary)

# --- Download ---
csv = roster.to_csv().encode('utf-8')
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv")
