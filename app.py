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

# Groups (unchanged)
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]
group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]
group3 = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]
group4 = ["Muppa Divya", "Anil Athkuri", "D Namithananda"]

# --------------------------
# Coverage pool (the people you listed) — they will be used to provide 24/7 coverage
# --------------------------
coverage_pool = [
    "Pousali C",               # Group5
    "B Madhurusha",            # Group5
    "Chinthalapudi Yaswanth",  # Group5
    "Edagotti Kalpana",        # Group6
    "Thorat Yashwant",         # Group6
    "Srivastav Nitin",         # Group7
    "Kishore Khati Vaibhav",   # Group7
    "Rupan Venkatesan Anandha",# Group8
    "Chaudhari Kaustubh",      # Group8
    "Shejal Gawade",           # Group9
    "Vivek Kushwaha",          # Group9
    "Abdul Mukthiyar Basha",   # Group10
    "M Naveen"                 # Group10
]

# --------------------------
# UI: Tabs
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# --------------------------
# Helpers: weekday / weekends
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
# TAB 1: Configuration & Generate
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

    st.info("Coverage pool members (these staff will be assigned to meet daily F/S/N targets):")
    st.write(", ".join(coverage_pool))

    # --------------------------
    # Default coverage constraints (applies to all days including weekends)
    # Night max: 2
    # Morning target: try 3 (acceptable 2-3)
    # Second target: try 4 (acceptable 3-4)
    # Max nights per person (for coverage_pool): 5  <-- UPDATED as requested
    # --------------------------
    max_night_per_day = 2
    target_morning = 3
    target_second = 4
    max_nights_per_person = 5  # <-- user requested: max night shift per coverage engineer = 5

    # Button to generate
    if st.button("Generate 24/7 Shift + Leave Plan"):
        # --------------------------
        # Step A: initialize plan with blanks, apply weekoffs and festival and group fixed shifts
        # --------------------------
        plan = {emp: ['']*num_days for emp in employees}

        # Apply weekoff patterns chosen by user (keeps behavior for other engineers unchanged)
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

        # Apply festival days
        for emp in employees:
            for f in festival_days:
                plan[emp][f-1] = 'H'

        # Group3 fixed shifts (unchanged)
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

        # Group4 always S (unchanged)
        for emp in group4:
            for d in range(num_days):
                if plan[emp][d] == '':
                    plan[emp][d] = 'S'

        # Group1 rotation F->S->N rotate after off day (unchanged)
        cycle_g1 = ['F','S','N']
        shift_index_g1 = 0
        for emp_idx, emp in enumerate(group1):
            idx = shift_index_g1 + emp_idx
            current_shift = cycle_g1[idx % 3]
            for d in range(num_days):
                if plan[emp][d] in ['O','H']:
                    idx = (idx + 1) % 3
                    current_shift = cycle_g1[idx]
                elif plan[emp][d] == '':
                    plan[emp][d] = current_shift

        # Group2 rotation but Imran no N (unchanged)
        cycle_g2 = ['F','S','N']
        shift_index_g2 = 0
        for emp_idx, emp in enumerate(group2):
            if emp == "Imran Khan":
                cycle_imran = ['F','S']
                idx = shift_index_g2 + emp_idx
                current_shift = cycle_imran[idx % 2]
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 2
                        current_shift = cycle_imran[idx]
                    elif plan[emp][d] == '':
                        plan[emp][d] = current_shift
            else:
                idx = shift_index_g2 + emp_idx
                current_shift = cycle_g2[idx % 3]
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx = (idx + 1) % 3
                        current_shift = cycle_g2[idx]
                    elif plan[emp][d] == '':
                        plan[emp][d] = current_shift

        # --------------------------
        # NEW: Apply 5-on / 2-off cycle for coverage_pool members
        # (Every 5 working days -> the next 2 days are marked O, repeating)
        # This is applied AFTER explicit weekoff selections and festivals so those are respected.
        # Also ensures weekend/festival offs are counted toward off-days.
        # --------------------------
        for emp in coverage_pool:
            work_streak = 0
            d = 0
            while d < num_days:
                # If day already O/H (user weekoff or festival), treat as off and reset streak.
                if plan[emp][d] in ['O', 'H']:
                    work_streak = 0
                    d += 1
                    continue
                # If currently in work mode (up to 5 consecutive work days)
                if work_streak < 5:
                    # leave blank for now (actual F/S/N assignment will happen later)
                    work_streak += 1
                    d += 1
                else:
                    # give two consecutive off days, if possible, mark as O (do not override H)
                    off_count = 0
                    while off_count < 2 and d < num_days:
                        if plan[emp][d] == '':
                            plan[emp][d] = 'O'
                            off_count += 1
                            d += 1
                        elif plan[emp][d] in ['O','H']:
                            # if already off/holiday, still count it towards two-day off
                            off_count += 1
                            d += 1
                        else:
                            # fixed-shift day or other assigned day — treat as work and break
                            break
                    work_streak = 0

        # --------------------------
        # Step B: Assign flexible pool to meet daily targets
        # Strategy (greedy):
        # - For each day:
        #   * respect existing assignments (O/H/L/G/E/S from fixed groups or weekoffs)
        #   * determine how many more F, S, N are required to meet targets
        #   * pick candidates from coverage_pool who are available and haven't exceeded max_nights_per_person
        #   * prefer to distribute nights fairly among pool (choose people with lowest night count first)
        #   * ensure daily N <= max_night_per_day
        #   * if not enough pool members, fallback to other available employees (but keep fixed groups unchanged)
        # --------------------------
        def count_shift_on_day(pln, day_index, shift_code):
            return sum(1 for e in employees if pln[e][day_index] == shift_code)

        # Initialize night counters
        night_count_by_person = {emp: sum(1 for v in plan[emp] if v == 'N') for emp in employees}

        # Fallback candidates = everyone except group3 fixed G/E and group4 fixed S
        fallback_candidates = [e for e in employees if e not in group3 + group4]

        # deterministic rng for fairness
        rng = np.random.default_rng(seed=(year*100 + month))

        for d in range(num_days):
            n_existing_N = count_shift_on_day(plan, d, 'N')
            n_existing_F = count_shift_on_day(plan, d, 'F')
            n_existing_S = count_shift_on_day(plan, d, 'S')

            need_N = max(0, max_night_per_day - n_existing_N)
            need_F = max(0, target_morning - n_existing_F)
            need_S = max(0, target_second - n_existing_S)

            # Build candidate pool for this day: coverage_pool members who are blank (available)
            available = [e for e in coverage_pool if plan[e][d] == '']
            # If not enough, include fallback candidates (keeps others unchanged where possible)
            if len(available) < (need_N + need_F + need_S):
                extras = [e for e in fallback_candidates if plan[e][d] == '' and e not in available]
                available += extras

            if available:
                available = list(rng.permutation(available))

            # pick_for_n respects per-person night cap (max_nights_per_person)
            def pick_for_n(avail_list):
                candidates = [e for e in avail_list if night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan"]
                candidates_sorted = sorted(candidates, key=lambda x: (night_count_by_person.get(x,0), rng.integers(0,1000)))
                return candidates_sorted[0] if candidates_sorted else None

            # Assign Nights first
            for _ in range(need_N):
                candidate = pick_for_n(available)
                if not candidate:
                    # fallback to any available person who still under nights cap
                    fallback = [e for e in employees if plan[e][d] == '' and night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan"]
                    fallback = list(rng.permutation(fallback))
                    candidate = fallback[0] if fallback else None
                if candidate:
                    plan[candidate][d] = 'N'
                    night_count_by_person[candidate] = night_count_by_person.get(candidate,0) + 1
                    if candidate in available:
                        available.remove(candidate)

            # Assign F next
            for _ in range(need_F):
                if not available:
                    break
                candidate = available.pop(0)
                plan[candidate][d] = 'F'

            # Assign S next
            for _ in range(need_S):
                if not available:
                    break
                candidate = available.pop(0)
                plan[candidate][d] = 'S'

            # Fill remaining blanks sensibly (prefer S if morning full)
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
                else:
                    if n_existing_N < max_night_per_day and night_count_by_person.get(e,0) < max_nights_per_person and e != "Imran Khan":
                        plan[e][d] = 'N'
                        night_count_by_person[e] = night_count_by_person.get(e,0) + 1
                        n_existing_N += 1
                    else:
                        plan[e][d] = 'S'
                        n_existing_S += 1

        # --------------------------
        # Step C: Final touches
        # Ensure no blanks remain (set any remaining blank to S)
        for e in employees:
            for d in range(num_days):
                if plan[e][d] == '':
                    plan[e][d] = 'S'

        # Save to session
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
            cmap = {
                'F': 'lightgreen','S':'lightblue','N':'lightpink',
                'G':'gold','E':'violet','O':'lightgray','H':'orange','L':'red'
            }
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map), height=600)

        # Summary counts
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

        # Daily coverage check: show counts per day for key shifts (F,S,N)
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

        st.info(
            "Notes: - Coverage pool members (listed) are used to provide 24/7 coverage. "
            "Night max = 2, Morning target = 3 (acceptable 2-3), Second target = 4 (acceptable 3-4). "
            "Coverage pool follows a 5-on / 2-off cycle (respects explicit user weekoffs and festival days). "
            "Max nights per coverage engineer this month = 5. Other engineers' fixed/group shifts are unchanged."
        )
