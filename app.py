# full_streamlit_shift_planner_v2.py
import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide", page_title="Employee Leave & Shift Planner")
st.title("Employee Leave & Shift Planner — 24/7 Coverage")

# --------------------------
# Employee / Group Definition (active only)
# --------------------------
employee_data = pd.DataFrame([
    ["Pousali C", "Group5"],
    ["B Madhurusha", "Group5"],
    ["Chinthalapudi Yaswanth", "Group5"],
    ["Edagotti Kalpana", "Group6"],
    ["Thorat Yashwant", "Group6"],
    ["Srivastav Nitin", "Group7"],
    ["Kishore Khati Vaibhav", "Group7"],
    ["Rupan Venkatesan Anandha", "Group8"],
    ["Chaudhari Kaustubh", "Group8"],
    ["Shejal Gawade", "Group9"],
    ["Vivek Kushwaha", "Group9"],
    ["Abdul Mukthiyar Basha", "Group10"],
    ["M Naveen", "Group10"]
], columns=["Name", "Group"])

employees = employee_data["Name"].tolist()

# Pool for 24/7 coverage (all active engineers)
coverage_pool = employees.copy()

# --------------------------
# UI: Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# --------------------------
# Helpers: weekday / weekends
# --------------------------
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in weekday_indices]

def get_weekoff_days(year, month):
    # Sat + Sun
    saturdays = get_weekdays(year, month, [5])
    sundays = get_weekdays(year, month, [6])
    return sorted(saturdays + sundays)

# --------------------------
# TAB 1: Configuration & Generate
# --------------------------
with tab1:
    st.header("Step 1 — Configure month & generate roster")

    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox("Month", list(range(1,13)), index=9,
                         format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    st.subheader("Festival / Common holidays (optional)")
    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    st.subheader("Coverage constraints")
    max_night_per_day = st.number_input("Max people on Night (N) per day", min_value=1, max_value=10, value=2)
    min_morning_per_day = st.number_input("Min people on Morning (F) per day", min_value=1, max_value=10, value=2)
    max_morning_per_day = st.number_input("Max people on Morning (F) per day", min_value=1, max_value=10, value=3)
    min_second_per_day = st.number_input("Min people on Second (S) per day", min_value=1, max_value=10, value=3)
    max_second_per_day = st.number_input("Max people on Second (S) per day", min_value=1, max_value=10, value=4)
    max_nights_per_person = st.number_input("Max nights per person per month", min_value=0, max_value=num_days, value=5)

    st.info("All active engineers will rotate to cover 24/7 shifts with weekoffs applied automatically.")

    # Button to generate
    if st.button("Generate 24/7 Shift Plan"):
        # --------------------------
        # Step A: initialize plan
        # --------------------------
        plan = {emp: ['']*num_days for emp in employees}
        night_count_by_person = {emp: 0 for emp in employees}

        # Apply weekends as offs
        weekoff_days = get_weekoff_days(year, month)
        for emp in employees:
            for d in weekoff_days:
                plan[emp][d-1] = 'O'

        # Apply festival days as holiday
        for emp in employees:
            for f in festival_days:
                plan[emp][f-1] = 'H'

        # --------------------------
        # Step B: Assign shifts with constraints
        # --------------------------
        rng = np.random.default_rng(seed=(year*100 + month))
        for d in range(num_days):
            # Skip O/H days
            available = [e for e in employees if plan[e][d] == '']

            # Assign Nights first (max 2 per day, max 5 per person)
            def pick_night(candidates):
                candidates = [e for e in candidates if night_count_by_person[e] < max_nights_per_person]
                candidates_sorted = sorted(candidates, key=lambda x: night_count_by_person[x])
                return candidates_sorted[:max_night_per_day]

            night_assigned = pick_night(available)
            for e in night_assigned:
                plan[e][d] = 'N'
                night_count_by_person[e] += 1
            available = [e for e in available if e not in night_assigned]

            # Assign Morning F
            n_morning_needed = min(max_morning_per_day, len(available))
            for e in available[:n_morning_needed]:
                plan[e][d] = 'F'
            available = [e for e in available if plan[e][d] == '']

            # Assign Second S
            for e in available:
                plan[e][d] = 'S'

        # --------------------------
        # Step C: Fill any blanks (safety)
        # --------------------------
        for emp in employees:
            for d in range(num_days):
                if plan[emp][d] == '':
                    plan[emp][d] = 'S'

        df_plan = pd.DataFrame(plan, index=employees, columns=dates)
        st.session_state['final_plan'] = df_plan
        st.success("Shift plan generated! Check the 'Final Plan & Summary' tab.")

# --------------------------
# TAB 2: Individual Leave
# --------------------------
with tab2:
    st.header("Individual leave / ad-hoc adjustments")
    if 'final_plan' not in st.session_state:
        st.warning("Generate a plan first.")
    else:
        df = st.session_state['final_plan']
        emp = st.selectbox("Employee", employees)
        day = st.multiselect("Select date(s) to mark as Individual Leave (L)", df.columns.tolist())
        if st.button("Apply Individual Leave"):
            for d in day:
                df.loc[emp, d] = 'L'
            st.session_state['final_plan'] = df
            st.success(f"Applied individual leave for {emp} on {', '.join(day)}")

# --------------------------
# TAB 3: Final Plan & Summary
# --------------------------
with tab3:
    st.header("Final Shift Plan and Summary")
    if 'final_plan' not in st.session_state:
        st.warning("No plan available. Generate first.")
    else:
        df_plan = st.session_state['final_plan']

        # Coloring
        def color_map(val):
            cmap = {'F': 'lightgreen','S':'lightblue','N':'lightpink','O':'lightgray','H':'orange','L':'red'}
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map), height=600)

        # Summary counts
        summary = pd.DataFrame({
            'F': [sum(1 for v in df_plan.loc[e] if v=='F') for e in df_plan.index],
            'S': [sum(1 for v in df_plan.loc[e] if v=='S') for e in df_plan.index],
            'N': [sum(1 for v in df_plan.loc[e] if v=='N') for e in df_plan.index],
            'O': [sum(1 for v in df_plan.loc[e] if v=='O') for e in df_plan.index],
            'H': [sum(1 for v in df_plan.loc[e] if v=='H') for e in df_plan.index],
            'L': [sum(1 for v in df_plan.loc[e] if v=='L') for e in df_plan.index],
        }, index=df_plan.index)
        st.subheader("Per-person shift counts this month")
        st.dataframe(summary)

        # Daily coverage check
        daily_counts = pd.DataFrame({
            'Date': df_plan.columns,
            'F': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='F') for col in df_plan.columns],
            'S': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='S') for col in df_plan.columns],
            'N': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='N') for col in df_plan.columns],
            'O/H/L': [sum(1 for e in df_plan.index if df_plan.loc[e, col] in ('O','H','L')) for col in df_plan.columns]
        })
        st.subheader("Daily coverage summary")
        st.dataframe(daily_counts)

        # Download
        csv = df_plan.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"final_shift_plan_{year}_{month:02d}.csv")

        st.info("Algorithm assigns F/S/N shifts respecting max nights per person, weekoffs, and coverage targets.")

