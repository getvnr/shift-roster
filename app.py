# full_streamlit_shift_planner_v2.py
import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide", page_title="Employee Leave & Shift Planner")
st.title("Employee Leave & Shift Planner — 24/7 Coverage")

# --------------------------
# Employee / Group Definition
# --------------------------
employee_data = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", "IIS"],
    ["Paneerselvam F", "IIS"],
    ["Rajesh Jayapalan", "IIS"],
    ["Ajay Chidipotu", "Websphere"],
    ["Imran Khan", "Websphere"],
    ["Sammeta Balachander", "Websphere"],
    ["Ramesh Polisetty", "Middleware"],
    ["Srinivasu Cheedalla", "Middleware"],
    ["Gangavarapu Suneetha", "Middleware"],
    ["Lakshmi Narayana Rao", "Middleware"],
    ["Muppa Divya", "Middleware"],
    ["Anil Athkuri", "Middleware"],
    ["D Namithananda", "Middleware"],
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

# Groups (fixed patterns)
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
group3 = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
group4 = ["Muppa Divya", "Anil Athkuri", "D Namithananda"]

# Pool for 24/7 coverage
coverage_pool = [
    "Pousali C","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana",
    "Thorat Yashwant","Srivastav Nitin","Kishore Khati Vaibhav","Rupan Venkatesan Anandha",
    "Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen"
]

# --------------------------
# Helpers
# --------------------------
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

def get_weekoff_days_for_pattern(year, month, pattern):
    patterns = {
        "Friday-Saturday": [4,5],
        "Sunday-Monday": [6,0],
        "Saturday-Sunday": [5,6],
        "Monday-Tuesday": [0,1],
        "Tuesday-Wednesday": [1,2],
        "Wednesday-Thursday": [2,3],
        "Thursday-Friday": [3,4]
    }
    idxs = patterns.get(pattern, [])
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in idxs]

