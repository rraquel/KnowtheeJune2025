import streamlit as st
from talent_explorer_tab import render_talent_explorer

# Page configuration
st.set_page_config(
    page_title="KnowThee Talent Intelligence",
    page_icon="��",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">KnowThee Talent Intelligence</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced AI-powered talent analysis and insights</p>', unsafe_allow_html=True)

# Horizontal tabs navigation
tabs = st.tabs(["Talent Explorer", "Team Builder", "Individual Profile", "Analytics Dashboard"])

with tabs[0]:  # Talent Explorer tab
    render_talent_explorer()

with tabs[1]:  # Team Builder tab
    st.header("Team Builder")
    st.info("This feature is under development. Coming soon!")
    st.markdown("""
    **Planned Features:**
    - Build optimal teams based on personality compatibility
    - Analyze team dynamics and potential conflicts
    - Recommend team compositions for specific projects
    - Team performance prediction and optimization
    """)

with tabs[2]:  # Individual Profile tab
    st.header("Individual Profile")
    st.info("This feature is under development. Coming soon!")
    st.markdown("""
    **Planned Features:**
    - Detailed individual employee profiles
    - Career development recommendations
    - Performance analysis and trends
    - Personalized development plans
    """)

with tabs[3]:  # Analytics Dashboard tab
    st.header("Analytics Dashboard")
    st.info("This feature is under development. Coming soon!")
    st.markdown("""
    **Planned Features:**
    - Organization-wide talent analytics
    - Assessment score distributions
    - Diversity and inclusion metrics
    - Predictive analytics for talent management
    """)
