import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Employee Leave & Shift Planner")
st.title("Employee Leave & Shift Planner")

# --- Employee List ---
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

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["🗓️ Leave Settings & Generator", "🙋 Individual Leave Entry", "📊 Final Shift Plan"])

# ========================================
# TAB 1: LEAVE SETTINGS & GENERATOR
# ========================================
with tab1:
    st.subheader("Step 1: Configure Month")
    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox(
        "Month", list(range(1, 13)),
        index=9, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B')
    )

    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days + 1)]

    # --- Automatically detect weekends ---
    def get_weekdays(year, month, weekday_indices):
        return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in weekday_indices]

    saturdays = get_weekdays(year, month, [5])
    sundays = get_weekdays(year, month, [6])
    weekends = set(saturdays + sundays)

    st.markdown(f"**Auto-detected weekends:** Saturdays = {len(saturdays)}, Sundays = {len(sundays)}")

    # --- Weekoff Preferences ---
    st.subheader("Step 2: Weekoff Preferences")
    friday_saturday_off = st.multiselect("Friday-Saturday Off", employees)
    sunday_monday_off = st.multiselect("Sunday-Monday Off", employees)
    saturday_sunday_off = st.multiselect("Saturday-Sunday Off", employees)
    monday_tuesday_off = st.multiselect("Monday-Tuesday Off", employees)
    tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday Off", employees)
    wednesday_thursday_off = st.multiselect("Wednesday-Thursday Off", employees)
    thursday_friday_off = st.multiselect("Thursday-Friday Off", employees)

    # --- Festival Days ---
    st.subheader("Step 3: Festival / Common Holidays")
    festival_days = st.multiselect(
        "Select Festival Days", list(range(1, num_days + 1)), default=[]
    )
    festival_set = set(festival_days)

    # --- Group1 (Opposite Shift) ---
    group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
    shift_cycle = ["F", "S", "N"]

    st.subheader("Step 4: Generate Plan")

    # --- Generate Leave & Shift Plan ---
    def generate_plan(target_offs=10):
        plan = {emp: [''] * num_days for emp in employees}

        # 1. Apply weekoff logic
        def apply_weekoff(emp, days):
            for d in days:
                if 1 <= d <= num_days:
                    plan[emp][d - 1] = "O"

        # Calculate weekday-based offs
        def get_weekoff_days(pattern):
            patterns = {
                "Friday-Saturday": [4, 5],
                "Sunday-Monday": [6, 0],
                "Saturday-Sunday": [5, 6],
                "Monday-Tuesday": [0, 1],
                "Tuesday-Wednesday": [1, 2],
                "Wednesday-Thursday": [2, 3],
                "Thursday-Friday": [3, 4]
            }
            return [d for d in range(1, num_days + 1) if weekday(year, month, d) in patterns[pattern]]

        weekoff_groups = {
            "Friday-Saturday": friday_saturday_off,
            "Sunday-Monday": sunday_monday_off,
            "Saturday-Sunday": saturday_sunday_off,
            "Monday-Tuesday": monday_tuesday_off,
            "Tuesday-Wednesday": tuesday_wednesday_off,
            "Wednesday-Thursday": wednesday_thursday_off,
            "Thursday-Friday": thursday_friday_off
        }

        for pattern, members in weekoff_groups.items():
            weekoff_days = get_weekoff_days(pattern)
            for emp in members:
                apply_weekoff(emp, weekoff_days)

        # Add festival days
        for emp in employees:
            for f in festival_set:
                plan[emp][f - 1] = "H"

        # 2. Assign Group1 opposite shifts (rotate after weekoff)
        shift_index = 0
        for emp in group1:
            current_shift = shift_cycle[shift_index]
            for d in range(1, num_days + 1):
                if plan[emp][d - 1] == "O":  # Rotate shift after off
                    shift_index = (shift_index + 1) % 3
                    current_shift = shift_cycle[shift_index]
                elif plan[emp][d - 1] == "":
                    plan[emp][d - 1] = current_shift

        # 3. Assign default shifts for others
        for emp in employees:
            if emp not in group1:
                shifts = ["F", "S", "N"]
                for d in range(1, num_days + 1):
                    if plan[emp][d - 1] == "":
                        plan[emp][d - 1] = np.random.choice(shifts)

        return plan

    if st.button("Generate Leave + Shift Plan"):
        plan = generate_plan()
        df_plan = pd.DataFrame(plan, index=dates).T

        # --- Display ---
        def color_shifts(val):
            color_map = {'F': 'lightgreen', 'S': 'lightblue', 'N': 'lightpink', 'O': 'lightgray', 'H': 'orange'}
            return f'background-color: {color_map.get(val, "")}'

        st.dataframe(df_plan.style.applymap(color_shifts), height=600)

        # --- Summary ---
        summary = pd.DataFrame({
            "F": [sum(1 for v in plan[e] if v == "F") for e in employees],
            "S": [sum(1 for v in plan[e] if v == "S") for e in employees],
            "N": [sum(1 for v in plan[e] if v == "N") for e in employees],
            "O": [sum(1 for v in plan[e] if v == "O") for e in employees],
            "H": [sum(1 for v in plan[e] if v == "H") for e in employees],
        }, index=employees)

        st.subheader("Summary")
        st.dataframe(summary)

        st.session_state['final_plan'] = df_plan

# ========================================
# TAB 2: INDIVIDUAL LEAVE ENTRY
# ========================================
with tab2:
    st.subheader("Mark Individual Employee Leave")

    if "final_plan" in st.session_state:
        df_plan = st.session_state['final_plan']
        emp = st.selectbox("Select Employee", employees)
        leave_days = st.multiselect("Select Leave Dates", df_plan.columns.tolist())

        if st.button("Apply Individual Leave"):
            for d in leave_days:
                df_plan.loc[emp, d] = "L"
            st.session_state['final_plan'] = df_plan
            st.success(f"Leave applied for {emp} on {', '.join(leave_days)}")
    else:
        st.warning("Please generate the plan in the first tab.")

# ========================================
# TAB 3: FINAL SHIFT PLAN
# ========================================
with tab3:
    st.subheader("Final Shift + Leave Plan")

    if "final_plan" in st.session_state:
        df_plan = st.session_state['final_plan']

        def color_all(val):
            color_map = {
                'F': 'lightgreen', 'S': 'lightblue', 'N': 'lightpink',
                'O': 'lightgray', 'H': 'orange', 'L': 'red'
            }
            return f'background-color: {color_map.get(val, "")}'

        st.dataframe(df_plan.style.applymap(color_all), height=600)

        csv = df_plan.to_csv().encode('utf-8')
        st.download_button("Download Final Plan CSV", csv, f"final_shift_plan_{year}_{month:02d}.csv")
    else:
        st.warning("No plan available yet. Please generate it first.")
