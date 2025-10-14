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

# Fixed employees who won't be disturbed
fixed_employees = [
    "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan",
    "Ajay Chidipotu","Imran Khan","Sammeta Balachander",
    "Ramesh Polisetty","Srinivasu Cheedalla","Gangavarapu Suneetha",
    "Lakshmi Narayana Rao","Muppa Divya","Anil Athkuri","D Namithananda"
]

# Groups (for rotation logic)
group1 = ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]  
group2 = ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]             
group3 = ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]  
group4 = ["Muppa Divya", "Anil Athkuri", "D Namithananda"]                  

# Pool for 24/7 coverage
coverage_pool = [e for e in employees if e not in fixed_employees]

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
    idxs = patterns[pattern]
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in idxs]

def count_shift_on_day(pln, day_index, shift_code):
    return sum(1 for e in pln if pln[e][day_index]==shift_code)

# --------------------------
# Streamlit UI
# --------------------------
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

with tab1:
    st.header("Step 1 — Configure month & weekoffs")
    year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
    month = st.selectbox("Month", list(range(1,13)), index=9,
                         format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    # Weekoff selection
    st.subheader("Weekoff preferences (choose employees for each pattern)")
    weekoff_patterns = ["Friday-Saturday","Sunday-Monday","Saturday-Sunday",
                        "Monday-Tuesday","Tuesday-Wednesday","Wednesday-Thursday","Thursday-Friday"]
    weekoff_assignments = {}
    for pattern in weekoff_patterns:
        weekoff_assignments[pattern] = st.multiselect(pattern, employees)

    # Festival days
    st.subheader("Festival / Common holidays (optional)")
    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    st.subheader("Coverage constraints")
    max_night_per_day = st.number_input("Max people on Night (N) per day", min_value=1, max_value=10, value=2)
    target_morning = st.number_input("Max people on Morning (F) per day", min_value=1, max_value=10, value=3)
    target_second = st.number_input("Max people on Second (S) per day", min_value=1, max_value=10, value=4)
    max_nights_per_person = st.number_input("Max nights per person in month", min_value=0, max_value=num_days, value=6)

    if st.button("Generate 24/7 Shift + Leave Plan"):
        plan = {emp:['']*num_days for emp in employees}

        # --------------------------
        # Apply weekoffs consistently
        for pattern, members in weekoff_assignments.items():
            days = get_weekoff_days_for_pattern(year, month, pattern)
            for emp in members:
                for d in days:
                    plan[emp][d-1] = 'O'

        # Festival days
        for emp in employees:
            for f in festival_days:
                plan[emp][f-1] = 'H'

        # --------------------------
        # Fixed shifts for group3 and group4
        fixed_shifts_g3 = {"Ramesh Polisetty":"G","Srinivasu Cheedalla":"E",
                           "Gangavarapu Suneetha":"G","Lakshmi Narayana Rao":"G"}
        for emp, sh in fixed_shifts_g3.items():
            for d in range(num_days):
                if plan[emp][d]=='':
                    plan[emp][d] = sh
        for emp in group4:
            for d in range(num_days):
                if plan[emp][d]=='':
                    plan[emp][d]='S'

        # Group1 rotation F->S->N after O/H
        cycle_g1 = ['F','S','N']
        for emp_idx, emp in enumerate(group1):
            idx = emp_idx
            for d in range(num_days):
                if plan[emp][d] in ['O','H']:
                    idx = (idx+1)%3
                elif plan[emp][d]=='':
                    plan[emp][d] = cycle_g1[idx%3]

        # Group2 rotation (Imran no N)
        for emp_idx, emp in enumerate(group2):
            if emp=='Imran Khan':
                cycle_imran=['F','S']
                idx=emp_idx
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx=(idx+1)%2
                    elif plan[emp][d]=='':
                        plan[emp][d]=cycle_imran[idx%2]
            else:
                idx=emp_idx
                for d in range(num_days):
                    if plan[emp][d] in ['O','H']:
                        idx=(idx+1)%3
                    elif plan[emp][d]=='':
                        plan[emp][d]=cycle_g1[idx%3]

        # --------------------------
        # Coverage pool assignment (respect max F/S/N per day)
        night_count = {e:0 for e in employees}
        for e in employees:
            night_count[e] = sum(1 for v in plan[e] if v=='N')

        rng = np.random.default_rng(seed=(year*100+month))

        for d in range(num_days):
            # Skip H/O already applied
            n_N = count_shift_on_day(plan,d,'N')
            n_F = count_shift_on_day(plan,d,'F')
            n_S = count_shift_on_day(plan,d,'S')
            need_N = max(0, max_night_per_day - n_N)
            need_F = max(0, target_morning - n_F)
            need_S = max(0, target_second - n_S)

            available = [e for e in coverage_pool if plan[e][d]=='']
            if len(available)<(need_N+need_F+need_S):
                extras = [e for e in employees if plan[e][d]=='' and e not in fixed_employees and e not in available]
                available+=extras
            available = list(rng.permutation(available))

            # Assign N first
            n_assigned=0
            for _ in range(need_N):
                candidate=None
                sorted_candidates=sorted([e for e in available if night_count[e]<max_nights_per_person and e!='Imran Khan'],
                                         key=lambda x:(night_count[x],rng.integers(0,1000)))
                if sorted_candidates:
                    candidate=sorted_candidates[0]
                if candidate:
                    plan[candidate][d]='N'
                    night_count[candidate]+=1
                    available.remove(candidate)
                    n_assigned+=1

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

            # Fill remaining blanks
            for e in [x for x in employees if plan[x][d]=='']:
                plan[e][d]='S'

        df_plan = pd.DataFrame(plan,index=dates).T
        st.session_state['final_plan']=df_plan
        st.success("Plan generated. Switch to 'Final Plan & Summary' tab.")

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
                df.loc[emp,d]='L'
            st.session_state['final_plan']=df
            st.success(f"Applied individual leave for {emp}")

with tab3:
    st.header("Final Shift Plan and Summary")
    if 'final_plan' not in st.session_state:
        st.warning("No plan available. Generate first.")
    else:
        df_plan=st.session_state['final_plan']

        def color_map(val):
            cmap={'F':'lightgreen','S':'lightblue','N':'lightpink','G':'gold','E':'violet','O':'lightgray','H':'orange','L':'red'}
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map),height=600)

        summary=pd.DataFrame({sh:[sum(1 for v in df_plan.loc[e] if v==sh) for e in df_plan.index] for sh in ['F','S','N','G','E','O','H','L']},index=df_plan.index)
        st.subheader("Per-person shift counts this month")
        st.dataframe(summary)

        daily_counts=pd.DataFrame({'Date':df_plan.columns,
                                   'F':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='F') for col in df_plan.columns],
                                   'S':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='S') for col in df_plan.columns],
                                   'N':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='N') for col in df_plan.columns],
                                   'O/H/L':[sum(1 for e in df_plan.index if df_plan.loc[e,col] in ('O','H','L')) for col in df_plan.columns]})
        st.subheader("Daily coverage summary")
        st.dataframe(daily_counts)

        csv=df_plan.to_csv().encode('utf-8')
        st.download_button("Download CSV",csv,file_name=f"final_shift_plan_{year}_{month:02d}.csv")
