import streamlit as st
from talent_explorer_tab import show_talent_explorer

# Page configuration
st.set_page_config(page_title="KnowThee Frontend", layout="wide")

# Horizontal tabs navigation
tabs = st.tabs(["Talent Explorer", "Team Builder", "Individual Profile", "Analytics Dashboard"])

with tabs[0]:  # Talent Explorer tab
    show_talent_explorer()

with tabs[1]:  # Team Builder tab
    st.write("Team Builder tab is under construction.")

with tabs[2]:  # Individual Profile tab
    st.write("Individual Profile tab is under construction.")

with tabs[3]:  # Analytics Dashboard tab
    st.write("Analytics Dashboard tab is under construction.")
