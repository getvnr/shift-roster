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
if len(employees) != 14:
    st.error("Please provide exactly 14 employee names to match requirements.")
    st.stop()

# --- Nightshift-Exempt Employees ---
st.subheader("Nightshift-Exempt Employees")
nightshift_exempt = st.multiselect(
    "Select employees who won't work night shifts (no 'N' shifts):",
    options=employees,
    default=[]  # No nightshift-exempt by default, as sample shows all can work N
)

# --- Friday-Saturday Off Employees ---
st.subheader("Friday-Saturday Off Employees")
friday_saturday_off = st.multiselect(
    "Select employees with Friday-Saturday off:",
    options=employees,
    default=["Chaudhari Kaustubh", "Shejal Gawade"]  # Few employees
)

# --- Sunday-Monday Off Employees ---
st.subheader("Sunday-Monday Off Employees")
sunday_monday_off = st.multiselect(
    "Select employees with Sunday-Monday off:",
    options=employees,
    default=["Vivek Kushwaha", "Abdul Mukthiyar Basha"]  # Few employees
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
working_days_per_emp = 20  # Fixed to 20 as per requirement
total_off_days = num_days - working_days_per_emp
st.write(f"Number of working days: {working_days_per_emp} (Total off days: {total_off_days})")

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

weekends = get_specific_days(year, month, [5, 6])  # 5=Saturday, 6=Sunday
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
    def get_available_periods(available_days, min_length, max_length):
        periods = []
        i = 0
        while i < len(available_days):
            start = available_days[i]
            j = i + 1
            while j < len(available_days) and available_days[j] == available_days[j-1] + 1:
                j += 1
            end = available_days[j-1]
            length = end - start + 1
            if length >= min_length:
                for block_len in range(min_length, min(max_length + 1, length + 1)):
                    periods.append((start, start + block_len - 1))
            i = j
        return periods
    
    # Assign N blocks (5N + 2O)
    block_length_n = 7  # 5N + 2O
    for emp in employees:
        if emp in nightshift_exempt:
            debug_info.append(f"{emp}: Skipped (nightshift-exempt)")
            continue
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO']]
        if len(available_days) < block_length_n:
            debug_info.append(f"{emp}: Not enough days for 5N+2O block")
            continue
        periods = get_available_periods(available_days, block_length_n, block_length_n)
        if not periods:
            debug_info.append(f"{emp}: No 7-day consecutive period available for N")
            continue
        # Prioritize periods that cover under-served days
        periods.sort(key=lambda p: sum(1 for d in range(p[0], p[0]+5) if n_shifts_per_day[d] < (3 if (d+1) in weekends or (d+1) in festival_days else 2)), reverse=True)
        if periods:
            start, end = periods[0]
            for i in range(5):
                roster_dict[emp][start + i] = 'N'
                n_shifts_per_day[start + i] += 1
                emp_shift_counts[emp]['N'] += 1
            roster_dict[emp][start + 5] = 'O'
            roster_dict[emp][start + 6] = 'O'
            emp_off_days[emp].extend([start + 5, start + 6])
            emp_off_days[emp] = sorted(set(emp_off_days[emp]))
            debug_info.append(f"{emp}: Assigned 5N+2O block starting day {start + 1}")

    # Assign F blocks (5 F consecutive)
    for emp in employees:
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O']]
        if len(available_days) < 5:
            debug_info.append(f"{emp}: Not enough days for 5F block")
            continue
        periods = get_available_periods(available_days, 5, 6)
        if not periods:
            debug_info.append(f"{emp}: No 5-6 day consecutive period available for F")
            continue
        periods.sort(key=lambda p: sum(1 for d in range(p[0], p[1]+1) if f_shifts_per_day[d] < (3 if (d+1) in weekends or (d+1) in festival_days else 2)), reverse=True)
        if periods:
            start, end = periods[0]
            block_len = min(5, end - start + 1)  # Prefer 5 days
            for i in range(block_len):
                roster_dict[emp][start + i] = 'F'
                f_shifts_per_day[start + i] += 1
                emp_shift_counts[emp]['F'] += 1
            debug_info.append(f"{emp}: Assigned {block_len}F block starting day {start + 1}")

    # Assign S blocks (two 5 S consecutive)
    for emp in employees:
        for block_num in range(2):
            available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O', 'F']]
            if len(available_days) < 5:
                debug_info.append(f"{emp}: Not enough days for S block {block_num + 1}")
                break
            periods = get_available_periods(available_days, 5, 6)
            if not periods:
                debug_info.append(f"{emp}: No 5-6 day consecutive period available for S block {block_num + 1}")
                break
            periods.sort(key=lambda p: sum(1 for d in range(p[0], p[1]+1) if s_shifts_per_day[d] < 2), reverse=True)
            if periods:
                start, end = periods[0]
                block_len = min(5, end - start + 1)  # Prefer 5 days
                for i in range(block_len):
                    roster_dict[emp][start + i] = 'S'
                    s_shifts_per_day[start + i] += 1
                    emp_shift_counts[emp]['S'] += 1
                debug_info.append(f"{emp}: Assigned {block_len}S block {block_num + 1} starting day {start + 1}")

    # Fallback: Assign single shifts to meet coverage and shift counts
    for emp in employees:
        while emp_shift_counts[emp]['N'] < 5:
            available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O', 'F', 'S']]
            if not available_days:
                debug_info.append(f"{emp}: No days left to assign remaining N shifts")
                break
            day = min(available_days, key=lambda d: n_shifts_per_day[d])
            roster_dict[emp][day] = 'N'
            n_shifts_per_day[day] += 1
            emp_shift_counts[emp]['N'] += 1
            debug_info.append(f"{emp}: Assigned single N shift on day {day + 1} to meet 5N requirement")
        
        while emp_shift_counts[emp]['F'] < 5:
            available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O', 'F', 'S']]
            if not available_days:
                debug_info.append(f"{emp}: No days left to assign remaining F shifts")
                break
            day = min(available_days, key=lambda d: f_shifts_per_day[d])
            roster_dict[emp][day] = 'F'
            f_shifts_per_day[day] += 1
            emp_shift_counts[emp]['F'] += 1
            debug_info.append(f"{emp}: Assigned single F shift on day {day + 1} to meet 5F requirement")
        
        while emp_shift_counts[emp]['S'] < 10:
            available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO', 'N', 'O', 'F', 'S']]
            if not available_days:
                debug_info.append(f"{emp}: No days left to assign remaining S shifts")
                break
            day = min(available_days, key=lambda d: s_shifts_per_day[d])
            roster_dict[emp][day] = 'S'
            s_shifts_per_day[day] += 1
            emp_shift_counts[emp]['S'] += 1
            debug_info.append(f"{emp}: Assigned single S shift on day {day + 1} to meet 10S requirement")

    # Ensure total working days <= 20
    for emp in employees:
        for day in range(num_days):
            if (roster_dict[emp][day] in ['F', 'N', 'S'] and 
                emp_shift_counts[emp]['F'] + emp_shift_counts[emp]['S'] + emp_shift_counts[emp]['N'] > 20):
                roster_dict[emp][day] = 'O'
                emp_off_days[emp].append(day)
                if roster_dict[emp][day] == 'F':
                    f_shifts_per_day[day] -= 1
                elif roster_dict[emp][day] == 'N':
                    n_shifts_per_day[day] -= 1
                elif roster_dict[emp][day] == 'S':
                    s_shifts_per_day[day] -= 1
    
    return roster_dict, emp_off_days, debug_info

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, weekends, festival_days, nightshift_exempt, leave_data):
    np.random.seed(42)
    roster_dict = {emp: ['O'] * num_days for emp in employees}
    
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
    
    # Ensure festival days
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_days:
            for emp in employees:
                roster_dict[emp][day] = 'H'
    
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

