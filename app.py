# full_streamlit_shift_planner.py
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

# Groups (fixed / special)
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
group3 = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
group4 = ["Muppa Divya", "Anil Athkuri", "D Namithananda"]

fixed_employees = group1 + group2 + group3 + group4

# Pool for 24/7 coverage
coverage_pool = [e for e in employees if e not in fixed_employees]

# --------------------------
# Helpers
# --------------------------
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in weekday_indices]

def get_weekoff_days_for_pattern(year, month, pattern):
    patterns = {
        "Friday-Saturday": [4, 5],
        "Sunday-Monday": [6, 0],
        "Saturday-Sunday": [5, 6],
        "Monday-Tuesday": [0, 1],
        "Tuesday-Wednesday": [1, 2],
        "Wednesday-Thursday": [2, 3],
        "Thursday-Friday": [3, 4]
    }
    idxs = patterns[pattern]
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in idxs]

def count_shift_on_day(pln, day_index, shift_code):
    return sum(1 for e in employees if pln[e][day_index] == shift_code)

# --------------------------
# Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# --------------------------
# TAB 1: Config & Generate
# --------------------------
with tab1:
    st.header("Step 1 — Configure month & weekoffs")
    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox("Month", list(range(1,13)), index=9,
                         format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    # Auto-detect weekends
    saturdays = get_weekdays(year, month, [5])
    sundays = get_weekdays(year, month, [6])
    st.markdown(f"**Auto-detected:** Saturdays = {len(saturdays)}, Sundays = {len(sundays)}")

    # Weekoff preferences
    st.subheader("Weekoff preferences (choose employees for each pattern)")
    patterns = ["Friday-Saturday", "Sunday-Monday", "Saturday-Sunday",
                "Monday-Tuesday", "Tuesday-Wednesday", "Wednesday-Thursday", "Thursday-Friday"]
    weekoff_selection = {}
    for p in patterns:
        weekoff_selection[p] = st.multiselect(p, employees)

    # Festival days
    st.subheader("Festival / Common holidays (optional)")
    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    # Coverage constraints
    st.subheader("Coverage constraints")
    max_night_per_day = st.number_input("Max people on Night (N) per weekday", min_value=1, max_value=10, value=2)
    target_morning = st.number_input("Max people on Morning (F) per weekday", min_value=1, max_value=10, value=3)
    target_second = st.number_input("Max people on Second (S) per weekday", min_value=1, max_value=10, value=4)
    max_nights_per_person = st.number_input("Max nights per person in month", min_value=0, max_value=num_days, value=6)

    st.subheader("Weekend coverage constraints")
    weekend_max_N = st.number_input("Max people on Night (N) per weekend day", min_value=1, max_value=10, value=2)
    weekend_max_F = st.number_input("Max people on Morning (F) per weekend day", min_value=1, max_value=10, value=3)
    weekend_max_S = st.number_input("Max people on Second (S) per weekend day", min_value=1, max_value=10, value=4)

    st.info("Coverage pool members:")
    st.write(", ".join(coverage_pool))

    if st.button("Generate 24/7 Shift + Leave Plan"):
        # Initialize
        plan = {emp: ['']*num_days for emp in employees}

        # Apply weekoff patterns
        for pattern, members in weekoff_selection.items():
            days = get_weekoff_days_for_pattern(year, month, pattern)
            for emp in members:
                for d in days:
                    plan[emp][d-1] = 'O'

        # Apply festival days
        for emp in employees:
            for f in festival_days:
                plan[emp][f-1] = 'H'

        # Fixed group shifts
        fixed_shifts_g3 = {"Ramesh Polisetty":"G","Srinivasu Cheedalla":"E",
                           "Gangavarapu Suneetha":"G","Lakshmi Narayana Rao":"G"}
        for emp, sh in fixed_shifts_g3.items():
            for d in range(num_days):
                if plan[emp][d]=='':
                    plan[emp][d]=sh

        for emp in group4:
            for d in range(num_days):
                if plan[emp][d]=='':
                    plan[emp][d]='S'

        # Group1 rotation F->S->N after off
        cycle_g1 = ['F','S','N']
        for idx_emp, emp in enumerate(group1):
            idx_shift = idx_emp
            for d in range(num_days):
                if plan[emp][d] in ['O','H']:
                    idx_shift = (idx_shift + 1) % 3
                elif plan[emp][d]=='':
                    plan[emp][d] = cycle_g1[idx_shift]

        # Group2 rotation, Imran no N
        for idx_emp, emp in enumerate(group2):
            if emp=="Imran Khan":
                cycle_imran = ['F','S']
                idx_shift = idx_emp
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx_shift = (idx_shift+1)%2
                    elif plan[emp][d]=='':
                        plan[emp][d]=cycle_imran[idx_shift]
            else:
                cycle_g2 = ['F','S','N']
                idx_shift = idx_emp
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx_shift = (idx_shift+1)%3
                    elif plan[emp][d]=='':
                        plan[emp][d]=cycle_g2[idx_shift]

        # Coverage pool assignment with weekday/weekend limits
        night_count = {e:sum(1 for v in plan[e] if v=='N') for e in employees}
        rng = np.random.default_rng(seed=(year*100+month))
        weekend_days = [d for d in range(1, num_days+1) if weekday(year, month, d) in [5,6]]

        for d in range(num_days):
            if (d+1) in weekend_days:
                max_n = weekend_max_N
                max_f = weekend_max_F
                max_s = weekend_max_S
            else:
                max_n = max_night_per_day
                max_f = target_morning
                max_s = target_second

            n_N = count_shift_on_day(plan,d,'N')
            n_F = count_shift_on_day(plan,d,'F')
            n_S = count_shift_on_day(plan,d,'S')
            need_N = max(0, max_n - n_N)
            need_F = max(0, max_f - n_F)
            need_S = max(0, max_s - n_S)

            available = [e for e in coverage_pool if plan[e][d]=='']
            if len(available)<(need_N+need_F+need_S):
                extras = [e for e in employees if plan[e][d]=='' and e not in fixed_employees and e not in available]
                available += extras
            available = list(rng.permutation(available))

            # Assign N
            for _ in range(need_N):
                candidates = sorted([e for e in available if night_count[e]<max_nights_per_person and e!='Imran Khan'],
                                    key=lambda x: (night_count[x], rng.integers(0,1000)))
                if candidates:
                    cand = candidates[0]
                    plan[cand][d]='N'
                    night_count[cand]+=1
                    available.remove(cand)
            # Assign F
            for _ in range(need_F):
                if not available: break
                plan[available[0]][d]='F'
                available.pop(0)
            # Assign S
            for _ in range(need_S):
                if not available: break
                plan[available[0]][d]='S'
                available.pop(0)
            # Fill remaining
            for e in [x for x in employees if plan[x][d]=='']:
                plan[e][d]='S'

        # Ensure no blanks
        for e in employees:
            for d in range(num_days):
                if plan[e][d]=='':
                    plan[e][d]='S'

        # Save session
        df_plan = pd.DataFrame(plan, index=employees, columns=dates)
        st.session_state['final_plan'] = df_plan
        st.success("Plan generated. Switch to 'Final Plan & Summary' tab to view and download.")