def count_shift_on_day(plan, day_index, shift_code):
    return sum(1 for e in employees if plan[e][day_index] == shift_code)

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# --------------------------
# TAB 1: Configuration
# --------------------------
with tab1:
    st.header("Step 1 — Configure month & weekoffs")

    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox("Month", list(range(1,13)), index=9,
                         format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    st.subheader("Weekoff preferences")
    weekoff_patterns = ["Friday-Saturday","Sunday-Monday","Saturday-Sunday",
                        "Monday-Tuesday","Tuesday-Wednesday","Wednesday-Thursday","Thursday-Friday"]
    weekoff_selection = {pattern: st.multiselect(pattern, employees) for pattern in weekoff_patterns}

    st.subheader("Festival / Common holidays (optional)")
    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    st.subheader("Coverage constraints")
    max_night_per_day = st.number_input("Max people on Night (N) per day", min_value=1, max_value=10, value=2)
    target_morning = st.number_input("Target people on Morning (F) per day", min_value=1, max_value=10, value=3)
    target_second = st.number_input("Target people on Second (S) per day", min_value=1, max_value=10, value=3)
    max_nights_per_person = st.number_input("Max nights per person in month", min_value=0, max_value=num_days, value=6)

    st.info("Coverage pool members (these staff will be assigned to meet daily F/S/N targets):")
    st.write(", ".join(coverage_pool))

    if st.button("Generate 24/7 Shift + Leave Plan"):
        # --------------------------
        # Step A: Initialize blank plan
        # --------------------------
        plan = {emp: ['']*num_days for emp in employees}

        # Apply weekoffs
        for pattern, members in weekoff_selection.items():
            days = get_weekoff_days_for_pattern(year, month, pattern)
            for emp in members:
                for d in days:
                    plan[emp][d-1] = 'O'

        # Apply festival days
        for emp in employees:
            for f in festival_days:
                plan[emp][f-1] = 'H'

        # Group3 fixed shifts
        fixed_shifts_g3 = {
            "Ramesh Polisetty": "G",
            "Srinivasu Cheedalla": "E",
            "Gangavarapu Suneetha": "G",
            "Lakshmi Narayana Rao": "G"
        }
        for emp, sh in fixed_shifts_g3.items():
            for d in range(num_days):
                if plan[emp][d] == '':
                    plan[emp][d] = sh

        # Group4 always S
        for emp in group4:
            for d in range(num_days):
                if plan[emp][d] == '':
                    plan[emp][d] = 'S'

        # Group1 rotation F->S->N
        cycle_g1 = ['F','S','N']
        for emp_idx, emp in enumerate(group1):
            idx = emp_idx
            for d in range(num_days):
                if plan[emp][d] in ['O','H']:
                    idx = (idx + 1) % 3
                elif plan[emp][d] == '':
                    plan[emp][d] = cycle_g1[idx % 3]

        # Group2 rotation (Imran no N)
        cycle_g2 = ['F','S','N']
        for emp in group2:
            if emp == "Imran Khan":
                cycle_imran = ['F','S']
                idx = 0
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 2
                    elif plan[emp][d] == '':
                        plan[emp][d] = cycle_imran[idx % 2]
            else:
                idx = 0
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 3
                    elif plan[emp][d] == '':
                        plan[emp][d] = cycle_g2[idx % 3]

        # --------------------------
        # Step B: Assign coverage pool fairly
        # --------------------------
        night_count = {emp: sum(1 for v in plan[emp] if v=='N') for emp in employees}
        shift_count = {emp: {'F':sum(1 for v in plan[emp] if v=='F'),
                             'S':sum(1 for v in plan[emp] if v=='S'),
                             'N':night_count[emp]} for emp in employees}

        for d in range(num_days):
            blanks = [e for e in coverage_pool if plan[e][d] == '']
            np.random.shuffle(blanks)

            # Nights
            needN = max(0, max_night_per_day - count_shift_on_day(plan,d,'N'))
            night_candidates = sorted([e for e in blanks if shift_count[e]['N'] < max_nights_per_person and e != "Imran Khan"], 
                                      key=lambda x: shift_count[x]['N'])
            for e in night_candidates[:needN]:
                plan[e][d] = 'N'
                shift_count[e]['N'] += 1
                blanks.remove(e)

            # F
            needF = max(0, target_morning - count_shift_on_day(plan,d,'F'))
            f_candidates = sorted(blanks, key=lambda x: shift_count[x]['F'])
            for e in f_candidates[:needF]:
                plan[e][d] = 'F'
                shift_count[e]['F'] += 1
                blanks.remove(e)

            # S
            needS = max(0, target_second - count_shift_on_day(plan,d,'S'))
            s_candidates = sorted(blanks, key=lambda x: shift_count[x]['S'])
            for e in s_candidates[:needS]:
                plan[e][d] = 'S'
                shift_count[e]['S'] += 1
                blanks.remove(e)

            # Remaining blanks -> assign S
            for e in blanks:
                plan[e][d] = 'S'
                shift_count[e]['S'] += 1

        # Ensure no blanks remain
        for e in employees:
            for d in range(num_days):
                if plan[e][d] == '':
                    plan[e][d] = 'S'

        # Save
        df_plan = pd.DataFrame(plan, index=dates).T
        st.session_state['final_plan'] = df_plan
        st.success("Plan generated. Switch to 'Final Plan & Summary' tab to view and download.")

# --------------------------
# TAB 2: Individual Leave
# --------------------------
with tab2:
    st.header("Individual leave / ad-hoc adjustments")
    if 'final_plan' not in st.session_state:
        st.warning("Please generate a plan first under 'Config & Generate' tab.")
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
            cmap = {'F':'lightgreen','S':'lightblue','N':'lightpink',
                    'G':'gold','E':'violet','O':'lightgray','H':'orange','L':'red'}
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map), height=600)

        # Summary counts
        summary = pd.DataFrame({sh:[sum(1 for v in df_plan.loc[e] if v==sh) for e in df_plan.index] 
                                for sh in ['F','S','N','G','E','O','H','L']}, index=df_plan.index)
        st.subheader("Per-person shift counts this month")
        st.dataframe(summary)

        # Daily coverage
        daily_counts = pd.DataFrame({
            'Date': df_plan.columns,
            'F':[sum(1 for e in df_plan.index if df_plan.loc[e,c]=='F') for c in df_plan.columns],
            'S':[sum(1 for e in df_plan.index if df_plan.loc[e,c]=='S') for c in df_plan.columns],
            'N':[sum(1 for e in df_plan.index if df_plan.loc[e,c]=='N') for c in df_plan.columns],
            'O/H/L':[sum(1 for e in df_plan.index if df_plan.loc[e,c] in ('O','H','L')) for c in df_plan.columns]
        })
        st.subheader("Daily coverage summary")
        st.dataframe(daily_counts)

        # Download CSV
        csv = df_plan.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"final_shift_plan_{year}_{month:02d}.csv")

        st.info("Algorithm respects weekoffs, festivals, individual leaves, fixed shifts, and daily F/S/N coverage while distributing night shifts fairly.")
