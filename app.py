import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday
import math

st.set_page_config(layout="wide")
st.title("Automated 24/7 Shift Roster Generator (Skill- & Preference-Based)")

# --- Load Employee Data ---
st.subheader("Upload or Paste Employee Shift Preferences")

uploaded_file = st.file_uploader("Upload Excel/CSV with columns: Name, Level, Night, Weekend, Morning, Second, General", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
else:
    # fallback default dataset
    data = {
        "Name": [
            "Ramesh Polisetty","Ajay Chidipotu","Srinivasu Cheedalla","Imran Khan","Sammeta Balachander","Muppa Divya",
            "Anil Athkuri","Gangavarapu Suneetha","Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan",
            "Lakshmi Narayana Rao","Pousali C","D Namithananda","Thorat Yashwant","Srivastav Nitin",
            "Kishore Khati Vaibhav","Rupan Venkatesan Anandha","Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha",
            "Abdul Mukthiyar Basha","M Naveen","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana"
        ],
        "Level":["L2","L2","L2","L2","L2","L2","L2","L2","L2","L2","L2","L2",
                  "L1","L2","L1","L1","L1","L1","L1","L1","L1","L1","L1","L1","L1","L1"],
        "Night":["No","Yes","No","No","Yes","No","No","No","Yes","Yes","Yes","No",
                 "Yes","No","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes"],
        "Weekend":["No","No","No","No","No","No","No","No","No","No","No","No",
                    "Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes"],
        "Morning":["No","Yes","No","No","Yes","No","No","No","Yes","Yes","Yes","No",
                   "5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10"],
        "Second":["Yes","Yes","No","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes",
                  "5 to 10","Yes","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10","5 to 10"],
        "General":["Yes","No","Yes","No","No","No","No","Yes","No","No","No","Yes",
                   "No","No","No","No","No","No","No","No","No","No","No","No","No","No"]
    }
    df = pd.DataFrame(data)

st.dataframe(df)

employees = df["Name"].tolist()

# --- Nightshift Exemption automatically inferred ---
nightshift_exempt = df.loc[df["Night"].str.lower() == "no", "Name"].tolist()

# --- Week-off pattern ---
st.subheader("Week-off Preferences")
friday_saturday_off = st.multiselect("Friday-Saturday off", employees, default=["Gangavarapu Suneetha","Lakshmi Narayana Rao"])
sunday_monday_off = st.multiselect("Sunday-Monday off", employees, default=["Ajay Chidipotu","Imran Khan"])
saturday_sunday_off = st.multiselect("Saturday-Sunday off", employees, default=["Muppa Divya","Anil Athkuri"])

# --- Year & Month ---
year = st.number_input("Select Year", min_value=2023, max_value=2100, value=2025)
month = st.selectbox("Select Month", list(range(1,13)), index=9, format_func=lambda x: pd.Timestamp(year, x, 1).strftime("%B"))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days+1)]

# --- Parameters ---
working_days_per_emp = st.number_input("Working days per employee", min_value=1, max_value=num_days, value=21)
festival_days = st.multiselect("Festival Days (optional)", options=list(range(1,num_days+1)), default=[])

# --- Helper to get weekday numbers ---
def get_days(year, month, weekdays):
    return [day for day in range(1, monthrange(year, month)[1]+1) if weekday(year, month, day) in weekdays]

fridays_saturdays = get_days(year, month, [4,5])
sundays_mondays = get_days(year, month, [6,0])
saturdays_sundays = get_days(year, month, [5,6])

# --- Shift Assignment Algorithm ---
def assign_shifts(df, num_days):
    np.random.seed(42)
    roster = {emp: ['']*num_days for emp in df["Name"]}
    counts = {emp: {"F":0,"S":0,"N":0,"G1":0,"O":0} for emp in df["Name"]}

    for day in range(num_days):
        is_festival = (day+1) in festival_days
        if is_festival:
            for emp in df["Name"]:
                roster[emp][day] = "H"
            continue

        # required coverage
        req_morning, req_second, req_night = 3, 3, 2

        available = df.copy()

        # assign Night shifts
        night_candidates = available[available["Night"].str.lower() == "yes"]["Name"].tolist()
        np.random.shuffle(night_candidates)
        for emp in night_candidates[:req_night]:
            roster[emp][day] = "N"; counts[emp]["N"]+=1

        # assign Morning (F/G1)
        morning_candidates = [e for e in available["Name"] if roster[e][day]=="" and (df.loc[df["Name"]==e,"Morning"].values[0]!="No")]
        np.random.shuffle(morning_candidates)
        for emp in morning_candidates[:req_morning]:
            roster[emp][day] = "F"; counts[emp]["F"]+=1

        # assign Second shift
        second_candidates = [e for e in available["Name"] if roster[e][day]=="" and (df.loc[df["Name"]==e,"Second"].values[0]!="No")]
        np.random.shuffle(second_candidates)
        for emp in second_candidates[:req_second]:
            roster[emp][day] = "S"; counts[emp]["S"]+=1

        # others off/general
        for emp in df["Name"]:
            if roster[emp][day]=="":
                if df.loc[df["Name"]==emp,"General"].values[0]=="Yes":
                    roster[emp][day]="G1"; counts[emp]["G1"]+=1
                else:
                    roster[emp][day]="O"; counts[emp]["O"]+=1

    return roster

roster_dict = assign_shifts(df, num_days)

# --- Display ---
st.subheader("Generated Roster")
roster = pd.DataFrame(roster_dict, index=dates).T
def color(v):
    c={"F":"lightgreen","S":"khaki","N":"lightblue","O":"lightgray","H":"orange","G1":"palegreen"}
    return f"background-color:{c.get(v,'')}"
st.dataframe(roster.style.applymap(color), height=600)

# --- Summary ---
summary = pd.DataFrame({s:[sum(1 for x in roster_dict[e] if x==s) for e in employees] for s in ["F","S","N","G1","O","H"]}, index=employees)
st.subheader("Shift Summary")
st.dataframe(summary)

st.download_button("📥 Download Roster CSV", roster.to_csv().encode(), f"roster_{year}_{month:02d}.csv")
