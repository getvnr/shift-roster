import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

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

# Helpers
def get_weekends(year, month):
    return [d for d in range(1, monthrange(year, month)[1]+1) if weekday(year, month, d) in [5,6]]

# TAB 1: Generate Roster
with tab1:
    st.header("Step 1 — Configure month & generate 24/7 roster")
    year = st.number_input("Year", 2023, 2100, 2025)
    month = st.selectbox("Month", range(1,13), index=9, format_func=lambda x: pd.Timestamp(year,x,1).strftime("%B"))
    num_days = monthrange(year, month)[1]
    dates = [pd.Timestamp(year, month, d).strftime("%d-%b-%Y") for d in range(1, num_days+1)]

    festival_days = st.multiselect("Festival days (1..n)", list(range(1, num_days+1)))
    max_night_per_person = st.number_input("Max Night (N) per month", 0, num_days, 5)
    min_morning = st.number_input("Min Morning (F) per day", 2, 3, 2)
    max_morning = st.number_input("Max Morning (F) per day", 2, 3, 3)
    min_second = st.number_input("Min Second (S) per day", 3, 4, 3)
    max_second = st.number_input("Max Second (S) per day", 3, 4, 4)

    if st.button("Generate 24/7 Roster"):
        plan = pd.DataFrame('', index=employees, columns=dates)
        night_count = {emp:0 for emp in employees}

        # Weekends
        weekends = get_weekends(year, month)

        # Assign shifts in rotation for each employee until weekly off
        shift_cycle = ['F','S','N']
        rng = np.random.default_rng(seed=(year*100+month))
        for emp in employees:
            day_idx = 0
            shift_idx = rng.integers(0,3)  # random starting shift
            while day_idx < num_days:
                # Determine consecutive working days (4-5)
                consec_days = rng.integers(4,6)
                for _ in range(consec_days):
                    if day_idx >= num_days:
                        break
                    date = dates[day_idx]
                    if day_idx+1 in weekends:
                        plan.loc[emp, date] = 'O'  # weekly off
                    elif day_idx+1 in festival_days:
                        plan.loc[emp, date] = 'H'
                    else:
                        # Assign shift
                        shift = shift_cycle[shift_idx]
                        if shift=='N' and night_count[emp]>=max_night_per_person:
                            # switch to F or S if night limit reached
                            shift = 'F' if rng.integers(0,2)==0 else 'S'
                        plan.loc[emp, date] = shift
                        if shift=='N':
                            night_count[emp]+=1
                    day_idx +=1
                # Add 2-day off after consecutive working days
                for off_day in range(2):
                    if day_idx>=num_days:
                        break
                    date = dates[day_idx]
                    plan.loc[emp, date] = 'O'
                    day_idx +=1
                # Rotate shift after off
                shift_idx = (shift_idx+1)%3

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
        st.download_button("Download CSV", csv, file_name=f"24_7_roster_{year}_{month:02d}.csv")
