import streamlit as st
import requests
import json
import time
import sys
import os
from typing import Dict, Any, Optional

# Add root directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BACKEND_URL

BACKEND_API_URL = BACKEND_URL

def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{BACKEND_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_chat_message(message: str, session_id: str) -> Dict[str, Any]:
    """Send a chat message to the API."""
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/chat",
            json={"message": message, "session_id": session_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "response": f"Error connecting to the API: {str(e)}",
            "session_id": session_id,
            "clarification_needed": False,
            "candidates": None,
            "analysis": None,
            "source": "error",
            "confidence": "low"
        }

def clear_cache():
    """Clear the API cache."""
    try:
        response = requests.post(f"{BACKEND_API_URL}/clear-cache", timeout=5)
        return response.status_code == 200
    except:
        return False

def format_reasoning_display(analysis: Dict[str, Any], source: str, confidence: str) -> str:
    """Format the reasoning information for display."""
    if not analysis:
        return "No reasoning information available."
    
    reasoning_parts = []
    
    # Intent explanation
    intent = analysis.get("intent", "unknown")
    intent_explanations = {
        "get_score": "Looking up a specific assessment score",
        "get_all_scores": "Retrieving all assessment scores",
        "compare_scores": "Comparing scores between employees",
        "rank_scores": "Ranking employees by assessment scores",
        "general_query": "Processing a general information request"
    }
    reasoning_parts.append(f"**Query Type:** {intent_explanations.get(intent, intent)}")
    
    # Assessment type
    if "assessment_type" in analysis:
        reasoning_parts.append(f"**Assessment:** {analysis['assessment_type']}")
    
    # Employees
    if "employees" in analysis and analysis["employees"]:
        emp_count = len(analysis["employees"])
        if emp_count == 1:
            reasoning_parts.append(f"**Employee:** {analysis['employees'][0]}")
        else:
            reasoning_parts.append(f"**Employees:** {', '.join(analysis['employees'])}")
    
    # Trait (if applicable)
    if "trait" in analysis:
        reasoning_parts.append(f"**Trait:** {analysis['trait']}")
    
    # Limit (for ranking queries)
    if "limit" in analysis:
        reasoning_parts.append(f"**Limit:** Top {analysis['limit']} results")
    
    # Source and confidence
    reasoning_parts.append(f"**Data Source:** {source}")
    reasoning_parts.append(f"**Confidence:** {confidence}")
    
    return "\n\n".join(reasoning_parts)

def render_talent_explorer():
    """Render the main talent explorer interface with enterprise-grade UX."""
    
    # Custom CSS for enterprise chat interface
    st.markdown("""
    <style>
    /* Main container styling */
    .chat-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Chat header */
    .chat-header {
        background: linear-gradient(135deg, #1f77b4 0%, #2c5aa0 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        font-size: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Chat messages area */
    .chat-messages {
        padding: 20px;
        background: #fafafa;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
    }
    
    /* Message styling */
    .message {
        margin-bottom: 16px;
        display: flex;
        align-items: flex-start;
    }
    
    .message.user {
        justify-content: flex-end;
    }
    
    .message.assistant {
        justify-content: flex-start;
    }
    
    .message-bubble {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.4;
        word-wrap: break-word;
    }
    
    .message.user .message-bubble {
        background: #1f77b4;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .message.assistant .message-bubble {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Input area */
    .chat-input-area {
        padding: 16px 20px;
        background: white;
        border-top: 1px solid #e0e0e0;
        border-radius: 0 0 8px 8px;
    }
    
    /* Control bar styling */
    .control-bar {
        background: #f8f9fa;
        padding: 12px 20px;
        border-radius: 6px;
        margin-bottom: 16px;
        border: 1px solid #e9ecef;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        font-size: 12px;
        color: #6c757d;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-online {
        background: #28a745;
    }
    
    .status-offline {
        background: #dc3545;
    }
    
    /* Example queries styling */
    .example-queries {
        background: #e3f2fd;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
        border-left: 4px solid #1f77b4;
    }
    
    .example-queries h4 {
        margin: 0 0 8px 0;
        color: #1f77b4;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Health check
    if not check_api_health():
        st.error("⚠️ API service is not available. Please ensure the backend server is running.")
        return
    
    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    if "auto_scroll" not in st.session_state:
        st.session_state.auto_scroll = True
    
    # Page header
    st.title("Talent Intelligence Explorer")
    st.markdown("Ask questions about employees, their assessment scores, and find the best candidates for your needs.")
    
    # Control bar
    with st.container():
        st.markdown('<div class="control-bar">', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button("Clear Chat", type="secondary", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        
        with col2:
            if st.button("Clear Cache", type="secondary", use_container_width=True):
                if clear_cache():
                    st.success("Cache cleared")
                else:
                    st.error("Cache clear failed")
        
        with col3:
            debug_mode = st.checkbox("Show Reasoning", value=False, 
                                   help="Display the system's reasoning and query analysis")
        
        with col4:
            st.metric("Messages", len(st.session_state.chat_history))
        
        with col5:
            st.metric("Session", st.session_state.session_id[:8])
        
        with col6:
            st.checkbox("Auto-scroll", value=st.session_state.auto_scroll, 
                       help="Automatically scroll to new messages")
        
        with col7:
            # Status indicator
            status_color = "status-online" if check_api_health() else "status-offline"
            status_text = "Online" if check_api_health() else "Offline"
            st.markdown(f"""
            <div class="status-indicator">
                <div class="status-dot {status_color}"></div>
                {status_text}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Example queries section
    example_queries = [
        "What are Carlos Garcia's Hogan scores?",
        "Compare Carlos Garcia and Carlos Gonzalez's Ambition scores",
        "Who has the highest Prudence score?",
        "Show me employees with high Leadership potential",
        "Who would be best for a customer service role?"
    ]
    
    with st.container():
        st.markdown('<div class="example-queries">', unsafe_allow_html=True)
        st.markdown('<h4>💡 Quick Examples</h4>', unsafe_allow_html=True)
        
        cols = st.columns(5)
        for i, query in enumerate(example_queries):
            with cols[i]:
                if st.button(query[:30] + "..." if len(query) > 30 else query, 
                           key=f"example_{i}", use_container_width=True):
                    st.session_state.pending_query = query
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Chat header
    st.markdown(f'''
    <div class="chat-header">
        <span>💬 Talent Intelligence Assistant</span>
        <span style="font-size: 12px; opacity: 0.8;">Session: {st.session_state.session_id[:8]}</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Chat messages area
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        for i, message in enumerate(st.session_state.chat_history):
            # Ensure message is a dictionary
            if isinstance(message, tuple):
                # Convert old tuple format to new dictionary format
                if len(message) >= 2:
                    role = "user" if message[0] == "You" else "assistant"
                    content = message[1]
                    message = {
                        "role": role,
                        "content": content,
                        "timestamp": time.time()
                    }
                    st.session_state.chat_history[i] = message
            
            # Now handle as dictionary
            if isinstance(message, dict):
                role = message.get("role", "assistant")
                content = message.get("content", "")
                
                # Message bubble
                if role == "user":
                    st.markdown(f'''
                    <div class="message user">
                        <div class="message-bubble">{content}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="message assistant">
                        <div class="message-bubble">{content}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Show reasoning if enabled and available
                if debug_mode and message.get("analysis"):
                    reasoning_text = format_reasoning_display(
                        message["analysis"],
                        message.get("source", "unknown"),
                        message.get("confidence", "unknown")
                    )
                    
                    with st.expander("🔍 View Reasoning", expanded=False):
                        st.markdown(reasoning_text)
                        
                        # Show raw analysis data
                        with st.expander("📊 Raw Analysis Data", expanded=False):
                            st.json(message["analysis"])
    
    else:
        # Welcome message
        st.markdown('''
        <div class="message assistant">
            <div class="message-bubble">
                👋 Welcome to the Talent Intelligence Assistant! I can help you with:
                <br><br>
                • <strong>Individual queries:</strong> "What are Carlos Garcia's Hogan scores?"
                <br>
                • <strong>Comparisons:</strong> "Compare Carlos and Carlos Gonzalez's Ambition scores"
                <br>
                • <strong>Rankings:</strong> "Who has the highest Prudence score?"
                <br>
                • <strong>General queries:</strong> "Who would be best for a customer service role?"
                <br><br>
                Try one of the example queries above or ask your own question!
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input area
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
    
    # Handle example query selection
    user_input = st.chat_input("Ask about employees, scores, or find candidates...")
    
    if "pending_query" in st.session_state:
        user_input = st.session_state.pending_query
        del st.session_state.pending_query
    
    if user_input:
        # Add user message to chat
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": time.time()
        })
        
        # Show loading state
        with st.spinner("Processing your query..."):
            # Send to API
            response = send_chat_message(user_input, st.session_state.session_id)
            
            # Add assistant response to chat
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.get("response", "No response received"),
                "analysis": response.get("analysis"),
                "source": response.get("source"),
                "confidence": response.get("confidence"),
                "timestamp": time.time()
            })
        
        # Auto-scroll to bottom
        if st.session_state.auto_scroll:
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Help section
    with st.expander("📚 How to use the Talent Explorer", expanded=False):
        st.markdown("""
        **Getting Started:**
        
        **Individual Queries:**
        - "What are [Employee Name]'s Hogan scores?"
        - "Show me [Employee Name]'s work experience"
        - "What are [Employee Name]'s strengths?"
        
        **Comparison Queries:**
        - "Compare [Employee 1] and [Employee 2]'s [Trait] scores"
        - "Who has higher [Trait] between [Employee 1] and [Employee 2]?"
        
        **Ranking Queries:**
        - "Who has the highest [Trait] score?"
        - "Top 5 employees by [Trait]"
        - "Show employees with [Trait] above [Score]"
        
        **General Queries:**
        - "Who would be best for a [Role/Project]?"
        - "Find employees with [Skill/Experience]"
        - "Who has experience in [Industry/Technology]?"
        
        **Assessment Types:**
        - **Hogan:** Personality, Development, Values assessments
        - **IDI:** Individual Directions Inventory
        
        **Common Traits:**
        - **HPI:** Adjustment, Ambition, Sociability, Prudence, etc.
        - **HDS:** Excitable, Skeptical, Cautious, Bold, etc.
        - **MVPI:** Recognition, Power, Affiliation, Security, etc.
        """)

if __name__ == "__main__":
    render_talent_explorer()