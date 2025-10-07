import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Night & Weekend Exemptions)")

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

# --- Weekend-Exempt Employees ---
st.subheader("Weekend-Exempt Employees")
weekend_exempt = st.multiselect(
    "Select employees who won't work on weekends (auto O on SA/SU):",
    options=employees,
    default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
)

# --- Night-Exempt Employees ---
st.subheader("Night-Exempt Employees")
night_exempt = st.multiselect(
    "Select employees who won't work Night shifts (no N shifts):",
    options=employees,
    default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao",
             "Muppa Divya", "Anil Athkuri", "Imran Khan", "Gayatri Ruttala"]
)

# --- Week-Off Preferences ---
st.subheader("Week-Off Preferences")
week_off_prefs = {}
for emp in employees:
    if emp in weekend_exempt:
        week_off_prefs[emp] = "SA-SU"  # Weekend-exempt get SA/SU
    else:
        st.write(f"Week-off preference for {emp}")
        week_off_prefs[emp] = st.selectbox(
            f"Choose week-off days for {emp}:",
            options=["Friday-Saturday", "Sunday-Monday", "No Preference"],
            key=f"weekoff_{emp}"
        )

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

# --- Working Days & Week-Offs ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
weekoff_per_emp = st.number_input("Number of week-off days per employee:", min_value=0, max_value=num_days-working_days_per_emp, value=10)
if working_days_per_emp + weekoff_per_emp > num_days:
    st.error("Working days plus week-off days cannot exceed the number of days in the month.")
    st.stop()

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days (H for all):", options=list(range(1, num_days+1)), default=[2])

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

# --- Weekends ---
def get_weekends(year, month):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) >= 5]

weekends = get_weekends(year, month)

