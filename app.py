import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (October 2025)")

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

# --- Weekend-Exempt Employees ---
st.subheader("Weekend-Exempt Employees")
weekend_exempt = st.multiselect(
    "Select employees who won't work on weekends (SA/SU off):",
    options=employees,
    default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
)

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'), index=9)
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

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

# --- Get Weekends ---
def get_weekends(year, month):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) >= 5]

weekends = get_weekends(year, month)

# --- Assign Off Days (2 consecutive off days after 5 working days) ---
def assign_off_days(num_days, working_days, weekends, is_weekend_exempt):
    total_off = num_days - working_days
    off_days_positions = []
    
    # Assign weekend off days for exempt employees
    if is_weekend_exempt:
        off_days_positions.extend([d-1 for d in weekends])
    
    remaining_off = total_off - len(off_days_positions)
    if remaining_off < 0:
        return off_days_positions  # Cannot satisfy, return fixed week-offs only
    
    # Add pairs of consecutive off days after 5 working days
    cycle_length = 7  # 5 working + 2 off
    num_cycles = remaining_off // 2
    for cycle in range(num_cycles):
        start = cycle * cycle_length + 5  # After 5 working days
        if start + 1 < num_days:  # Ensure we don't exceed month
            off_days_positions.extend([start, start + 1])
    
    # Handle any remaining single off day
    if remaining_off % 2 == 1 and len(off_days_positions) + 1 < num_days:
        last_off = min(num_days - 1, off_days_positions[-1] + cycle_length + 1 if off_days_positions else 5)
        off_days_positions.append(last_off)
    
    return sorted(set(off_days_positions))  # Remove duplicates

# --- Assign Night Shift Blocks (5 nights + 2 off) ---
def assign_night_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, emp_off_days, leave_data):
    block_length = 7  # 5 nights + 2 off
    debug_info = []
    for emp in employees:
        if emp in nightshift_exempt:
            debug_info.append(f"{emp}: Skipped (nightshift-exempt)")
            continue
        # Get available days (not off, not leave/H/CO)
        available_days = [d for d in range(num_days) if d not in emp_off_days[emp] and roster_dict[emp][d] not in ['L', 'H', 'CO']]
        debug_info.append(f"{emp}: {len(available_days)} available days: {available_days}")
        if len(available_days) < block_length:
            debug_info.append(f"{emp}: Not enough days for 5N+2O block")
            continue
        # Try to assign multiple 5N+2O blocks
        valid_starts = []
        for i in range(len(available_days) - block_length + 1):
            block = available_days[i:i + block_length]
            if len(block) == block_length and all(block[j + 1] == block[j] + 1 for j in range(block_length - 1)):
                valid_starts.append(block[0])
        if not valid_starts:
            debug_info.append(f"{emp}: No consecutive 7-day block available")
            continue
        # Assign as many blocks as possible
        np.random.shuffle(valid_starts)
        blocks_assigned = 0
        for start_day in valid_starts:
            # Check if block is still available
            if all(roster_dict[emp][start_day + i] not in ['N', 'O', 'L', 'H', 'CO'] for i in range(block_length)):
                for i in range(5):
                    roster_dict[emp][start_day + i] = 'N'
                roster_dict[emp][start_day + 5] = 'O'
                roster_dict[emp][start_day + 6] = 'O'
                emp_off_days[emp].extend([start_day + 5, start_day + 6])
                emp_off_days[emp] = sorted(set(emp_off_days[emp]))
                debug_info.append(f"{emp}: Assigned 5N+2O block starting day {start_day + 1}")
                blocks_assigned += 1
                # Update available days
                available_days = [d for d in available_days if not (start_day <= d < start_day + block_length)]
                if len(available_days) < block_length:
                    break
        debug_info.append(f"{emp}: Assigned {blocks_assigned} night shift blocks")
    return roster_dict, emp_off_days, debug_info

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, weekends, festival_days, nightshift_exempt, weekend_exempt, leave_data):
    np.random.seed(42)
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    
    # Pre-assign off days
    emp_off_days = {}
    g1_employees = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
    for emp in employees:
        is_weekend_exempt = emp in weekend_exempt
        emp_off_days[emp] = assign_off_days(num_days, working_days, weekends, is_weekend_exempt)
    
    # Apply leaves first
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
    
    # Assign night shift blocks (5 nights + 2 off)
    roster_dict, emp_off_days, debug_info = assign_night_shift_blocks(roster_dict, employees, num_days, nightshift_exempt, emp_off_days, leave_data)
    
    # Display debug info
    st.subheader("Night Shift Assignment Debug Info")
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
        
        # Coverage requirements
        min_fg1 = 4 if is_special else 3
        min_n = 3 if is_special else 2
        min_s = 2  # Minimum S shifts every day
        
        # Available employees (not off, not leave/H/CO/N)
        available_emps = [emp for emp in employees 
                         if day not in emp_off_days[emp] 
                         and roster_dict[emp][day] not in ['L', 'H', 'CO', 'N', 'O']]
        
        # Count current shifts
        f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
        g1_count = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
        n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
        s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
        
        # Assign G1 to eligible employees
        for emp in g1_employees:
            if emp in available_emps and g1_count + f_count < min_fg1:
                roster_dict[emp][day] = 'G1'
                available_emps.remove(emp)
                g1_count += 1
        
        # Assign F to meet min_fg1
        np.random.shuffle(available_emps)
        for emp in available_emps:
            if f_count + g1_count < min_fg1:
                roster_dict[emp][day] = 'F'
                f_count += 1
                available_emps.remove(emp)
            else:
                break
        
        # Assign S to meet min_s
        for emp in available_emps:
            if s_count < min_s:
                roster_dict[emp][day] = 'S'
                s_count += 1
                available_emps.remove(emp)
            else:
                break
        
        # Apply off days last
        for emp in employees:
            if day in emp_off_days[emp]:
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekends, festival_days, nightshift_exempt, weekend_exempt, leave_data)

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    g1_count = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    s_count = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    is_special = day_num in weekends or day_num in festival_days
    min_fg1 = 4 if is_special else 3
    min_n = 3 if is_special else 2
    min_s = 2
    
    if f_count + g1_count < min_fg1 or n_count < min_n or s_count < min_s:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count + g1_count} F/G1, {n_count} N, {s_count} S (need {min_fg1} F/G1, {min_n} N, {min_s} S)")

# Validate night shift blocks (5 nights + 2 off)
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
            elif consecutive_n > 5:
                night_shift_issues.append(f"⚠️ {emp} has {consecutive_n} consecutive night shifts (max 5 allowed)")
        else:
            consecutive_n = 0

if coverage_issues or night_shift_issues:
    if coverage_issues:
        st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
    if night_shift_issues:
        st.warning("Night Shift Issues:\n" + "\n".join(night_shift_issues))
else:
    st.success("✅ Full 24/7 coverage achieved with night shift constraints!")

# --- Color Coding ---
def color_shifts(val):
    colors = {'G1': 'limegreen', 'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple', 'E': 'pink'}
    return f'background-color: {colors.get(val, "")}'

# --- Display Roster ---
st.subheader("Generated Roster")
roster = pd.DataFrame(roster_dict, index=dates).T
st.dataframe(roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary_data = {shift: [sum(1 for s in roster_dict[emp] if s == shift) for emp in employees] for shift in ['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO', 'E']}
summary = pd.DataFrame(summary_data, index=employees)
st.dataframe(summary)

# --- Download ---
csv = roster.to_csv().encode('utf-8')
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv")
