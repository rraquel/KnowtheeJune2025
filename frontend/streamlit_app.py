import streamlit as st
import requests
from talent_explorer_tab import show_talent_explorer

# Page configuration
st.set_page_config(page_title="KnowThee Frontend", layout="wide")

# Tabs
tabs = st.tabs(["Overview", "Talent Explorer", "Other Tabs..."])

with tabs[1]:  # Talent Explorer tab
    st.header("🧠 Talent Explorer")
    
    # Session ID for conversation tracking
    if "session_id" not in st.session_state:
        st.session_state.session_id = "session_001"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask the Talent Explorer a question:")
    if st.button("Send") and user_input:
        try:
            response = requests.post(
                "http://localhost:8000/api/talent/chat",
                json={
                    "session_id": st.session_state.session_id,
                    "message": user_input
                }
            )
            if response.status_code == 200:
                answer = response.json()["response"]
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("AI", answer))
            else:
                st.error("Failed to get a response from the backend.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

    # Display chat history
    for sender, msg in st.session_state.chat_history:
        st.markdown(f"**{sender}:** {msg}")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Talent Explorer",
    "Team Builder",
    "Individual Profile",
    "Analytics Dashboard"
])

# Route based on selected page
if page == "Talent Explorer":
    show_talent_explorer()
elif page == "Team Builder":
    st.write("🚧 Team Builder tab is under construction.")
elif page == "Individual Profile":
    st.write("🚧 Individual Profile tab is under construction.")
elif page == "Analytics Dashboard":
    st.write("🚧 Analytics Dashboard tab is under construction.")
