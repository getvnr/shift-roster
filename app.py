import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

st.set_page_config(layout="wide", page_title="Employee Leave & Shift Planner")
st.title("Employee Leave & Shift Planner — 24/7 Coverage")

# Employees
employees = [
    "Pousali C","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana",
    "Thorat Yashwant","Srivastav Nitin","Kishore Khati Vaibhav","Rupan Venkatesan Anandha",
    "Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha","M Naveen"
]

# Tabs
tab1, tab2, tab3 = st.tabs(["🗓️ Config & Generate", "🙋 Individual Leave", "📊 Final Plan & Summary"])

# Helpers
def get_weekdays(year, month, weekday_indices):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in weekday_indices]

def get_weekoff_days(year, month):
    saturdays = get_weekdays(year, month, [5])
    sundays = get_weekdays(year, month, [6])
    return sorted(saturdays + sundays)

# TAB 1
with tab1:
    st.header("Step 1 — Configure month & generate roster")
    year = st.number_input("Year", 2023, 2100, 2025)
    month = st.selectbox("Month", range(1,13), index=9, format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))

    max_night_per_day = st.number_input("Max Night (N) per day", 1, 10, 2)
    min_morning = st.number_input("Min Morning (F) per day", 1, 10, 2)
    max_morning = st.number_input("Max Morning (F) per day", 1, 10, 3)
    min_second = st.number_input("Min Second (S) per day", 1, 10, 3)
    max_second = st.number_input("Max Second (S) per day", 1, 10, 4)
    max_nights_per_person = st.number_input("Max nights per person per month", 0, num_days, 5)

    if st.button("Generate 24/7 Shift Plan"):
        plan = pd.DataFrame('', index=employees, columns=dates)
        night_count = {emp:0 for emp in employees}

        # Apply weekend offs
        weekoff_days = get_weekoff_days(year, month)
        for emp in employees:
            for d in weekoff_days:
                plan.loc[emp, dates[d-1]] = 'O'

        # Apply festival days
        for emp in employees:
            for f in festival_days:
                plan.loc[emp, dates[f-1]] = 'H'

        rng = np.random.default_rng(seed=(year*100 + month))

        for d_idx, date in enumerate(dates):
            available = [e for e in employees if plan.loc[e,date]=='']

            # Assign Night
            candidates = [e for e in available if night_count[e] < max_nights_per_person]
            candidates_sorted = sorted(candidates, key=lambda x: night_count[x])
            night_assigned = candidates_sorted[:max_night_per_day]
            for e in night_assigned:
                plan.loc[e,date] = 'N'
                night_count[e] += 1
            available = [e for e in available if e not in night_assigned]

            # Assign Morning
            n_morning = min(max_morning, len(available))
            for e in available[:n_morning]:
                plan.loc[e,date] = 'F'
            available = [e for e in available if plan.loc[e,date]=='']

            # Assign Second
            for e in available:
                plan.loc[e,date] = 'S'

        st.session_state['final_plan'] = plan
        st.success("Shift plan generated!")

# TAB 2
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

# TAB 3
with tab3:
    st.header("Final Shift Plan and Summary")
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
            'L':[sum(1 for v in df_plan.loc[e] if v=='L') for e in df_plan.index]
        }, index=df_plan.index)
        st.subheader("Per-person shift counts this month")
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
        st.download_button("Download CSV", csv, file_name=f"final_shift_plan_{year}_{month:02d}.csv")