# --- Assign Off Days ---
def assign_off_days(num_days, working_days, weekoff, weekends, week_off_pref):
    total_off = num_days - working_days
    off_days_positions = []
    
    # Weekend-exempt employees get all SA/SU
    if week_off_pref == "SA-SU":
        off_days_positions.extend([d-1 for d in weekends])
        remaining_off = total_off - len(off_days_positions)
        if remaining_off > 0:
            st.warning(f"Insufficient weekend days for full off-day requirement. Adding extra off days.")
            available_days = [i for i in range(num_days) if i not in [d-1 for d in weekends]]
            num_pairs = remaining_off // 2
            for _ in range(num_pairs):
                if available_days:
                    start = np.random.choice([i for i in available_days if i+1 in available_days])
                    off_days_positions.extend([start, start+1])
                    available_days.remove(start)
                    available_days.remove(start+1)
    else:
        # Calculate weeks and assign FR-SA or SU-MO
        num_pairs = total_off // 2
        week_starts = [i for i in range(0, num_days, 7) if i+6 < num_days]
        for week_start in week_starts:
            fr = week_start + 4  # Friday (0=WE, 4=FR)
            sa = week_start + 5  # Saturday
            su = week_start + 6  # Sunday
            mo = week_start + 7  # Monday (may exceed num_days)
            if week_off_pref == "Friday-Saturday" and fr < num_days and sa < num_days:
                off_days_positions.extend([fr, sa])
            elif week_off_pref == "Sunday-Monday" and su < num_days and (mo < num_days or mo == num_days):
                off_days_positions.extend([su, mo-1 if mo == num_days else su, mo])
            elif week_off_pref == "No Preference":
                # Randomly choose FR-SA or SU-MO
                choice = np.random.choice(["FR-SA", "SU-MO"])
                if choice == "FR-SA" and fr < num_days and sa < num_days:
                    off_days_positions.extend([fr, sa])
                elif su < num_days and (mo < num_days or mo == num_days):
                    off_days_positions.extend([su, mo-1 if mo == num_days else su, mo])
        
        # Add remaining off days in pairs
        remaining_off = total_off - len(off_days_positions)
        if remaining_off > 0:
            available_days = [i for i in range(num_days) if i not in off_days_positions]
            num_pairs = remaining_off // 2
            for _ in range(num_pairs):
                if available_days:
                    start = np.random.choice([i for i in available_days if i+1 in available_days])
                    off_days_positions.extend([start, start+1])
                    available_days.remove(start)
                    available_days.remove(start+1)
    
    return sorted(set(off_days_positions))

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, weekoff, weekends, festival_days, weekend_exempt, night_exempt, leave_data, week_off_prefs):
    np.random.seed(42)
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    g1_employees = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
    
    # Pre-assign off days
    emp_off_days = {emp: assign_off_days(num_days, working_days, weekoff, weekends, week_off_prefs[emp]) for emp in employees}
    
    # Apply leaves first
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
    
    # Assign Night shifts in blocks of at least 5
    n_eligible = [emp for emp in employees if emp not in night_exempt]
    for emp in n_eligible:
        available_days = [d for d in range(num_days) if roster_dict[emp][d] not in ['L', 'H', 'CO', 'O']]
        num_nights = sum(1 for d in range(num_days) if roster_dict[emp][d] == 'N')
        target_nights = 5 if num_nights < 5 else num_nights
        if available_days and len(available_days) >= target_nights:
            blocks = []
            for i in range(len(available_days) - target_nights + 1):
                if all(available_days[i+j] == available_days[i]+j for j in range(target_nights)):
                    blocks.append(available_days[i:i+target_nights])
            if blocks:
                block = np.random.choice(len(blocks))
                for d in blocks[block]:
                    roster_dict[emp][d] = 'N'
    
    for day in range(num_days):
        day_num = day + 1
        is_weekend = day_num in weekends
        is_festival = day_num in festival_days
        is_special = is_weekend or is_festival
        
        # Festival: All H
        if is_festival:
            for emp in employees:
                roster_dict[emp][day] = 'H'
            continue
        
        # Coverage requirements
        min_fg1 = 4 if is_special else 3
        min_n = 3 if is_special else 2
        
        # Available employees (not off, not leave/H/CO)
        available_emps = [emp for emp in employees 
                         if day not in emp_off_days[emp] 
                         and roster_dict[emp][day] not in ['L', 'H', 'CO', 'N']]
        
        # Filter out night-exempt for N shifts
        n_available = [emp for emp in employees 
                       if emp not in night_exempt 
                       and day not in emp_off_days[emp] 
                       and roster_dict[emp][day] not in ['L', 'H', 'CO']]
        
        if len(n_available) < min_n:
            st.warning(f"Day {day_num}: Not enough non-night-exempt employees for {min_n} Night shifts. Adjusting.")
            n_available = [emp for emp in employees if day not in emp_off_days[emp] and roster_dict[emp][day] not in ['L', 'H', 'CO']]
        
        # Assign G1 to eligible employees
        for emp in g1_employees:
            if emp in available_emps and roster_dict[emp][day] not in ['L', 'H', 'CO', 'N']:
                roster_dict[emp][day] = 'G1'
                available_emps.remove(emp)
                if emp in n_available:
                    n_available.remove(emp)
                min_fg1 -= 1
        
        # Shuffle for fairness
        np.random.shuffle(available_emps)
        np.random.shuffle(n_available)
        
        # Assign F to meet F/G1 minimum
        f_assigned = 0
        for i, emp in enumerate(available_emps):
            if f_assigned < min_fg1:
                roster_dict[emp][day] = 'F'
                f_assigned += 1
                if emp in n_available:
                    n_available.remove(emp)
            else:
                break
        
        # Assign additional N to meet minimum
        current_n = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
        n_needed = max(0, min_n - current_n)
        for i, emp in enumerate(n_available):
            if n_needed > 0:
                roster_dict[emp][day] = 'N'
                n_needed -= 1
            else:
                break
        
        # Apply off days
        for emp in employees:
            if day in emp_off_days[emp]:
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekoff_per_emp, weekends, festival_days, weekend_exempt, night_exempt, week_off_prefs)

# Convert to DataFrame
roster = pd.DataFrame(roster_dict, index=dates).T

# --- Coverage Validation ---
st.subheader("Coverage Check")
coverage_issues = []
for day in range(num_days):
    day_num = day + 1
    f_count = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    g1_count = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
    n_count = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    is_special = day_num in weekends or day_num in festival_days
    min_fg1 = 4 if is_special else 3
    min_n = 3 if is_special else 2
    
    if f_count + g1_count < min_fg1 or n_count < min_n:
        coverage_issues.append(f"⚠️ Day {day_num}: {f_count + g1_count} F/G1, {n_count} N (need {min_fg1} F/G1, {min_n} N)")

if coverage_issues:
    st.warning("Coverage Issues:\n" + "\n".join(coverage_issues))
else:
    st.success("✅ Full 24/7 coverage achieved!")

# --- Color Coding ---
def color_shifts(val):
    colors = {'G1': 'limegreen', 'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple'}
    return f'background-color: {colors.get(val, "")}'

# --- Display Roster ---
st.subheader("Generated Roster")
st.dataframe(roster.style.applymap(color_shifts), height=600)

# --- Shift Summary ---
st.subheader("Shift Summary")
summary_data = {shift: [sum(1 for s in roster_dict[emp] if s == shift) for emp in employees] for shift in ['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO']}
summary = pd.DataFrame(summary_data, index=employees)
st.dataframe(summary)

# --- Download ---
csv = roster.to_csv().encode('utf-8')
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv", "text/csv")
