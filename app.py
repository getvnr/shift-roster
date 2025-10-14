import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("Employee Leave + Shift Plan Generator")

# --- Default Employee Data ---
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", "IIS"],
    ["Paneerselvam F", "IIS"],
    ["Rajesh Jayapalan", "IIS"],
    ["Ajay Chidipotu", "Websphere"],
    ["Imran Khan", "Websphere"],
    ["Sammeta Balachander", "Websphere"],
    ["Ramesh Polisetty", ""],
    ["Muppa Divya", ""],
    ["Anil Athkuri", ""],
    ["D Namithananda", ""],
    ["Srinivasu Cheedalla", ""],
    ["Gangavarapu Suneetha", ""],
    ["Lakshmi Narayana Rao", ""],
    ["Pousali C", ""],
    ["Thorat Yashwant", ""],
    ["Srivastav Nitin", ""],
    ["Kishore Khati Vaibhav", ""],
    ["Rupan Venkatesan Anandha", ""],
    ["Chaudhari Kaustubh", ""],
    ["Shejal Gawade", ""],
    ["Vivek Kushwaha", ""],
    ["Abdul Mukthiyar Basha", ""],
    ["M Naveen", ""],
    ["B Madhurusha", ""],
    ["Chinthalapudi Yaswanth", ""],
    ["Edagotti Kalpana", ""]
], columns=["Name", "Skill"])

employees = employee_data["Name"].tolist()

# --- Group1 Opposite Shift Members ---
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
shift_cycle = ["F", "S", "N"]  # Opposite shifts

# --- Month Selection ---
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox(
    "Month", list(range(1, 13)),
    index=9,
    format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B')
)
num_days = monthrange(year, month)[1]
dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days + 1)]

# --- Auto Detect Weekends ---
def get_weekday_days(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1] + 1)
            if weekday(year, month, d) in weekday_indices]

saturdays = get_weekday_days(year, month, [5])
sundays = get_weekday_days(year, month, [6])
weekends = set(saturdays + sundays)

# --- Festival Days (Optional Manual Selection) ---
festival_days = st.multiselect(
    "Festival Days (Optional)",
    list(range(1, num_days + 1)),
    default=[]
)
festival_set = set(festival_days)

# --- Generate Shift Plan ---
def generate_shift_plan():
    plan = {emp: [''] * num_days for emp in employees}

    # Assign Group1 opposite shifts that change only after weekoff
    shift_index = 0
    for emp in group1:
        current_shift = shift_cycle[shift_index]
        for day in range(1, num_days + 1):
            if day in weekends:
                plan[emp][day - 1] = "O"
                # rotate to next shift after weekoff
                if day == num_days or (day + 1 not in weekends):
                    shift_index = (shift_index + 1) % 3
                    current_shift = shift_cycle[shift_index]
            else:
                plan[emp][day - 1] = current_shift
        shift_index = (shift_index + 1) % 3

    # Assign rest employees with default S shift except weekends
    for emp in employees:
        if emp not in group1:
            for day in range(1, num_days + 1):
                if day in weekends:
                    plan[emp][day - 1] = "O"
                elif day in festival_set:
                    plan[emp][day - 1] = "H"
                else:
                    plan[emp][day - 1] = np.random.choice(["F", "S", "N"])

    return plan

# --- Generate Plan ---
shift_plan = generate_shift_plan()
df_plan = pd.DataFrame(shift_plan, index=dates).T

# --- Color Coding ---
def color_shifts(val):
    color_map = {
        'F': 'lightgreen',
        'S': 'lightblue',
        'N': 'lightpink',
        'O': 'lightgray',
        'H': 'orange'
    }
    return f'background-color: {color_map.get(val, "")}'

# --- Display Shift Plan ---
st.subheader("Employee Shift Plan")
st.dataframe(df_plan.style.applymap(color_shifts), height=600)

# --- Summary Table ---
summary = pd.DataFrame({
    "F Shift": [sum(1 for v in shift_plan[e] if v == 'F') for e in employees],
    "S Shift": [sum(1 for v in shift_plan[e] if v == 'S') for e in employees],
    "N Shift": [sum(1 for v in shift_plan[e] if v == 'N') for e in employees],
    "Off (O)": [sum(1 for v in shift_plan[e] if v == 'O') for e in employees],
    "Holidays (H)": [sum(1 for v in shift_plan[e] if v == 'H') for e in employees],
}, index=employees)
st.subheader("Shift Summary")
st.dataframe(summary)

# --- Download CSV ---
csv = df_plan.to_csv().encode('utf-8')
st.download_button("Download Shift Plan CSV", csv, f"shift_plan_{year}_{month:02d}.csv")
