import streamlit as st
import os

# Page config MUST be the first Streamlit command
st.set_page_config(page_title="KnowThee Talent Intelligence", page_icon="��", layout="wide")

from individual_profile_tab import render_individual_profile
from talent_explorer_tab import render_talent_explorer
from analytics_dashboard_tab import render_analytics_dashboard
from team_builder_tab import render_team_builder

# Custom CSS and banner
try:
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(script_dir, "styles.css")
    
    with open(css_path, "r") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError as e:
    st.warning(f"⚠️ styles.css not found at {css_path}. UI may not render as intended. Error: {e}")

st.markdown(
    '<div class="top-banner"><div class="banner-content"><div class="banner-text">KnowThee Talent Intelligence</div></div></div>',
    unsafe_allow_html=True
)
st.markdown('<div class="top-spacer"></div>', unsafe_allow_html=True)

# Define tab names and associated rendering functions
tab_names = [
    "👤 Individual Profile",
    "🔍 Talent Explorer",
    "📊 Analytics Dashboard",
    "👥 Team Builder"
]

tab_functions = [
    render_individual_profile,
    render_talent_explorer,
    render_analytics_dashboard,
    render_team_builder
]

# Render each tab
tabs = st.tabs(tab_names)

for tab, func in zip(tabs, tab_functions):
    with tab:
        func()
