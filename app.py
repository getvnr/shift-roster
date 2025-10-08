import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import uuid

# Set page configuration
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (13 Employees, Weekend Week-offs)")

# --- Employee Input ---
st.subheader("Employee List")
default_employees = [
    "Pousali C", "Thorat Yashwant", "Srivastav Nitin", "Kishore Khati Vaibhav",
    "Rupan Venkatesan Anandha", "Chaudhari Kaustubh", "Shejal Gawade", "Vivek Kushwaha",
    "Abdul Mukthiyar Basha", "M Naveen", "B Madhurusha", "Chinthalapudi Yaswanth", "Edagotti Kalpana"
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
    default=[]
)

# --- Weekend Week-off Groups ---
st.subheader("Weekend Week-off Preferences")
st.info("Weekend week-offs will be assigned as Saturday-Sunday off days. Number of weekends: {} for the selected month.".format(4))  # Placeholder, calculate dynamically below

tab1, tab2, tab3 = st.tabs(["Saturday-Sunday Off", "Friday-Saturday Off", "Sunday-Monday Off"])

with tab1:
    saturday_sunday_off = st.multiselect(
        "Select employees with Saturday-Sunday week-offs ({} weekends):".format(4),
        options=employees,
        default=employees,  # Default all to Saturday-Sunday
        key="saturday_sunday_off"
    )

with tab2:
    friday_saturday_off = st.multiselect(
        "Select employees with Friday-Saturday week-offs:",
        options=employees,
        default=[],
        key="friday_saturday_off"
    )

with tab3:
    sunday_monday_off = st.multiselect(
        "Select employees with Sunday-Monday week-offs:",
        options=employees,
        default=[],
        key="sunday_monday_off"
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
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]

# Calculate number of weekends
saturdays = [day for day in range(1, num_days + 1) if weekday(year, month, day) == 5]
sundays = [day for day in range(1, num_days + 1) if weekday(year, month, day) == 6]
num_weekends = len(saturdays)  # 5 for November 2025
st.info(f"Number of weekends (Sat-Sun pairs) in {pd.Timestamp(year, month, 1).strftime('%B %Y')}: {num_weekends}")

# --- Working Days ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=15, max_value=num_days, value=20)
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

