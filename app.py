import streamlit as st
import pandas as pd
import numpy as np
import random
from calendar import monthrange, weekday

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("Shift & Leave Plan Generator (Equalized Off Days + Group Logic)")

# --- Default Employee and Group Setup ---
employee_groups = pd.DataFrame([
    ["Gopalakrishnan Selvaraj", "Group1", "Opposite"],
    ["Paneerselvam F", "Group1", "Opposite"],
    ["Rajesh Jayapalan", "Group1", "Opposite"],
    ["Ajay Chidipotu", "Group2", "Opposite"],
    ["Imran Khan", "Group2", "Opposite"],
    ["Sammeta Balachander", "Group2", "Opposite"],
    ["Ramesh Polisetty", "Group3", "Always G Shift"],
    ["Srinivasu Cheedalla", "Group3", "Always G Shift"],
    ["Gangavarapu Suneetha", "Group3", "Always G Shift"],
    ["Lakshmi Narayana Rao", "Group3", "Always G Shift"],
    ["Muppa Divya", "Group4", "Always S Shift"],
    ["Anil Athkuri", "Group4", "Always S Shift"],
    ["D Namithananda", "Group4", "Always S Shift"],
    ["Pousali C", "Group5", "Opposite"],
    ["B Madhurusha", "Group5", "Opposite"],
    ["Edagotti Kalpana", "Group5", "Opposite"],
    ["Thorat Yashwant", "Group6", "Opposite"],
    ["Srivastav Nitin", "Group6", "Opposite"],
    ["Kishore Khati Vaibhav", "Group6", "Opposite"],
    ["Rupan Venkatesan Anandha", "Group7", "Opposite"],
    ["Chaudhari Kaustubh", "Group7", "Opposite"],
    ["Shejal Gawade", "Group7", "Opposite"],
    ["Vivek Kushwaha", "Group8", "Opposite"],
    ["Abdul Mukthiyar Basha", "Group8", "Opposite"],
    ["M Naveen", "Group8", "Opposite"],
    ["Chinthalapudi Yaswanth", "Group8", "Opposite"]
], columns=["Name", "Group", "Type"])

employees = employee_groups["Name"].tolist()

# --- Sidebar: Input Settings ---
st.sidebar.header("Month & Year")
year = st.sidebar.number_input("Year", min_value=2023, max_value=2100, value=2025)
month = st.sidebar.selectbox(
    "Month", list(range(1, 13)), index=9, format_func=lambda x: pd.Timestamp(year, x, 1).strftime('%B')
)
num_days = monthrange(year, month)[1]
dates = [f"{day:02d}-{month:02d}-{year}" for day in range(1, num_days + 1)]

# --- Festival Days ---
festival_days = st.sidebar.multiselect("Festival Days", list(range(1, num_days + 1)), default=[])

# --- Target Off Days ---
target_offs = st.sidebar.slider("Target Off Days per Employee", 6, 12, 8)

# --- Helper Function to Generate Shifts by Group Logic ---
def generate_roster_with_groups(group_df, num_days=30, target_offs=8):
    shifts = ['F', 'S', 'N']
    roster = {emp: [''] * num_days for emp in group_df["Name"]}

    grouped = group_df.groupby(["Group", "Type"])
    for (group, gtype), df in grouped:
        employees = df["Name"].tolist()

        # Fixed Shift Groups (Always G / Always S)
        if "Always G" in gtype or "Always S" in gtype:
            fixed_shift = "G" if "G" in gtype else "S"
            for emp in employees:
                day = 0
                while day < num_days:
                    work_days = random.randint(5, 10)
                    for _ in range(work_days):
                        if day >= num_days: break
                        roster[emp][day] = fixed_shift
                        day += 1
                    for _ in range(2):
                        if day >= num_days: break
                        roster[emp][day] = 'O'
                        day += 1

        # Opposite Shifts (rotate F, S, N but not same shift for group)
        elif "Opposite" in gtype:
            for emp in employees:
                shift_cycle = random.sample(shifts, len(shifts))
                day = 0
                while day < num_days:
                    shift = random.choice(shift_cycle)
                    block_len = random.randint(5, 10)
                    for _ in range(block_len):
                        if day >= num_days: break
                        roster[emp][day] = shift
                        day += 1
                    for _ in range(2):
                        if day >= num_days: break
                        roster[emp][day] = 'O'
                        day += 1

    # Equalize offs
    for emp, days in roster.items():
        off_count = sum(1 for d in days if d == 'O')
        diff = off_count - target_offs
        if diff > 0:  # Too many offs → convert extras to shifts
            off_indices = [i for i, v in enumerate(days) if v == 'O']
            for idx in off_indices[:diff]:
                days[idx] = random.choice(['F', 'S', 'N'])
        elif diff < 0:  # Too few offs → assign more offs randomly
            work_indices = [i for i, v in enumerate(days) if v not in ['O', 'H']]
            add = np.random.choice(work_indices, abs(diff), replace=False)
            for idx in add:
                days[idx] = 'O'

    # Add Holidays
    for emp in roster:
        for fday in festival_days:
            if 1 <= fday <= num_days:
                roster[emp][fday - 1] = 'H'

    return pd.DataFrame(roster, index=[f"Day {i+1}" for i in range(num_days)]).T


# --- Generate & Display ---
if st.button("Generate Roster"):
    df_roster = generate_roster_with_groups(employee_groups, num_days, target_offs)

    # Color coding
    def color_code(val):
        colors = {'F': '#8FD694', 'S': '#F7DC6F', 'N': '#85C1E9', 'O': '#D7DBDD', 'H': '#E59866', 'G': '#D2B4DE'}
        return f'background-color: {colors.get(val, "")}'

    st.subheader("📅 Shift & Leave Plan")
    st.dataframe(df_roster.style.applymap(color_code), height=700, use_container_width=True)

    # Summary
    st.subheader("📊 Summary")
    summary = pd.DataFrame({
        "Off Days (O)": [sum(1 for v in df_roster.loc[e] if v == 'O') for e in df_roster.index],
        "Holidays (H)": [sum(1 for v in df_roster.loc[e] if v == 'H') for e in df_roster.index],
        "F": [sum(1 for v in df_roster.loc[e] if v == 'F') for e in df_roster.index],
        "S": [sum(1 for v in df_roster.loc[e] if v == 'S') for e in df_roster.index],
        "N": [sum(1 for v in df_roster.loc[e] if v == 'N') for e in df_roster.index],
        "G": [sum(1 for v in df_roster.loc[e] if v == 'G') for e in df_roster.index],
    })
    st.dataframe(summary)

    # Download option
    csv = df_roster.to_csv().encode('utf-8')
    st.download_button("⬇️ Download Roster CSV", csv, f"shift_roster_{year}_{month:02d}.csv")

else:
    st.info("Click **Generate Roster** to create the schedule.")
