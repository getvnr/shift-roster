import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Weekend Exemptions + Coverage)")

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

# --- Weekend Exempt Employees ---
st.subheader("Weekend-Exempt Employees")
weekend_exempt = st.multiselect(
    "Select employees who won't work on weekends (auto O on SA/SU):",
    options=employees,
    default=["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
)

# --- Month & Year ---
year = st.number_input("Select Year:", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B'))
num_days = monthrange(year, month)[1]
dates = [f"{day}-{month}-{year}" for day in range(1, num_days+1)]

# --- Working Days & Week-Offs ---
working_days_per_emp = st.number_input("Number of working days per employee:", min_value=1, max_value=num_days, value=21)
weekoff_per_emp = st.number_input("Number of week-off days per employee:", min_value=0, max_value=num_days-working_days_per_emp, value=4)
if working_days_per_emp + weekoff_per_emp > num_days:
    st.error("Working days plus week-off days cannot exceed the number of days in the month.")
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
        codes = [''] * len(leave_days)  # Allow empty or select
        for i in range(len(leave_days)):
            codes[i] = st.selectbox(f"Code for day {leave_days[i]}:", ['L', 'H', 'CO'], key=f"code_{emp}_{i}")
    leave_data[emp] = dict(zip(leave_days, codes))

# --- Weekends ---
def get_weekends(year, month):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) >= 5]

weekends = get_weekends(year, month)

# --- Assign Off Days ---
def assign_off_days(num_days, working_days, weekoff, weekends, is_exempt):
    total_off = num_days - working_days
    off_days_positions = []
    
    # For exempt employees, add ALL weekends as off
    if is_exempt:
        weekend_indices = [d-1 for d in weekends]
        off_days_positions.extend(weekend_indices)
        remaining_off = total_off - len(weekend_indices)
    else:
        remaining_off = total_off
    
    # Add remaining off days evenly
    if remaining_off > 0:
        interval = max(1, num_days // remaining_off)
        additional_off = [i for i in range(interval-1, num_days, interval)][:remaining_off]
        off_days_positions.extend(additional_off)
    
    return sorted(set(off_days_positions))  # Remove duplicates

# --- Assign Structured Shifts ---
@st.cache_data
def assign_shifts(employees, num_days, working_days, weekoff, weekends, festival_days, weekend_exempt, leave_data):
    np.random.seed(42)
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    
    # Pre-assign off days
    emp_off_days = {}
    g1_employees = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
    for emp in employees:
        is_exempt = emp in weekend_exempt
        emp_off_days[emp] = assign_off_days(num_days, working_days, weekoff, weekends, is_exempt)
    
    # Apply leaves first
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            if code:
                roster_dict[emp][day-1] = code
    
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
                         and roster_dict[emp][day] not in ['L', 'H', 'CO', 'O']]
        
        # Assign G1 to eligible employees
        for emp in g1_employees:
            if emp in available_emps:
                roster_dict[emp][day] = 'G1'
                available_emps.remove(emp)
                min_fg1 -= 1  # G1 counts toward F/G1
        
        # Assign F and N to meet minima
        np.random.shuffle(available_emps)
        f_assigned = 0
        n_assigned = 0
        
        # F/G1 first
        for i, emp in enumerate(available_emps):
            if f_assigned < min_fg1:
                roster_dict[emp][day] = 'F'
                f_assigned += 1
            else:
                break
        
        # N next
        for i, emp in enumerate(available_emps[f_assigned:]):
            if n_assigned < min_n:
                roster_dict[emp][day] = 'N'
                n_assigned += 1
            else:
                break
        
        # Apply off days last (overrides if needed)
        for emp in employees:
            if day in emp_off_days[emp]:
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekoff_per_emp, weekends, festival_days, weekend_exempt, leave_data)

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
st.download_button("📥 Download CSV", csv, f"roster_{year}_{month:02d}.csv")
