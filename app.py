import streamlit as st
import pandas as pd
import numpy as np
from calendar import monthrange, weekday

# -------------------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------------------
st.set_page_config(page_title="24/7 Shift Roster Generator", layout="wide")
st.title("🕒 Automated 24/7 Shift Roster Generator")

# -------------------------------------------------------------
# Step 1: Upload Employee Data
# -------------------------------------------------------------
st.subheader("📋 Upload or Use Default Employee Preference Data")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel with columns: Name, Level, Night, Weekend, Morning, Second, General",
    type=["csv", "xlsx"]
)

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
else:
    # Default data
    data = {
        "Name": [
            "Ramesh Polisetty","Ajay Chidipotu","Srinivasu Cheedalla","Imran Khan",
            "Sammeta Balachander","Muppa Divya","Anil Athkuri","Gangavarapu Suneetha",
            "Gopalakrishnan Selvaraj","Paneerselvam F","Rajesh Jayapalan",
            "Lakshmi Narayana Rao","Pousali C","D Namithananda","Thorat Yashwant",
            "Srivastav Nitin","Kishore Khati Vaibhav","Rupan Venkatesan Anandha",
            "Chaudhari Kaustubh","Shejal Gawade","Vivek Kushwaha","Abdul Mukthiyar Basha",
            "M Naveen","B Madhurusha","Chinthalapudi Yaswanth","Edagotti Kalpana"
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

# -------------------------------------------------------------
# Step 2: Month and Year Selection
# -------------------------------------------------------------
st.subheader("📅 Select Roster Month and Parameters")

year = st.number_input("Year", min_value=2024, max_value=2100, value=2025)
month = st.selectbox("Month", range(1, 13), index=9, format_func=lambda x: pd.Timestamp(year, x, 1).strftime("%B"))
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days + 1)]

working_days = st.number_input("Working days per employee", min_value=1, max_value=num_days, value=21)
festival_days = st.multiselect("Festival Holidays (Optional)", options=list(range(1, num_days + 1)), default=[])

# -------------------------------------------------------------
# Step 3: Week-off Setup
# -------------------------------------------------------------
st.subheader("🗓️ Week-Off Setup")

fri_sat_off = st.multiselect("Friday-Saturday Off", employees, default=["Gangavarapu Suneetha","Lakshmi Narayana Rao"])
sun_mon_off = st.multiselect("Sunday-Monday Off", employees, default=["Ajay Chidipotu","Imran Khan"])
sat_sun_off = st.multiselect("Saturday-Sunday Off", employees, default=["Muppa Divya","Anil Athkuri"])

def get_days(year, month, weekdays):
    return [day for day in range(1, monthrange(year, month)[1] + 1) if weekday(year, month, day) in weekdays]

frisat_days = get_days(year, month, [4,5])
sunmon_days = get_days(year, month, [6,0])
satsun_days = get_days(year, month, [5,6])

# -------------------------------------------------------------
# Step 4: Roster Logic
# -------------------------------------------------------------
def assign_shifts(df, num_days):
    np.random.seed(42)
    roster = {emp: [""] * num_days for emp in df["Name"]}

    for day in range(num_days):
        day_num = day + 1
        if day_num in festival_days:
            for emp in df["Name"]:
                roster[emp][day] = "H"
            continue

        # Shift demand
        req_morning, req_second, req_night = 3, 3, 2

        # Night shift
        night_eligible = df[df["Night"].str.lower() == "yes"]["Name"].tolist()
        np.random.shuffle(night_eligible)
        for emp in night_eligible[:req_night]:
            roster[emp][day] = "N"

        # Morning shift
        morning_eligible = [e for e in df["Name"] if roster[e][day] == "" and df.loc[df["Name"]==e, "Morning"].values[0] != "No"]
        np.random.shuffle(morning_eligible)
        for emp in morning_eligible[:req_morning]:
            roster[emp][day] = "F"

        # Second shift
        second_eligible = [e for e in df["Name"] if roster[e][day] == "" and df.loc[df["Name"]==e, "Second"].values[0] != "No"]
        np.random.shuffle(second_eligible)
        for emp in second_eligible[:req_second]:
            roster[emp][day] = "S"

        # Remaining: General or Off
        for emp in df["Name"]:
            if roster[emp][day] == "":
                general_ok = df.loc[df["Name"]==emp, "General"].values[0]
                roster[emp][day] = "G1" if general_ok == "Yes" else "O"

        # Week-off application
        if emp in fri_sat_off and day_num in frisat_days:
            roster[emp][day] = "O"
        elif emp in sun_mon_off and day_num in sunmon_days:
            roster[emp][day] = "O"
        elif emp in sat_sun_off and day_num in satsun_days:
            roster[emp][day] = "O"

    return roster

# -------------------------------------------------------------
# Step 5: Generate and Display
# -------------------------------------------------------------
if st.button("Generate Roster"):
    roster_data = assign_shifts(df, num_days)
    roster_df = pd.DataFrame(roster_data, index=dates).T

    def color(v):
        c = {"F":"lightgreen","S":"khaki","N":"lightblue","G1":"palegreen","O":"lightgray","H":"orange"}
        return f"background-color:{c.get(v,'')}"
    
    st.subheader("📅 Generated Monthly Roster")
    st.dataframe(roster_df.style.applymap(color), height=600)

    # Summary
    summary = pd.DataFrame({
        s: [sum(1 for x in roster_data[e] if x == s) for e in df["Name"]]
        for s in ["F", "S", "N", "G1", "O", "H"]
    }, index=df["Name"])
    
    st.subheader("📊 Shift Summary")
    st.dataframe(summary)

    csv = roster_df.to_csv().encode()
    st.download_button("📥 Download Roster CSV", csv, f"roster_{year}_{month:02d}.csv", "text/csv")