# --- Assign Off Days with Weekend Week-offs ---
def assign_off_days(num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, is_friday_saturday, is_sunday_monday, is_saturday_sunday, leave_data, emp, num_weekends):
    total_off = num_days - working_days
    off_days_positions = []
    
    # Assign preferred weekend week-offs (2 days per weekend)
    if is_saturday_sunday:
        for i in range(num_weekends):
            sat = saturdays[i] - 1  # 0-indexed
            sun = sundays[i] - 1
            if sat < num_days and sun < num_days:
                off_days_positions.extend([sat, sun])
    elif is_friday_saturday:
        off_days_positions.extend([d-1 for d in fridays_saturdays if d not in festival_days and d not in leave_data.get(emp, {})])
    elif is_sunday_monday:
        off_days_positions.extend([d-1 for d in sundays_mondays if d not in festival_days and d not in leave_data.get(emp, {})])
    
    # Remove duplicates and ensure no overlap with festivals/leaves
    off_days_positions = sorted(set(off_days_positions))
    
    remaining_off = total_off - len(off_days_positions)
    if remaining_off < 0:
        return off_days_positions[:total_off]
    
    # Distribute remaining off days in 2-day blocks after every 5 working days
    available_days = [d for d in range(num_days) if d not in off_days_positions and d+1 not in festival_days and d+1 not in leave_data.get(emp, {})]
    cycle_length = 7  # 5 working + 2 off
    num_cycles = remaining_off // 2
    for cycle in range(num_cycles):
        start = cycle * cycle_length + 5
        if start + 1 < num_days and start in available_days and start + 1 in available_days:
            off_days_positions.extend([start, start + 1])
            available_days.remove(start)
            available_days.remove(start + 1)
    
    remaining_off = total_off - len(off_days_positions)
    if remaining_off > 0:
        available_days = sorted(available_days)
        for i in range(0, remaining_off, 2):
            if i + 1 < len(available_days):
                off_days_positions.extend([available_days[i], available_days[i + 1]])
    
    return sorted(set(off_days_positions))

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data, num_weekends):
    np.random.seed(42)
    roster_dict = {emp: [''] * num_days for emp in employees}
    shift_counts = {emp: {'F': 0, 'N': 0, 'S': 0, 'O': 0, 'L': 0, 'H': 0, 'CO': 0} for emp in employees}
    target_f = 5
    target_n = 5
    target_s_min = 5
    target_s_max = 10
    
    # Pre-assign off days and leaves
    emp_off_days = {}
    for emp in employees:
        is_friday_saturday = emp in friday_saturday_off
        is_sunday_monday = emp in sunday_monday_off
        is_saturday_sunday = emp in saturday_sunday_off
        emp_off_days[emp] = assign_off_days(num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, is_friday_saturday, is_sunday_monday, is_saturday_sunday, leave_data, emp, num_weekends)
        for day in emp_off_days[emp]:
            roster_dict[emp][day] = 'O'
            shift_counts[emp]['O'] += 1
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
                shift_counts[emp][code] += 1
    
    # Ensure enough employees per day
    for day in range(num_days):
        if day + 1 in festival_days:
            continue
        available_count = sum(1 for emp in employees if roster_dict[emp][day] not in ['O', 'L', 'H', 'CO'])
        if available_count < 7:  # Need at least 7 for 2F+3S+2N
            # Reassign off days if possible
            off_emps = [emp for emp in employees if roster_dict[emp][day] == 'O']
            np.random.shuffle(off_emps)
            for emp in off_emps[:7 - available_count]:
                # Find another day to move off to
                other_days = [d for d in range(num_days) if roster_dict[emp][d] == '' and d + 1 not in festival_days]
                if other_days:
                    new_day = np.random.choice(other_days)
                    roster_dict[emp][new_day] = 'O'
                    roster_dict[emp][day] = ''
    
    # Assign F and N shifts in 5-day blocks
    for emp in employees:
        available_days = sorted([d for d in range(num_days) if roster_dict[emp][d] == '' and d+1 not in festival_days])
        if not available_days:
            continue
        
        # Assign F shifts (5 in one block)
        if shift_counts[emp]['F'] < target_f:
            block_size = 5
            start_idx = np.random.randint(0, max(1, len(available_days) - block_size + 1))
            f_days = available_days[start_idx:start_idx + block_size]
            for day in f_days:
                f_count_day = sum(1 for e in employees if roster_dict[e][day] == 'F')
                if f_count_day < 5 and shift_counts[emp]['F'] < target_f:
                    roster_dict[emp][day] = 'F'
                    shift_counts[emp]['F'] += 1
        
        # Update available_days
        available_days = [d for d in available_days if roster_dict[emp][d] == '']
        
        # Assign N shifts (5 in one block)
        if emp not in nightshift_exempt and shift_counts[emp]['N'] < target_n:
            block_size = 5
            start_idx = np.random.randint(0, max(1, len(available_days) - block_size + 1))
            n_days = available_days[start_idx:start_idx + block_size]
            for day in n_days:
                if day >= 5 and sum(1 for d in range(day-4, day) if roster_dict[emp][d] == 'N') == 5:
                    continue
                n_count_day = sum(1 for e in employees if roster_dict[e][day] == 'N')
                if n_count_day < 3 and shift_counts[emp]['N'] < target_n:
                    roster_dict[emp][day] = 'N'
                    shift_counts[emp]['N'] += 1
    
    # Assign S shifts in 4–5 day blocks
    for emp in employees:
        available_days = sorted([d for d in range(num_days) if roster_dict[emp][d] == '' and d+1 not in festival_days])
        if not available_days:
            continue
        
        s_to_assign = min(target_s_max - shift_counts[emp]['S'], len(available_days))
        s_to_assign = max(s_to_assign, target_s_min - shift_counts[emp]['S'])
        
        while s_to_assign > 0 and available_days:
            block_size = np.random.choice([4, 5])
            block_size = min(block_size, s_to_assign, len(available_days))
            start_idx = np.random.randint(0, len(available_days) - block_size + 1)
            s_days = available_days[start_idx:start_idx + block_size]
            for day in s_days:
                s_count_day = sum(1 for e in employees if roster_dict[e][day] == 'S')
                if s_count_day < 5 and shift_counts[emp]['S'] < target_s_max:
                    roster_dict[emp][day] = 'S'
                    shift_counts[emp]['S'] += 1
                    s_to_assign -= 1
            available_days = [d for d in available_days if roster_dict[emp][d] == '']
    
    # Ensure daily coverage
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_days:
            for emp in employees:
                if roster_dict[emp][day] == '':
                    roster_dict[emp][day] = 'H'
                    shift_counts[emp]['H'] += 1
            continue
        
        min_f = 2
        min_n = 2
        min_s = 3
        
        f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
        n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
        s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
        
        available_emps = [emp for emp in employees if roster_dict[emp][day] == '']
        
        # Fix shortages
        # Prioritize F
        available_emps_f = sorted(available_emps, key=lambda emp: shift_counts[emp]['F'])
        for emp in available_emps_f:
            if f_count < min_f and shift_counts[emp]['F'] < target_f:
                roster_dict[emp][day] = 'F'
                shift_counts[emp]['F'] += 1
                f_count += 1
                available_emps.remove(emp)
        
        # Prioritize N
        non_exempt_available = [emp for emp in available_emps if emp not in nightshift_exempt]
        non_exempt_available = sorted(non_exempt_available, key=lambda emp: shift_counts[emp]['N'])
        for emp in non_exempt_available:
            if n_count < min_n and shift_counts[emp]['N'] < target_n:
                roster_dict[emp][day] = 'N'
                shift_counts[emp]['N'] += 1
                n_count += 1
                available_emps.remove(emp)
        
        # Prioritize S
        available_emps_s = sorted(available_emps, key=lambda emp: shift_counts[emp]['S'])
        for emp in available_emps_s:
            if s_count < min_s and shift_counts[emp]['S'] < target_s_max:
                roster_dict[emp][day] = 'S'
                shift_counts[emp]['S'] += 1
                s_count += 1
                available_emps.remove(emp)
        
        # Assign remaining
        for emp in available_emps:
            if shift_counts[emp]['S'] < target_s_max:
                roster_dict[emp][day] = 'S'
                shift_counts[emp]['S'] += 1
    
    return roster_dict, shift_counts

