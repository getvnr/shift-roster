import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from git import Repo

st.title("Automatic Employee Roster")

# ---------------------------
# Step 1: Employee Data (embedded)
# ---------------------------
data = [
    ["Ramesh Polisetty","","L2","S","Yes",0],
    ["Ajay Chidipotu","Websphere","L2","F,S,N","Yes",10],
    ["Srinivasu Cheedalla","","L2","E","Yes",0],
    ["Imran Khan","Websphere","L2","F,S","Yes",0],
    ["Sammeta Balachander","Websphere","L2","F,S,N","Yes",10],
    ["Muppa Divya","","L2","S","Yes",0],
    ["Anil Athkuri","","L2","S","Yes",0],
    ["Gangavarapu Suneetha","","L2","G","Yes",0],
    ["Gopalakrishnan Selvaraj","IIS","L2","F,S,N","Yes",10],
    ["Paneerselvam","IIS","L2","F,S,N","Yes",10],
    ["Rajesh Jayapalan","IIS","L2","F,S,N","Yes",10],
    ["Lakshmi Narayana Rao","","L2","G","Yes",0],
    ["Pousali C","","L1","F,S,N","Yes",10],
    ["D Namithananda","","L2","S","No",0],
    ["Thorat Yashwant","","L1","F,S,N","Yes",10],
    ["Srivastav Nitin","","L1","F,S,N","No",10],
    ["Kishore Khati Vaibhav","","L1","F,S,N","No",10],
    ["Rupan Venkatesan Anandha","","L1","F,S,N","No",10],
    ["Chaudhari Kaustubh","","L1","F,S,N","No",10],
    ["Shejal Gawade","","L1","F,S,N","No",10],
    ["Vivek Kushwaha","","L1","F,S,N","No",10],
    ["Abdul Mukthiyar Basha","","L1","F,S,N","No",10],
    ["M Naveen","","L1","F,S,N","No",10],
    ["B Madhurusha","","L1","F,S,N","No",10],
    ["Chinthalapudi Yaswanth","","L1","F,S,N","No",10],
    ["Edagotti Kalpana","","L1","F,S,N","No",10]
]

columns = ["Name","AlwaysOppositeShifts","Skill","ShiftsAllowed","WeekendOff","MaxNightShifts"]
employees = pd.DataFrame(data, columns=columns)

# ---------------------------
# Step 2: Initialize roster
# ---------------------------
days = 30  # Number of days to schedule
shifts = ['F', 'S', 'N', 'E']  # Possible shifts
roster = pd.DataFrame('', index=employees['Name'], columns=[f'Day{i+1}' for i in range(days)])

# Track night shifts per employee
night_count = {name:0 for name in employees['Name']}

# ---------------------------
# Step 3: Helper functions
# ---------------------------
def is_weekend(day):
    """Return True if the day index corresponds to Saturday(5) or Sunday(6)"""
    weekday = day % 7
    return weekday in [5,6]

def allowed_shift(emp, day):
    """Return list of allowed shifts for employee on a day considering night limit & weekend off"""
    shifts_allowed = list(str(emp['ShiftsAllowed']).split(','))
    
    # Weekend off
    if str(emp['WeekendOff']).strip().lower() == 'yes' and is_weekend(day):
        return ['O']
    
    # Night shift limit
    if 'N' in shifts_allowed and night_count[emp['Name']] >= int(emp['MaxNightShifts']):
        shifts_allowed.remove('N')
    
    if not shifts_allowed:
        return ['O']  # No shifts possible
    return shifts_allowed

# ---------------------------
# Step 4: Generate roster
# ---------------------------
for day in range(days):
    for idx, emp in employees.iterrows():
        shifts_today = allowed_shift(emp, day)
        # Randomly assign one of allowed shifts
        assigned_shift = np.random.choice(shifts_today)
        roster.iloc[idx, day] = assigned_shift
        if assigned_shift == 'N':
            night_count[emp['Name']] += 1

# ---------------------------
# Step 5: Display roster
# ---------------------------
st.subheader("Generated Roster")
st.dataframe(roster)

# ---------------------------
# Step 6: Save roster locally
# ---------------------------
if st.button("Save Roster Locally"):
    filename = f"Roster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    roster.to_csv(filename)
    st.success(f"Roster saved as {filename}")

# ---------------------------
# Step 7: Push roster to GitHub
# ---------------------------
if st.button("Push Roster to GitHub"):
    try:
        repo = Repo(".")  # Streamlit app must be inside a git repo
        roster.to_csv("roster.csv", index=True)
        repo.git.add("roster.csv")
        repo.git.commit("-m", f"Update roster {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        repo.git.push()
        st.success("Roster pushed to GitHub successfully!")
    except Exception as e:
        st.error(f"Git push failed: {e}")
