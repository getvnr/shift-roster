import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import math

# Set page configuration
st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Balanced Shifts)")

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
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]

# --- Working Days ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
total_off_days = num_days - working_days_per_emp
if total_off_days < 0:
    st.error("Working days cannot exceed the number of days in the month.")
    st.stop()

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days (day numbers):", options=list(range(1, num_days+1)), default=[2])

# --- Leaves / Special Codes ---
st.subheader("Add Employee Leaves or Special Codes")
leave_data = {}
for emp in employees:
    st.write(f"{emp} Leaves/Special Codes")
    cols = st.columns(3)
    with cols[0]:
        leave_days = st.multiselect(f"Leave/Special Days for {emp} (day numbers):", options=list(range(1, num_days+1)), key=f"leave_{emp}")
    with cols[1]:
        # Allow each selected day to be assigned one code
        codes = {}
        for d in leave_days:
            codes[d] = st.selectbox(f"Code for {emp} day {d}:", ['', 'L', 'H', 'CO'], key=f"code_{emp}_{d}")
    # store only days which have codes ('' means no code)
    leave_data[emp] = {d: codes[d] for d in leave_days if codes.get(d)}

# --- Helper: get specific weekdays in month ---
def get_specific_days(year, month, target_weekday_indices):
    """Return list of day numbers in the month where weekday() is in target_weekday_indices.
       weekday: Monday=0 ... Sunday=6"""
    days = []
    for day in range(1, monthrange(year, month)[1] + 1):
        if weekday(year, month, day) in target_weekday_indices:
            days.append(day)
    return days

fridays_saturdays = get_specific_days(year, month, [4, 5])  # 4=Friday,5=Saturday
sundays_mondays = get_specific_days(year, month, [6, 0])    # 6=Sunday,0=Monday
saturdays_sundays = get_specific_days(year, month, [5, 6])  # 5=Saturday,6=Sunday

# --- Assign Off Days (improved) ---
def assign_off_days_for_emp(num_days, total_off_needed, weekoff_days_for_emp):
    """
    weekoff_days_for_emp: list of day numbers (1-based) that MUST be off for this employee (from selected week-off group).
    Returns list of 0-based indices to mark as 'O' for this employee.
    Ensures exactly total_off_needed off-days (if possible) by adding evenly-distributed off days.
    """
    off_set = set(d-1 for d in weekoff_days_for_emp)  # convert to 0-based
    # If already more off days than needed, trim from the end
    if len(off_set) >= total_off_needed:
        return sorted(list(off_set))[:total_off_needed]
    remaining = total_off_needed - len(off_set)
    # spread remaining off days across the month avoiding festival-like collisions (handled later)
    # Choose candidate days that are not already weekoff days
    candidates = [i for i in range(num_days) if i not in off_set]
    if not candidates:
        return sorted(list(off_set))
    # Choose approximately evenly spaced indices from candidates
    step = max(1, math.floor(len(candidates) / remaining)) if remaining > 0 else len(candidates)
    chosen = []
    idx = 0
    while len(chosen) < remaining and idx < len(candidates):
        chosen.append(candidates[idx])
        idx += step
    # If still short, pick random remaining
    i = 0
    while len(chosen) < remaining:
        candidate = candidates[i]
        if candidate not in chosen:
            chosen.append(candidate)
        i += 1
    off_set.update(chosen)
    return sorted(off_set)

