import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange

st.set_page_config(layout="wide", page_title="24/7 Shift Planner")
st.title("24/7 Shift Planner — Continuous Coverage")

# Employees
employees = [
    "Pousali C","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana",
    "Thorat Yashwant","Srivastav Nitin","Kishore Khati Vaibhav","Rupan Venkatesan Anandha",
    "Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen"
]

# Tabs
tab1, tab2, tab3 = st.tabs(["🗓️ Configure & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# TAB 1: Configuration & Generate
with tab1:
    st.header("Configure month & generate 24/7 roster")
    year = st.number_input("Year", 2023, 2100, 2025)
    month = st.selectbox("Month", range(1,13), index=9, format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    min_morning = st.number_input("Min Morning (F) per employee per month", 5, 10, 5)
    max_morning = st.number_input("Max Morning (F) per employee per month", 5, 10, 10)
    min_second = st.number_input("Min Second (S) per employee per month", 5, 10, 5)
    max_second = st.number_input("Max Second (S) per employee per month", 5, 10, 10)
    max_night_per_person = st.number_input("Max Night (N) per employee per month", 0, 5, 5)

    max_night_per_day = st.number_input("Max Night per day", 1, 5, 2)
    min_morning_per_day = st.number_input("Min Morning per day", 2, 5, 2)
    max_morning_per_day = st.number_input("Max Morning per day", 2, 5, 3)
    min_second_per_day = st.number_input("Min Second per day", 3, 5, 3)
    max_second_per_day = st.number_input("Max Second per day", 3, 5, 4)

    if st.button("Generate 24/7 Roster"):
        plan = pd.DataFrame('', index=employees, columns=dates)
        night_count = {emp:0 for emp in employees}
        f_count = {emp:0 for emp in employees}
        s_count = {emp:0 for emp in employees}
        rng = np.random.default_rng(seed=(year*100+month))

        # Generate weekly offs per employee: 2 consecutive days every 4-5 working days
        weekly_off_days = {emp:[] for emp in employees}
        for emp in employees:
            day = 0
            while day < num_days:
                start_off = min(day + rng.integers(4,6), num_days-1)
                off_days = [start_off, min(start_off+1, num_days-1)]
                weekly_off_days[emp].extend(off_days)
                day = start_off + 2

        # Assign shifts with continuity until weekly off
        for d_idx, date in enumerate(dates):
            assigned_N = 0
            assigned_F = 0
            assigned_S = 0

            shuffled_emps = list(rng.permutation(employees))
            for emp in shuffled_emps:
                if plan.loc[emp, date] != '':
                    continue
                # Weekly off
                if d_idx in weekly_off_days[emp]:
                    plan.loc[emp, date] = 'O'
                # Festival
                elif d_idx+1 in festival_days:
                    plan.loc[emp, date] = 'H'
                else:
                    # Continue last shift if not off
                    last_shift = plan.loc[emp, dates[d_idx-1]] if d_idx>0 else ''
                    if last_shift in ['F','S','N']:
                        shift = last_shift
                    else:
                        # Assign new shift respecting min/max per month and per day
                        if assigned_N < max_night_per_day and night_count[emp] < max_night_per_person:
                            shift = 'N'
                            night_count[emp] += 1
                            assigned_N += 1
                        elif assigned_F < max_morning_per_day and f_count[emp] < max_morning:
                            shift = 'F'
                            f_count[emp] += 1
                            assigned_F += 1
                        elif assigned_S < max_second_per_day and s_count[emp] < max_second:
                            shift = 'S'
                            s_count[emp] += 1
                            assigned_S += 1
                        else:
                            # Fill remaining coverage
                            if f_count[emp] < max_morning:
                                shift = 'F'
                                f_count[emp] +=1
                                assigned_F +=1
                            elif s_count[emp] < max_second:
                                shift = 'S'
                                s_count[emp] +=1
                                assigned_S +=1
                            else:
                                shift = 'S' # fallback
                    plan.loc[emp, date] = shift

        st.session_state['final_plan'] = plan
        st.success("24/7 Roster generated successfully!")

# TAB 2: Individual leave
with tab2:
    st.header("Individual leave / ad-hoc adjustments")
    if 'final_plan' not in st.session_state:
        st.warning("Generate a roster first.")
    else:
        df = st.session_state['final_plan']
        emp = st.selectbox("Employee", employees)
        day = st.multiselect("Select date(s) to mark as Individual Leave (L)", df.columns.tolist())
        if st.button("Apply Individual Leave"):
            for d in day:
                df.loc[emp, d] = 'L'
            st.session_state['final_plan'] = df
            st.success(f"Applied individual leave for {emp} on {', '.join(day)}")

# TAB 3: Final Plan & Summary
with tab3:
    st.header("Final 24/7 Shift Plan")
    if 'final_plan' not in st.session_state:
        st.warning("No plan available. Generate first.")
    else:
        df_plan = st.session_state['final_plan']

        def color_map(val):
            cmap = {'F':'lightgreen','S':'lightblue','N':'lightpink','O':'lightgray','H':'orange','L':'red'}
            return f'background-color: {cmap.get(val,"")}'
        st.dataframe(df_plan.style.applymap(color_map), height=600)

        summary = pd.DataFrame({
            'F':[sum(1 for v in df_plan.loc[e] if v=='F') for e in df_plan.index],
            'S':[sum(1 for v in df_plan.loc[e] if v=='S') for e in df_plan.index],
            'N':[sum(1 for v in df_plan.loc[e] if v=='N') for e in df_plan.index],
            'O':[sum(1 for v in df_plan.loc[e] if v=='O') for e in df_plan.index],
            'H':[sum(1 for v in df_plan.loc[e] if v=='H') for e in df_plan.index],
            'L':[sum(1 for v in df_plan.loc[e] if v=='L') for e in df_plan.index],
            'Working Days':[sum(1 for v in df_plan.loc[e] if v in ['F','S','N']) for e in df_plan.index],
            'Week Off':[sum(1 for v in df_plan.loc[e] if v=='O') for e in df_plan.index]
        }, index=df_plan.index)
        st.subheader("Per-person shift counts, working days & week offs")
        st.dataframe(summary)

        daily_counts = pd.DataFrame({
            'Date': df_plan.columns,
            'F':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='F') for col in df_plan.columns],
            'S':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='S') for col in df_plan.columns],
            'N':[sum(1 for e in df_plan.index if df_plan.loc[e,col]=='N') for col in df_plan.columns],
            'O/H/L':[sum(1 for e in df_plan.index if df_plan.loc[e,col] in ('O','H','L')) for col in df_plan.columns]
        })
        st.subheader("Daily coverage summary")
        st.dataframe(daily_counts)

        csv = df_plan.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"24_7_roster_{year}_{month:02d}.csv")
