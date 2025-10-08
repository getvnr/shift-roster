import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import uuid

# Set page configuration
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (13 Employees, Full Coverage)")

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

# --- Week-off Groups ---
st.subheader("Week-off Preferences")
tab1, tab2, tab3 = st.tabs(["Friday-Saturday Off", "Sunday-Monday Off", "Saturday-Sunday Off"])

with tab1:
    friday_saturday_off = st.multiselect(
        "Select employees with Friday-Saturday week-offs:",
        options=employees,
        default=[],
        key="friday_saturday_off"
    )

with tab2:
    sunday_monday_off = st.multiselect(
        "Select employees with Sunday-Monday week-offs:",
        options=employees,
        default=[],
        key="sunday_monday_off"
    )

with tab3:
    saturday_sunday_off = st.multiselect(
        "Select employees with Saturday-Sunday week-offs:",
        options=employees,
        default=[],
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
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]

# --- Working Days ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=22)
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
    
    # Assign preferred week-offs
    if is_friday_saturday:
        off_days_positions.extend([d-1 for d in fridays_saturdays])
    elif is_sunday_monday:
        off_days_positions.extend([d-1 for d in sundays_mondays])
    elif is_saturday_sunday:
        off_days_positions.extend([d-1 for d in saturdays_sundays])
    
    remaining_off = total_off - len(off_days_positions)
    if remaining_off < 0:
        return off_days_positions[:total_off]
    
    # Distribute remaining off days to avoid clustering
    available_days = [d for d in range(num_days) if d not in off_days_positions]
    if remaining_off > 0:
        off_days_positions.extend(np.random.choice(available_days, size=remaining_off, replace=False))
    
    return sorted(set(off_days_positions))

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data):
    np.random.seed(42)
    roster_dict = {emp: [''] * num_days for emp in employees}
    shift_counts = {emp: {'F': 0, 'N': 0, 'S': 0, 'O': 0, 'L': 0, 'H': 0, 'CO': 0} for emp in employees}
    
    # Pre-assign off days, ensuring enough employees are available
    emp_off_days = {}
    for emp in employees:
        is_friday_saturday = emp in friday_saturday_off
        is_sunday_monday = emp in sunday_monday_off
        is_saturday_sunday = emp in saturday_sunday_off
        emp_off_days[emp] = assign_off_days(num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, is_friday_saturday, is_sunday_monday, is_saturday_sunday)
    
    # Check if off days allow enough employees per day
    for day in range(num_days):
        if day + 1 in festival_days:
            continue
        available_count = sum(1 for emp in employees if day not in emp_off_days[emp] and (day+1 not in leave_data.get(emp, {})))
        if available_count < 8:
            # Redistribute off days
            excess_offs = 8 - available_count
            off_employees = [emp for emp in employees if day in emp_off_days[emp]]
            np.random.shuffle(off_employees)
            for emp in off_employees[:excess_offs]:
                emp_off_days[emp].remove(day)
                # Reassign off day to another day
                available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and d+1 not in festival_days and d+1 not in leave_data.get(emp, {})]
                if available_days:
                    new_off = np.random.choice(available_days)
                    emp_off_days[emp].append(new_off)
                    emp_off_days[emp] = sorted(set(emp_off_days[emp]))
    
    # Apply off days
    for emp in employees:
        for day in emp_off_days[emp]:
            roster_dict[emp][day] = 'O'
            shift_counts[emp]['O'] += 1
    
    # Apply leaves
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
                shift_counts[emp][code] += 1
    
    # Assign shifts for each day
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_days:
            for emp in employees:
                roster_dict[emp][day] = 'H'
                shift_counts[emp]['H'] += 1
            continue
        
        # Minimum shift requirements
        min_f = 3  # Morning (F only, no G1 employees)
        min_n = 2  # Night
        min_s = 3  # Second
        
        # Available employees
        available_emps = [emp for emp in employees if roster_dict[emp][day] == '']
        
        # Assign Night shifts (N)
        non_exempt_available = [emp for emp in available_emps if emp not in nightshift_exempt]
        non_exempt_available.sort(key=lambda emp: (shift_counts[emp]['N'], np.random.random()))
        n_count = 0
        for emp in non_exempt_available:
            if n_count < min_n:
                if day >= 5:
                    if all(roster_dict[emp][d] == 'N' for d in range(day-5, day)):
                        continue
                roster_dict[emp][day] = 'N'
                shift_counts[emp]['N'] += 1
                n_count += 1
                available_emps.remove(emp)
        
        # If night shifts are short, reassign from S or F
        if n_count < min_n:
            reassign_emps = [emp for emp in employees if roster_dict[emp][day] == 'S' and emp not in nightshift_exempt]
            reassign_emps.sort(key=lambda emp: (shift_counts[emp]['N'], np.random.random()))
            for emp in reassign_emps:
                if n_count < min_n:
                    if day >= 5 and all(roster_dict[emp][d] == 'N' for d in range(day-5, day)):
                        continue
                    roster_dict[emp][day] = 'N'
                    shift_counts[emp]['N'] += 1
                    shift_counts[emp]['S'] -= 1
                    n_count += 1
        
        # Assign Morning shifts (F)
        available_emps.sort(key=lambda emp: (shift_counts[emp]['F'], np.random.random()))
        f_count = 0
        for emp in available_emps:
            if f_count < min_f:
                roster_dict[emp][day] = 'F'
                shift_counts[emp]['F'] += 1
                f_count += 1
                available_emps.remove(emp)
        
        # If morning shifts are short, reassign from S
        if f_count < min_f:
            reassign_emps = [emp for emp in employees if roster_dict[emp][day] == 'S']
            reassign_emps.sort(key=lambda emp: (shift_counts[emp]['F'], np.random.random()))
            for emp in reassign_emps:
                if f_count < min_f:
                    roster_dict[emp][day] = 'F'
                    shift_counts[emp]['F'] += 1
                    shift_counts[emp]['S'] -= 1
                    f_count += 1
        
        # Assign Second shifts (S)
        available_emps.sort(key=lambda emp: (shift_counts[emp]['S'], np.random.random()))
        s_count = 0
        for emp in available_emps:
            if s_count < min_s:
                roster_dict[emp][day] = 'S'
                shift_counts[emp]['S'] += 1
                s_count += 1
                available_emps.remove(emp)
        
        # Assign remaining as S
        for emp in available_emps:
            roster_dict[emp][day] = 'S'
            shift_counts[emp]['S'] += 1
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data)

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    is_festival = day_num in festival_days
    min_f = 0 if is_festival else 3
    min_n = 0 if is_festival else 2
    min_s = 0 if is_festival else 3
    
    if f_count < min_f or n_count < min_n or s_count < min_s:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count} F, {n_count} N, {s_count} S (need {min_f} F, {min_n} N, {min_s} S)")

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
    st.success("✅ Full 24/7 coverage achieved with balanced shifts!")

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
