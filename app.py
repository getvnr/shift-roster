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

# Groups
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
group3 = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
group4 = ["Muppa Divya", "Anil Athkuri", "D Namithananda"]

coverage_pool = [
    "Pousali C", "B Madhurusha", "Chinthalapudi Yaswanth", "Edagotti Kalpana",
    "Thorat Yashwant", "Srivastav Nitin", "Kishore Khati Vaibhav",
    "Rupan Venkatesan Anandha", "Chaudhari Kaustubh", "Shejal Gawade", "Vivek Kushwaha"
]

# --------------------------
# UI Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# --------------------------
# Helper functions
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
    return [d for d in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, d) in idxs]

# --------------------------
# TAB 1 — Config & Generate
# --------------------------
with tab1:
    st.header("Step 1 — Configure month & weekoffs")

    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox("Month", list(range(1,13)), index=9,
                         format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    saturdays = get_weekdays(year, month, [5])
    sundays = get_weekdays(year, month, [6])
    st.markdown(f"**Auto-detected weekends:** Saturdays = {len(saturdays)}, Sundays = {len(sundays)}")

    st.subheader("Weekoff preferences (choose employees for each pattern)")
    friday_saturday_off = st.multiselect("Friday-Saturday", employees)
    sunday_monday_off = st.multiselect("Sunday-Monday", employees)
    saturday_sunday_off = st.multiselect("Saturday-Sunday", employees)
    monday_tuesday_off = st.multiselect("Monday-Tuesday", employees)
    tuesday_wednesday_off = st.multiselect("Tuesday-Wednesday", employees)
    wednesday_thursday_off = st.multiselect("Wednesday-Thursday", employees)
    thursday_friday_off = st.multiselect("Thursday-Friday", employees)

    st.subheader("Festival / Common holidays (optional)")
    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    # Default coverage rules (no UI input)
    max_night_per_day = 2
    target_morning = 3
    target_second = 3
    max_nights_per_person = 6

    st.info("Coverage pool members (auto-assigned for daily F/S/N targets):")
    st.write(", ".join(coverage_pool))

    if st.button("Generate 24/7 Shift + Leave Plan"):
        plan = {emp: ['']*num_days for emp in employees}

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
            days = get_weekoff_days_for_pattern(year, month, pattern)
            for emp in members:
                for d in days:
                    plan[emp][d-1] = 'O'

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

        # Group1 rotation F→S→N
        cycle_g1 = ['F','S','N']
        for emp_idx, emp in enumerate(group1):
            idx = emp_idx
            current_shift = cycle_g1[idx % 3]
            for d in range(num_days):
                if plan[emp][d] in ['O','H']:
                    idx = (idx + 1) % 3
                    current_shift = cycle_g1[idx]
                elif plan[emp][d] == '':
                    plan[emp][d] = current_shift

        # Group2 rotation (Imran skips N)
        cycle_g2 = ['F','S','N']
        for emp_idx, emp in enumerate(group2):
            if emp == "Imran Khan":
                cycle_imran = ['F','S']
                idx = emp_idx
                current_shift = cycle_imran[idx % 2]
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 2
                        current_shift = cycle_imran[idx]
                    elif plan[emp][d] == '':
                        plan[emp][d] = current_shift
            else:
                idx = emp_idx
                current_shift = cycle_g2[idx % 3]
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 3
                        current_shift = cycle_g2[idx]
                    elif plan[emp][d] == '':
                        plan[emp][d] = current_shift

        # Helper to count shift on day
        def count_shift_on_day(pln, day_index, shift_code):
            return sum(1 for e in employees if pln[e][day_index] == shift_code)

        # Assign coverage pool to fill F/S/N
        night_count_by_person = {e: sum(1 for v in plan[e] if v == 'N') for e in employees}
        fallback_candidates = [e for e in employees if e not in group3 + group4]
        rng = np.random.default_rng(seed=(year*100 + month))

        for d in range(num_days):
            n_existing_N = count_shift_on_day(plan, d, 'N')
            n_existing_F = count_shift_on_day(plan, d, 'F')
            n_existing_S = count_shift_on_day(plan, d, 'S')

            need_N = max(0, max_night_per_day - n_existing_N)
            need_F = max(0, target_morning - n_existing_F)
            need_S = max(0, target_second - n_existing_S)

            available = [e for e in coverage_pool if plan[e][d] == '']
            if len(available) < (need_N + need_F + need_S):
                extras = [e for e in fallback_candidates if plan[e][d] == '' and e not in available]
                available += extras
            if available:
                available = list(rng.permutation(available))

            def pick_for_n(avail):
                candidates = [e for e in avail if night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan"]
                candidates_sorted = sorted(candidates, key=lambda x: (night_count_by_person.get(x,0), rng.integers(0,1000)))
                return candidates_sorted[0] if candidates_sorted else None

            for _ in range(need_N):
                candidate = pick_for_n(available)
                if not candidate:
                    fallback = [e for e in employees if plan[e][d] == '' and night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan"]
                    fallback = list(rng.permutation(fallback))
                    candidate = fallback[0] if fallback else None
                if candidate:
                    plan[candidate][d] = 'N'
                    night_count_by_person[candidate] += 1
                    if candidate in available:
                        available.remove(candidate)

            for _ in range(need_F):
                if not available: break
                plan[available.pop(0)][d] = 'F'

            for _ in range(need_S):
                if not available: break
                plan[available.pop(0)][d] = 'S'

            n_existing_N = count_shift_on_day(plan, d, 'N')
            n_existing_F = count_shift_on_day(plan, d, 'F')
            n_existing_S = count_shift_on_day(plan, d, 'S')
            remaining_blanks = [e for e in employees if plan[e][d] == '']
            for e in remaining_blanks:
                if n_existing_F < target_morning:
                    plan[e][d] = 'F'
                    n_existing_F += 1
                elif n_existing_S < target_second:
                    plan[e][d] = 'S'
                    n_existing_S += 1
                elif n_existing_N < max_night_per_day and night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan":
                    plan[e][d] = 'N'
                    night_count_by_person[e] += 1
                    n_existing_N += 1
                else:
                    plan[e][d] = 'S'
                    n_existing_S += 1

        for e in employees:
            for d in range(num_days):
                if plan[e][d] == '':
                    plan[e][d] = 'S'

        df_plan = pd.DataFrame(plan, index=dates).T
        st.session_state['final_plan'] = df_plan
        st.success("Plan generated. Switch to 'Final Plan & Summary' tab to view and download.")

# --------------------------
# TAB 2 — Individual Leave
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
# TAB 3 — Final Plan & Summary
# --------------------------
with tab3:
    st.header("Final Shift Plan and Summary")
    if 'final_plan' not in st.session_state:
        st.warning("No plan available. Generate first.")
    else:
        df_plan = st.session_state['final_plan']

        def color_map(val):
            cmap = {
                'F': 'lightgreen','S':'lightblue','N':'lightpink',
                'G':'gold','E':'violet','O':'lightgray','H':'orange','L':'red'
            }
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map), height=600)

        summary = pd.DataFrame({
            'F': [sum(1 for v in df_plan.loc[e] if v=='F') for e in df_plan.index],
            'S': [sum(1 for v in df_plan.loc[e] if v=='S') for e in df_plan.index],
            'N': [sum(1 for v in df_plan.loc[e] if v=='N') for e in df_plan.index],
            'G': [sum(1 for v in df_plan.loc[e] if v=='G') for e in df_plan.index],
            'E': [sum(1 for v in df_plan.loc[e] if v=='E') for e in df_plan.index],
            'O': [sum(1 for v in df_plan.loc[e] if v=='O') for e in df_plan.index],
            'H': [sum(1 for v in df_plan.loc[e] if v=='H') for e in df_plan.index],
            'L': [sum(1 for v in df_plan.loc[e] if v=='L') for e in df_plan.index],
        }, index=df_plan.index)

        st.subheader("Per-person shift counts this month")
        st.dataframe(summary)

        daily_counts = pd.DataFrame({
            'Date': df_plan.columns,
            'F': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='F') for col in df_plan.columns],
            'S': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='S') for col in df_plan.columns],
            'N': [sum(1 for e in df_plan.index if df_plan.loc[e, col]=='N') for col in df_plan.columns],
            'O/H/L': [sum(1 for e in df_plan.index if df_plan.loc[e, col] in ('O','H','L')) for col in df_plan.columns]
        })
        st.subheader("Daily coverage summary")
        st.dataframe(daily_counts)

        csv = df_plan.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"final_shift_plan_{year}_{month:02d}.csv")

        st.info("Notes: Algorithm applies default coverage rules: "
                "Max 2 on Night, 3 on Morning, 3 on Second, max 6 nights per person.")
