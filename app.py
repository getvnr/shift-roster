import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from calendar import monthrange, weekday

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Based on Sample Roster)")

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
num_employees = len(employees)

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

# --- Weekend-Restricted Employees ---
st.subheader("Employees Who Won't Work on Weekends")
no_weekend_emps = st.multiselect("Select employees unavailable on weekends (SA/SU):", options=employees, default=["Ramesh Polisetty", "Ajay Chidipotu", "Srinivasu Cheedalla", "Gangavarapu Suneetha"])  # Example "few" from sample

# --- Festivals ---
st.subheader("Select Festival Dates (Optional)")
festival_days = st.multiselect("Festival Days:", options=list(range(1, num_days+1)), default=[2])  # Default to day 2 (TH) as per sample

# --- Leaves / Special Codes (Pre-populated Examples from Sample) ---
st.subheader("Add Employee Leaves or Special Codes (Examples Pre-Populated)")
leave_data = {}
example_leaves = {
    "Ajay Chidipotu": {1: 'L', 7: 'L', 8: 'L', 9: 'L', 10: 'L'},
    "Pousali C": {1: 'L'},
    "Gopalakrishnan Selvaraj": {29: 'L', 30: 'L'},
    "Gayatri Ruttala": {20: 'L', 21: 'L', 22: 'L', 23: 'L', 27: 'L', 28: 'L', 29: 'L', 30: 'L', 31: 'L'},
    "D Namithananda": {19: 'L', 20: 'L'},
    # Add more from sample as needed
}
for emp in employees:
    st.write(f"{emp} Leaves/Special Codes")
    cols = st.columns(3)
    with cols[0]:
        leave_days = st.multiselect(f"Leave/Special Days for {emp}:", options=list(range(1, num_days+1)), 
                                    default=list(example_leaves.get(emp, {}).keys()), key=f"leave_{emp}")
    with cols[1]:
        codes_options = ['L', 'H', 'CO']
        selected_codes = st.multiselect(f"Code for each day:", options=codes_options, 
                                        default=[example_leaves.get(emp, {}).get(d, 'L') for d in leave_days], key=f"code_{emp}")
    leave_data[emp] = dict(zip(leave_days, selected_codes[:len(leave_days)]))

# --- Weekends ---
def get_weekends(year, month):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) >= 5]

weekends = get_weekends(year, month)

# --- Assign Off Days (Prioritize Weekends for Restricted Employees) ---
def assign_off_days(num_days, working_days, weekoff, no_weekend_emps, weekends):
    total_off = num_days - working_days
    off_days_positions = []
    weekend_indices = [d-1 for d in weekends]
    
    # Force weekends for no_weekend_emps
    for emp in no_weekend_emps:
        emp_offs = weekend_indices[:weekoff]  # Assign offs on weekends first
        off_days_positions.append(emp_offs)
    
    # For other employees, spread offs, preferring weekends
    for emp in [e for e in employees if e not in no_weekend_emps]:
        emp_offs = weekend_indices[:min(weekoff, len(weekend_indices))]
        remaining = weekoff - len(emp_offs)
        if remaining > 0:
            non_weekend = [i for i in range(num_days) if i not in weekend_indices]
            emp_offs.extend(np.random.choice(non_weekend, remaining, replace=False))
        off_days_positions.append(sorted(emp_offs))
    
    return {emp: offs[:total_off] for emp, offs in zip(employees, off_days_positions)}  # Truncate if needed

