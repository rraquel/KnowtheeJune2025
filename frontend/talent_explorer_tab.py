import streamlit as st
import pandas as pd
import requests
from config import BACKEND_URL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_talent_explorer():
    st.title("Talent Explorer")

    # Employee Table with error handling
    try:
        response = requests.get(f"{BACKEND_URL}/employees", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df)
                st.success(f"✅ Loaded {len(data)} employees")
            else:
                st.warning("⚠️ No employees found in the database")
        else:
            st.error(f"❌ Failed to fetch data from backend: {response.status_code}")
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection error. Please check if the backend is running.")
    except Exception as e:
        st.error(f"❌ Error connecting to backend: {e}")

    # Chat Feature with improved error handling
    if "session_id" not in st.session_state:
        st.session_state.session_id = "session_001"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("Chat with Talent Explorer")
    
    # Add Clear Chat button
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.session_state["talent_chat_input"] = ""
        st.success("💬 Chat history cleared!")

    # Add health check button
    if st.button("Check System Health", key="health_check"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                st.success("✅ System is healthy!")
                st.json(health_data)
            else:
                st.error(f"❌ System health check failed: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Health check error: {e}")

    user_input = st.text_input("Ask a question:", key="talent_chat_input")
    
    if st.button("Send", key="talent_chat_send") and user_input:
        # Show loading spinner
        with st.spinner("🤔 Processing your question..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message": user_input
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    rag_result = response.json()
                    
                    # Add user message to chat history
                    st.session_state.chat_history.append(("You", user_input))
                    
                    # Handle clarification responses with improved presentation
                    if rag_result.get("clarification_needed"):
                        answer = rag_result.get("response", "Sorry, I couldn't generate a response.")
                        candidates = rag_result.get("candidates", [])
                        
                        # Show clarification warning with better styling
                        st.warning("🔍 **Clarification Needed**")
                        st.markdown(answer)
                        
                        # Show candidates list with improved formatting
                        if candidates:
                            st.markdown("**Available candidates:**")
                            
                            # Create a more structured display
                            for i, cand in enumerate(candidates, 1):
                                with st.container():
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.markdown(f"**{i}. {cand.get('name', 'Unknown')}**")
                                        st.markdown(f"*{cand.get('department', 'Unknown department')}*")
                                        if cand.get('position'):
                                            st.markdown(f"Position: {cand.get('position')}")
                                    with col2:
                                        if cand.get('email'):
                                            st.markdown(f"📧 {cand.get('email')}")
                                    
                                    st.divider()
                        
                        # Add clarification message to chat history
                        st.session_state.chat_history.append(("AI", answer))
                        
                    else:
                        # Normal response - show as success and add to chat history
                        answer = rag_result.get("response", "Sorry, I couldn't generate a response.")
                        
                        # Check if it's an error response
                        if "error" in rag_result.get("source", "").lower() or "could not" in answer.lower():
                            st.error("❌ **Response**")
                        else:
                            st.success("✅ **Response**")
                        
                        st.markdown(answer)
                        st.session_state.chat_history.append(("AI", answer))
                        
                elif response.status_code == 400:
                    st.error("❌ **Invalid Request**")
                    st.markdown("Please check your input and try again.")
                elif response.status_code == 500:
                    st.error("❌ **Server Error**")
                    st.markdown("The server encountered an error. Please try again later.")
                else:
                    st.error(f"❌ **Unexpected Error** (Status: {response.status_code})")
                    st.markdown("An unexpected error occurred. Please try again.")
                    
            except requests.exceptions.Timeout:
                st.error("⏰ **Request Timeout**")
                st.markdown("The request took too long to process. Please try a simpler question or try again later.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 **Connection Error**")
                st.markdown("Could not connect to the backend server. Please check if the server is running.")
            except Exception as e:
                st.error(f"❌ **Unexpected Error**")
                st.markdown(f"An error occurred: {str(e)}")
                logger.error(f"Error in chat endpoint: {e}")

    # Display chat history with improved formatting
    if st.session_state.chat_history:
        st.subheader("💬 Chat History")
        
        for sender, msg in st.session_state.chat_history:
            if sender == "You":
                st.markdown(f"**👤 {sender}:**")
                st.markdown(f"_{msg}_")
            else:
                st.markdown(f"**🤖 {sender}:**")
                st.markdown(msg)
            st.divider()