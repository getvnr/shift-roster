import streamlit as st
import pandas as pd
import numpy as np

st.title("12-Person Shift Roster")

# Example DataFrame
employees = ["Alice", "Bob", "Charlie"]
roster = pd.DataFrame(index=employees, columns=[f"Day {i}" for i in range(1, 31)])
st.dataframe(roster)
