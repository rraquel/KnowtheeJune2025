import streamlit as st
import pandas as pd
import requests

#BACKEND_URL = "http://localhost:8000"
BACKEND_URL = "http://localhost:8000/api/talent"

def show_talent_explorer():
    st.title("Talent Explorer")

    # Employee Table
    try:
        response = requests.get(f"{BACKEND_URL}/employees")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            st.dataframe(df)
        else:
            st.error("Failed to fetch data from backend.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

    # Chat Feature
    if "session_id" not in st.session_state:
        st.session_state.session_id = "session_001"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("Chat with Talent Explorer")
    
    # Add Clear Chat button
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.session_state["talent_chat_input"] = ""

    user_input = st.text_input("Ask a question:", key="talent_chat_input")
    if st.button("Send", key="talent_chat_send") and user_input:
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
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