# full_streamlit_247_roster.py
import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange

st.set_page_config(layout="wide", page_title="24/7 Shift Planner")
st.title("24/7 Employee Shift Planner")

# --------------------------
# Employees
# --------------------------
employees = [
    "Pousali C","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana",
    "Thorat Yashwant","Srivastav Nitin","Kishore Khati Vaibhav","Rupan Venkatesan Anandha",
    "Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen"
]

# --------------------------
# UI: Month Selection
# --------------------------
year = st.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Month", list(range(1,13)), index=9,
                     format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
num_days = monthrange(year, month)[1]
dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

# --------------------------
# Coverage constraints
# --------------------------
max_night_per_day = 2
max_morning_per_day = 3
max_second_per_day = 4
max_night_per_person = 5
min_max_morning_per_person = (5,10)
min_max_second_per_person = (5,10)

# --------------------------
# Button to generate
# --------------------------
if st.button("Generate 24/7 Roster"):
    # Initialize plan
    plan = {emp: ['']*num_days for emp in employees}

    # --------------------------
    # Step 1: Assign weekly offs (2 consecutive days every 4–5 working days)
    # --------------------------
    for emp in employees:
        day = 0
        while day < num_days:
            # 4–5 working days before next off
            work_span = np.random.choice([4,5])
            off_span = 2
            # Assign working days as blank for now
            for i in range(work_span):
                if day < num_days:
                    plan[emp][day] = ''
                    day +=1
            # Assign off days
            for i in range(off_span):
                if day < num_days:
                    plan[emp][day] = 'O'
                    day +=1

    # --------------------------
    # Step 2: Assign shifts F, S, N while respecting constraints
    # --------------------------
    # Night count per person
    night_count = {emp:0 for emp in employees}

    for d in range(num_days):
        # Count assigned shifts
        morning_today = sum(1 for e in employees if plan[e][d]=='F')
        second_today = sum(1 for e in employees if plan[e][d]=='S')
        night_today = sum(1 for e in employees if plan[e][d]=='N')

        # Build list of available employees for this day
        available = [e for e in employees if plan[e][d]=='']

        # Assign Night first
        for _ in range(max_night_per_day - night_today):
            # pick available with night count < max_night_per_person
            candidates = [e for e in available if night_count[e]<max_night_per_person]
            if not candidates:
                break
            chosen = candidates[0]
            plan[chosen][d] = 'N'
            night_count[chosen] +=1
            available.remove(chosen)

        # Assign Morning next
        for _ in range(max_morning_per_day - morning_today):
            if not available:
                break
            chosen = available.pop(0)
            plan[chosen][d] = 'F'

        # Assign Second next
        for _ in range(max_second_per_day - second_today):
            if not available:
                break
            chosen = available.pop(0)
            plan[chosen][d] = 'S'

        # Remaining employees get shifts to maintain coverage
        for e in available:
            # Prefer Second if morning full
            if sum(1 for ee in employees if plan[ee][d]=='S') < max_second_per_day:
                plan[e][d] = 'S'
            elif sum(1 for ee in employees if plan[ee][d]=='F') < max_morning_per_day:
                plan[e][d] = 'F'
            else:
                plan[e][d] = 'N'
                night_count[e] +=1

    # --------------------------
    # Step 3: Create DataFrame
    # --------------------------
    df_plan = pd.DataFrame(plan, index=employees, columns=dates)

    # --------------------------
    # Step 4: Summary
    # --------------------------
    summary = pd.DataFrame({
        'Working Days':[sum(1 for v in df_plan.loc[e] if v!='O') for e in employees],
        'Week Offs':[sum(1 for v in df_plan.loc[e] if v=='O') for e in employees],
        'F':[sum(1 for v in df_plan.loc[e] if v=='F') for e in employees],
        'S':[sum(1 for v in df_plan.loc[e] if v=='S') for e in employees],
        'N':[sum(1 for v in df_plan.loc[e] if v=='N') for e in employees],
    }, index=employees)

    # --------------------------
    # Step 5: Display
    # --------------------------
    st.subheader("24/7 Shift Roster")
    def color_map(val):
        cmap = {'F':'lightgreen','S':'lightblue','N':'lightpink','O':'lightgray'}
        return f'background-color: {cmap.get(val,"")}'
    st.dataframe(df_plan.style.applymap(color_map), height=600)

    st.subheader("Summary per employee")
    st.dataframe(summary)

    # Download
    csv = df_plan.to_csv().encode('utf-8')
    st.download_button("Download CSV", csv, file_name=f"shift_roster_{year}_{month:02d}.csv")
