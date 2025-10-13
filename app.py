import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Shift Roster Generator", layout="wide")

# --- Function: Generate Roster ---
def generate_roster_by_custom_groups(group_mapping, num_days=30):
    roster = {}
    shifts = ['F', 'S', 'N']
    
    for group, info in group_mapping.items():
        gtype = info["Type"]
        employees = info["Employees"]

        if gtype.lower().startswith("always"):
            fixed_shift = 'G' if 'G' in gtype else 'S'
            for emp in employees:
                emp_schedule = []
                day = 0
                while day < num_days:
                    work_days = random.randint(5, 10)
                    for _ in range(work_days):
                        if day >= num_days:
                            break
                        emp_schedule.append(fixed_shift)
                        day += 1
                    for _ in range(2):
                        if day >= num_days:
                            break
                        emp_schedule.append('O')
                        day += 1
                emp_schedule = emp_schedule[:num_days]
                roster[emp] = emp_schedule

        elif gtype.lower() == "opposite":
            emp_count = len(employees)
            for emp in employees:
                roster[emp] = [''] * num_days
            for day in range(num_days):
                day_shifts = random.sample(shifts, min(emp_count, len(shifts)))
                for i, emp in enumerate(employees[:len(day_shifts)]):
                    roster[emp][day] = day_shifts[i]
            for emp in employees:
                final = []
                day = 0
                while day < num_days:
                    shift = roster[emp][day] if roster[emp][day] else random.choice(shifts)
                    block_len = random.randint(5, 10)
                    for _ in range(block_len):
                        if day >= num_days:
                            break
                        final.append(shift)
                        day += 1
                    for _ in range(2):
                        if day >= num_days:
                            break
                        final.append('O')
                        day += 1
                roster[emp] = final[:num_days]

    return roster


# --- Page Title ---
st.title("📅 Middleware Team Shift Roster Generator")

# --- Sidebar Inputs ---
st.sidebar.header("Settings")
num_days = st.sidebar.slider("Number of days", 7, 31, 30)

# --- Group Mapping (you can later move this to a config file) ---
group_mapping = {
    "Group1": {"Type": "Opposite", "Employees": ["Gopalakrishnan Selvaraj", "Paneerselvam F", "Rajesh Jayapalan"]},
    "Group2": {"Type": "Opposite", "Employees": ["Ajay Chidipotu", "Imran Khan", "Sammeta Balachander"]},
    "Group3": {"Type": "Always G Shift", "Employees": ["Ramesh Polisetty", "Srinivasu Cheedalla", "Gangavarapu Suneetha", "Lakshmi Narayana Rao"]},
    "Group4": {"Type": "Always S Shift", "Employees": ["Muppa Divya", "Anil Athkuri", "D Namithananda"]},
    "Group5": {"Type": "Opposite", "Employees": ["Pousali C", "B Madhurusha", "Edagotti Kalpana"]},
    "Group6": {"Type": "Opposite", "Employees": ["Thorat Yashwant", "Srivastav Nitin", "Kishore Khati Vaibhav"]},
    "Group7": {"Type": "Opposite", "Employees": ["Rupan Venkatesan Anandha", "Chaudhari Kaustubh", "Shejal Gawade"]},
    "Group8": {"Type": "Opposite", "Employees": ["Vivek Kushwaha", "Abdul Mukthiyar Basha", "M Naveen", "Chinthalapudi Yaswanth"]}
}

# --- Generate Button ---
if st.button("Generate Roster"):
    roster = generate_roster_by_custom_groups(group_mapping, num_days=num_days)
    df = pd.DataFrame(roster).T
    df.columns = [f"Day {i+1}" for i in range(num_days)]
    
    st.success("✅ Roster generated successfully!")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv().encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "roster.csv", "text/csv")
else:
    st.info("Click the **Generate Roster** button to create the schedule.")