# --- Generate Roster ---
roster_dict, shift_counts = assign_shifts(employees, num_days, working_days_per_emp, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data, num_weekends)

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    is_festival = day_num in festival_days
    min_f = 0 if is_festival else 2
    min_n = 0 if is_festival else 2
    min_s = 0 if is_festival else 3
    
    if f_count < min_f or n_count < min_n or s_count < min_s:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count} F, {n_count} N, {s_count} S (need {min_f} F, {min_n} N, {min_s} S)")

# Validate shift counts and consecutive night shifts
shift_count_issues = []
night_shift_issues = []
for emp in employees:
    if shift_counts[emp]['F'] != 5:
        shift_count_issues.append(f"⚠️ {emp} has {shift_counts[emp]['F']} F shifts (target 5)")
    if emp not in nightshift_exempt and shift_counts[emp]['N'] != 5:
        shift_count_issues.append(f"⚠️ {emp} has {shift_counts[emp]['N']} N shifts (target 5)")
    if not (5 <= shift_counts[emp]['S'] <= 10):
        shift_count_issues.append(f"⚠️ {emp} has {shift_counts[emp]['S']} S shifts (target 5-10)")
    
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

if coverage_issues or shift_count_issues or night_shift_issues:
    if coverage_issues:
        st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
    if shift_count_issues:
        st.warning("Shift Count Issues:\n" + "\n".join(shift_count_issues))
    if night_shift_issues:
        st.warning("Night Shift Issues:\n" + "\n".join(night_shift_issues))
else:
    st.success("✅ Full 24/7 coverage achieved with target shift counts and weekend week-offs!")

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

# --- Download Roster ---
csv = roster.to_csv().encode('utf-8')
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv")