# --- Assign Structured Shifts (main algorithm) ---
def assign_shifts(employees, num_days, working_days, fridays_saturdays, sundays_mondays, saturdays_sundays, festival_days, nightshift_exempt, friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data):
    np.random.seed(42)
    roster_dict = {emp: [''] * num_days for emp in employees}
    shift_counts = {emp: {'F': 0, 'G1': 0, 'N': 0, 'S': 0, 'O': 0, 'L': 0, 'H': 0, 'CO': 0} for emp in employees}

    # Pre-assign week-off days and ensure total off-days per employee = total_off_days
    for emp in employees:
        # Determine weekoff days by group membership
        weekoff_days = []
        if emp in friday_saturday_off:
            weekoff_days = fridays_saturdays
        elif emp in sunday_monday_off:
            weekoff_days = sundays_mondays
        elif emp in saturday_sunday_off:
            weekoff_days = saturdays_sundays
        emp_off_indices = assign_off_days_for_emp(num_days, num_days - working_days, weekoff_days)
        for idx in emp_off_indices:
            roster_dict[emp][idx] = 'O'
            shift_counts[emp]['O'] += 1

    # Apply leaves/special codes (these override 'O' if chosen)
    for emp in employees:
        for day_num, code in leave_data.get(emp, {}).items():
            if 1 <= day_num <= num_days and code:
                roster_dict[emp][day_num-1] = code
                shift_counts[emp][code] += 1

    # Apply festivals as 'H' for everyone (override others)
    festival_set = set(festival_days)

    # For shift balancing we'll use an order that tries to minimize per-person differences
    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_set:
            # festival -> everyone has H (holiday)
            for emp in employees:
                roster_dict[emp][day] = 'H'
            continue

        # Minimum coverage requirements
        min_fg1 = 3  # F or G1 combined
        min_n = 2
        min_s = 3

        # Build list of employees available (currently '')
        available_emps = [emp for emp in employees if roster_dict[emp][day] == '']

        # Assign Night shifts first from non-exempt employees with fewest night assignments
        non_exempt = [e for e in available_emps if e not in nightshift_exempt]
        non_exempt.sort(key=lambda e: (shift_counts[e]['N'], np.random.random()))
        n_assigned = 0
        for emp in non_exempt:
            if n_assigned >= min_n:
                break
            # avoid >5 consecutive nights
            cons_n = 0
            for p in range(day-1, max(-1, day-6), -1):
                if p >= 0 and roster_dict[emp][p] == 'N':
                    cons_n += 1
                else:
                    break
            if cons_n >= 5:
                continue
            roster_dict[emp][day] = 'N'
            shift_counts[emp]['N'] += 1
            n_assigned += 1
            available_emps.remove(emp)

        # Assign G1 (preferred morning group) from a configurable set (keep your original G1 list if present)
        # We'll keep a small set of G1 specialists if they exist in employees
        g1_specials = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
        g1_available = [e for e in available_emps if e in g1_specials]
        g1_available.sort(key=lambda e: (shift_counts[e]['G1'], np.random.random()))
        g1_assigned = 0
        for emp in g1_available:
            if g1_assigned >= min_fg1:
                break
            roster_dict[emp][day] = 'G1'
            shift_counts[emp]['G1'] += 1
            g1_assigned += 1
            available_emps.remove(emp)

        # If still need FG1 (F+G1), assign F from remaining available employees (fewest F)
        f_assigned = 0
        if g1_assigned < min_fg1:
            available_emps.sort(key=lambda e: (shift_counts[e]['F'], np.random.random()))
            for emp in list(available_emps):
                if g1_assigned + f_assigned >= min_fg1:
                    break
                roster_dict[emp][day] = 'F'
                shift_counts[emp]['F'] += 1
                f_assigned += 1
                available_emps.remove(emp)

        # Assign Second shifts (S) to meet min_s
        s_assigned = 0
        available_emps.sort(key=lambda e: (shift_counts[e]['S'], np.random.random()))
        for emp in list(available_emps):
            if s_assigned >= min_s:
                break
            roster_dict[emp][day] = 'S'
            shift_counts[emp]['S'] += 1
            s_assigned += 1
            available_emps.remove(emp)

        # Assign remaining available employees as 'S' to balance workload
        for emp in available_emps:
            roster_dict[emp][day] = 'S'
            shift_counts[emp]['S'] += 1

    # Final correction: ensure each employee has exactly the expected number of O (off) days.
    # If someone has fewer off-days (because leaves/festivals replaced them), add additional offs on least-impact days.
    desired_off = num_days - working_days
    for emp in employees:
        current_off = sum(1 for s in roster_dict[emp] if s == 'O')
        if current_off < desired_off:
            # pick days where employee currently has 'S' or 'F' (not festival 'H' or leave codes)
            candidate_days = [i for i, s in enumerate(roster_dict[emp]) if s in ('S', 'F', 'G1') and (i+1) not in festival_set]
            # sort by current total assignments of that day (prefer days with many staff so removing one has less impact)
            if candidate_days:
                candidate_days.sort(key=lambda d: (sum(1 for e in employees if roster_dict[e][d] in ('S','F','G1','N')), np.random.random()))
                needed = desired_off - current_off
                for idx in candidate_days[:needed]:
                    roster_dict[emp][idx] = 'O'
                    shift_counts[emp]['O'] += 1
        elif current_off > desired_off:
            # If too many offs (rare), convert some 'O' to 'S' to restore working days
            off_indices = [i for i, s in enumerate(roster_dict[emp]) if s == 'O']
            to_restore = current_off - desired_off
            for idx in off_indices[:to_restore]:
                roster_dict[emp][idx] = 'S'
                shift_counts[emp]['S'] += 1
                shift_counts[emp]['O'] -= 1

    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(
    employees, num_days, working_days_per_emp,
    fridays_saturdays, sundays_mondays, saturdays_sunday := saturdays_sundays,  # small assign for readability
    festival_days, nightshift_exempt,
    friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data
) if False else assign_shifts(
    employees, num_days, working_days_per_emp,
    fridays_saturdays, sundays_mondays, saturdays_sundays,
    festival_days, nightshift_exempt,
    friday_saturday_off, sunday_monday_off, saturday_sunday_off, leave_data
)

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
    st.success("✅ Full 24/7 coverage achieved with balanced shifts!")

# --- Color Coding ---
def color_shifts(val):
    colors = {'G1': 'limegreen', 'F': 'green', 'N': 'lightblue', 'S': 'lightgreen', 'O': 'lightgray', 'L': 'yellow', 'H': 'orange', 'CO': 'plum'}
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