# Validate night shift blocks
night_shift_issues = []
for emp in employees:
    if emp in nightshift_exempt:
        continue
    consecutive_n = 0
    for day in range(num_days):
        if roster_dict[emp][day] == 'N':
            consecutive_n += 1
            if consecutive_n == 5 and day + 2 < num_days:
                if not (roster_dict[emp][day + 1] == 'O' and roster_dict[emp][day + 2] == 'O'):
                    night_shift_issues.append(f"⚠️ {emp} has 5 night shifts ending on day {day + 1} without 2 consecutive off days")
            elif consecutive_n > 6:
                night_shift_issues.append(f"⚠️ {emp} has {consecutive_n} consecutive night shifts (max 6 allowed)")
        else:
            consecutive_n = 0
    if consecutive_n > 0 and consecutive_n < 4 and not nightshift_exempt:
        night_shift_issues.append(f"⚠️ {emp} has {consecutive_n} consecutive night shifts (min 4, max 6 allowed)")

# Validate shift counts and block lengths
shift_count_issues = []
for emp in employees:
    f_count = sum(1 for d in roster_dict[emp] if d == 'F')
    s_count = sum(1 for d in roster_dict[emp] if d == 'S')
    n_count = sum(1 for d in roster_dict[emp] if d == 'N')
    total_work = f_count + s_count + n_count
    if f_count != 5:
        shift_count_issues.append(f"⚠️ {emp} has {f_count} F shifts (need 5)")
    if s_count != 10:
        shift_count_issues.append(f"⚠️ {emp} has {s_count} S shifts (need 10)")
    if n_count != 5 and emp not in nightshift_exempt:
        shift_count_issues.append(f"⚠️ {emp} has {n_count} N shifts (need 5)")
    if total_work > 20:
        shift_count_issues.append(f"⚠️ {emp} has {total_work} working days (max 20)")

if coverage_issues or night_shift_issues or shift_count_issues:
    if coverage_issues:
        st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
        st.info("To resolve coverage issues, reduce nightshift-exempt employees, Friday-Saturday/Sunday-Monday off assignments, or leaves.")
    if night_shift_issues:
        st.warning("Night Shift Issues:\n" + "\n".join(night_shift_issues))
        st.info("To resolve night shift issues, ensure employees have enough consecutive days available by reducing leaves or off assignments.")
    if shift_count_issues:
        st.warning("Shift Count Issues:\n" + "\n".join(shift_count_issues))
        st.info("To resolve shift count issues, adjust leaves or off assignments to allow 5N, 5F, 10S per employee.")
else:
    st.success("✅ Full 24/7 coverage achieved with all constraints!")

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