# --- Assign Structured Shifts (Ensure 24/7 Coverage) ---
def assign_shifts(employees, num_days, working_days, weekoff, weekends, festival_days, no_weekend_emps, leave_data):
    np.random.seed(42)  # Reproducibility
    roster_dict = {emp: ['S'] * num_days for emp in employees}
    emp_off_days = assign_off_days(num_days, working_days, weekoff, no_weekend_emps, weekends)
    
    # G1 Employees from sample
    g1_employees = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
    
    # Pre-apply leaves and festivals
    for emp in employees:
        for day, code in leave_data.get(emp, {}).items():
            roster_dict[emp][day-1] = code
        for festival_day in festival_days:
            if roster_dict[emp][festival_day-1] not in ['L', 'CO']:
                roster_dict[emp][festival_day-1] = 'H'
    
    for day in range(num_days):
        if day + 1 in festival_days:
            continue  # Already handled as 'H'
        
        is_weekend = day + 1 in weekends
        if is_weekend:
            f_count, n_count = 4, 3  # Higher coverage for weekends
        else:
            f_count, n_count = 3, 2
        
        # Available employees (exclude offs, leaves, H, CO; for weekends, exclude no_weekend_emps)
        available_emps = [emp for emp in employees 
                          if (day not in emp_off_days[emp] and 
                              roster_dict[emp][day] not in ['L', 'H', 'CO', 'O']) and
                          (not is_weekend or emp not in no_weekend_emps)]
        
        # If insufficient, override offs to maintain coverage
        if len(available_emps) < f_count + n_count:
            st.warning(f"Day {day+1} (coverage: {f_count}F/G1 + {n_count}N): Insufficient available employees ({len(available_emps)}). Overriding offs.")
            override_emps = [emp for emp in employees 
                             if roster_dict[emp][day] == 'O' and emp not in no_weekend_emps]  # Don't override restricted
            available_emps.extend(override_emps[:f_count + n_count - len(available_emps)])
        
        np.random.shuffle(available_emps)
        
        # Assign G1 to specific employees if available
        assigned_g1 = 0
        for emp in g1_employees:
            if emp in available_emps and assigned_g1 < f_count // 2:  # Limit G1
                roster_dict[emp][day] = 'G1'
                available_emps.remove(emp)
                assigned_g1 += 1
        
        # Assign F and N
        for i, emp in enumerate(available_emps[:f_count - assigned_g1]):
            roster_dict[emp][day] = 'F'
        for i, emp in enumerate(available_emps[f_count - assigned_g1:f_count - assigned_g1 + n_count]):
            roster_dict[emp][day] = 'N'
        
        # Assign O for offs (after coverage)
        for emp in employees:
            if day in emp_off_days[emp] and roster_dict[emp][day] not in ['F', 'N', 'G1']:  # Don't override assigned shifts
                roster_dict[emp][day] = 'O'
    
    return roster_dict

# --- Generate Roster ---
roster_dict = assign_shifts(employees, num_days, working_days_per_emp, weekoff_per_emp, weekends, festival_days, no_weekend_emps, leave_data)

# Convert to DataFrame
roster = pd.DataFrame(roster_dict).T
roster.index = dates

# --- Check and Display Coverage ---
st.subheader("Daily Coverage Report")
coverage_data = []
for day in range(num_days):
    is_weekend = day + 1 in weekends
    required_f_g1 = 4 if is_weekend else 3
    required_n = 3 if is_weekend else 2
    f_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'F')
    n_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'N')
    g1_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'G1')
    total_f_g1 = f_assigned + g1_assigned
    s_assigned = sum(1 for emp in employees if roster_dict[emp][day] == 'S')
    coverage_data.append({
        'Day': dates[day],
        'F Assigned': f_assigned,
        'G1 Assigned': g1_assigned,
        'Total F/G1': total_f_g1,
        'Required F/G1': required_f_g1,
        'N Assigned': n_assigned,
        'Required N': required_n,
        'S Assigned': s_assigned,
        'Coverage Met': 'Yes' if total_f_g1 >= required_f_g1 and n_assigned >= required_n else 'No'
    })
coverage_df = pd.DataFrame(coverage_data)
st.dataframe(coverage_df.style.highlight_max(axis=0, subset=['Total F/G1', 'N Assigned']))

# --- Color Coding ---
def color_shifts(val):
    colors = {'G1': 'limegreen', 'F': 'green', 'N': 'blue', 'S': 'lightgreen', 'O': 'red', 'L': 'yellow', 'H': 'orange', 'CO': 'purple'}
    return f'background-color: {colors.get(val, "white")}'

# --- Display Roster ---
st.subheader("Generated 24/7 Roster")
st.dataframe(roster.style.applymap(color_shifts))

# --- Shift Summary per Employee ---
st.subheader("Shift Summary per Employee")
summary_data = {shift: [sum(1 for s in roster_dict[emp] if s == shift) for emp in employees] for shift in ['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO']}
summary_df = pd.DataFrame(summary_data, index=employees)
st.dataframe(summary_df)

# --- Visualization: Shift Distribution Chart ---
st.subheader("Shift Distribution Visualization")
fig = go.Figure()
for i, emp in enumerate(employees[:10]):  # Limit to 10 for readability; adjust as needed
    emp_data = [summary_data[shift][i] for shift in ['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO']]
    fig.add_trace(go.Bar(name=emp, x=['G1', 'F', 'N', 'S', 'O', 'L', 'H', 'CO'], y=emp_data, 
                         marker_color=['lime', 'green', 'blue', 'lightgreen', 'red', 'yellow', 'orange', 'purple']))

fig.update_layout(barmode='group', title="Shift Counts per Employee (First 10 Employees)", xaxis_title="Shift Type", yaxis_title="Number of Days")
st.plotly_chart(fig, use_container_width=True)

# --- Download CSV ---
csv = roster.to_csv().encode('utf-8')
st.download_button("Download Roster CSV", csv, "roster.csv", "text/csv")
st.download_button("Download Coverage Report CSV", coverage_df.to_csv(index=False).encode('utf-8'), "coverage_report.csv", "text/csv")
