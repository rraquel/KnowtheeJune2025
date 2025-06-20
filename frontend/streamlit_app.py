import streamlit as st
from talent_explorer_tab import render_talent_explorer

# Page configuration
st.set_page_config(
    page_title="KnowThee Talent Intelligence",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for the beautiful UI styling
st.markdown("""
<style>
    /* Import Poppins font for better typography */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Set base zoom and font sizing for better readability */
    html {
        zoom: 1.4;
        font-size: 18px;
    }
    
    body {
        background-color: #f8f9fa;
        font-size: 1.15rem;
        font-family: 'Poppins', sans-serif;
        color: #0a2c4d;
    }
    
    /* Hide default Streamlit elements */
    .stApp > header {
        background-color: transparent;
        height: 0;
    }
    
    .stApp > div > div > div > div > section > div {
        padding-top: 0;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
        background-color: #f8f9fa;
    }
    
    /* Fixed top banner like the original */
    .top-banner {
        position: fixed;
        left: 0;
        top: 0;
        width: 100vw;
        background: #0a2c4d;
        text-align: center;
        padding: 1.5rem 0.75rem;
        z-index: 100;
    }
    
    .banner-content {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .banner-text {
        color: #ffc72c !important;
        font-size: 3rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif !important;
        letter-spacing: 2.5px;
        text-align: center;
    }
    
    .top-spacer {
        height: 6.5rem;
    }
    
    /* Enhanced tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background-color: #ffffff;
        padding: 0;
        border-bottom: none;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 70px;
        background-color: transparent;
        border-radius: 0;
        color: #6b7280;
        font-weight: 600;
        font-size: 1.6rem;
        font-family: 'Poppins', sans-serif;
        padding: 0 2.5rem;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f9fafb;
        color: #0a2c4d;
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #0a2c4d;
        border-bottom: 3px solid #0a2c4d;
        font-weight: 700;
    }
    
    /* Enhanced content area styling */
    .content-wrapper {
        padding: 2rem 0;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Enhanced Leader Insights styling */
    .leader-insights-header {
        color: #0a2c4d;
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-family: 'Poppins', sans-serif;
    }
    
    .insight-description {
        font-size: 1.4rem;
        color: #0a2c4d;
        margin-bottom: 2.5rem;
        line-height: 1.7;
        max-width: 900px;
        font-weight: 400;
    }
    
    .upload-section-header {
        color: #0a2c4d;
        font-size: 2.3rem;
        font-weight: 700;
        margin: 2.5rem 0 1.5rem 0;
        font-family: 'Poppins', sans-serif;
    }
    
    .upload-description {
        color: #0a2c4d;
        font-size: 1.4rem;
        margin-bottom: 2rem;
        line-height: 1.6;
        max-width: 900px;
        font-weight: 400;
    }
    
    /* Enhanced requirements box */
    .upload-requirements {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(10, 44, 77, 0.1);
    }
    
    .requirements-text {
        color: #0a2c4d;
        font-size: 1.3rem;
        margin: 0;
        font-weight: 500;
        line-height: 1.5;
    }
    
    .upload-label {
        font-size: 1.3rem;
        font-weight: 600;
        color: #0a2c4d;
        margin-bottom: 1rem;
        display: block;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Enhanced file uploader styling */
    .stFileUploader {
        margin-top: 1rem;
    }
    
    .stFileUploader > div > div > div > div {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 3px dashed #0a2c4d;
        border-radius: 20px;
        padding: 3.5rem 2.5rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        min-height: 120px;
    }
    
    .stFileUploader > div > div > div > div:hover {
        border-color: #ffc72c;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(10, 44, 77, 0.15);
    }
    
    .stFileUploader > div > div > div > div::before {
        content: "☁️";
        font-size: 3.5rem;
        display: block;
        margin-bottom: 1rem;
        opacity: 0.8;
    }
    
    /* Enhanced text styling throughout */
    .stCaption, .stMarkdown, .stTextInput, .stTextArea, .stFileUploader {
        font-size: 1.3rem !important;
        color: #0a2c4d !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Enhanced button styling */
    .stButton > button {
        background: linear-gradient(135deg, #0a2c4d 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(10, 44, 77, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(10, 44, 77, 0.3);
        background: linear-gradient(135deg, #1e40af 0%, #0a2c4d 100%);
    }
    
    /* Enhanced success message styling */
    .stSuccess {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    
    .stSuccess > div {
        color: #0a2c4d !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    
    /* Enhanced coming soon styling */
    .coming-soon {
        text-align: center;
        padding: 4rem 3rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 24px;
        margin: 3rem auto;
        max-width: 700px;
        box-shadow: 0 8px 24px rgba(10, 44, 77, 0.1);
    }
    
    .coming-soon h3 {
        color: #0a2c4d;
        font-size: 2.2rem;
        margin-bottom: 1.5rem;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
    }
    
    .coming-soon p {
        color: #0a2c4d;
        font-size: 1.3rem;
        line-height: 1.6;
        font-weight: 400;
        opacity: 0.8;
    }
    
    /* Make all text elements use consistent styling - AGGRESSIVE APPROACH */
    p, div, span, label, a {
        font-size: 1.3rem !important;
        color: #0a2c4d !important;
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Make buttons and form elements larger */
    button, input, select, textarea, .stButton>button, .stSelectbox>div>div, [data-testid="stFileUploader"] {
        font-size: 1.3rem !important;
        color: #0a2c4d !important;
    }
    
    /* Make sure text in the file uploader is bigger */
    [data-testid="stFileUploader"] span {
        font-size: 1.3rem !important;
        color: #0a2c4d !important;
    }
    
    /* Increase size of question text area */
    textarea {
        min-height: 120px !important;
        font-size: 1.3rem !important;
        color: #0a2c4d !important;
    }
    
    /* AGGRESSIVE TAB FONT OVERRIDES - Target all tab elements */
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] * {
        font-size: 1.3rem !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Override any gray text colors */
    [style*="color: #888"], [style*="color: rgb(136, 136, 136)"], 
    [style*="color: gray"], [style*="color: #333"], [style*="color: rgb(51, 51, 51)"] {
        color: #0a2c4d !important;
    }
    
    /* Enhanced responsive design */
    @media (max-width: 768px) {
        .banner-text {
            font-size: 2.5rem;
        }
        
        .top-spacer {
            height: 4.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0 1.5rem;
            font-size: 1.4rem;
        }
        
        .leader-insights-header {
            font-size: 2rem;
        }
        
        .insight-description, .upload-description {
            font-size: 1.3rem;
        }
    }
</style>

<script>
// Set initial zoom level using JavaScript as a backup
document.body.style.zoom = "140%";

// Additional script to ensure text colors are applied to dynamically loaded content
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with gray text and change to blue
    const grayTexts = document.querySelectorAll('[style*="color: #888"], [style*="color: rgb(136, 136, 136)"], [style*="color: gray"], [style*="color: #333"], [style*="color: rgb(51, 51, 51)"]');
    grayTexts.forEach(element => {
        element.style.color = '#0a2c4d';
    });
    
    // Force tab font sizes after load
    const tabElements = document.querySelectorAll('.stTabs [data-baseweb="tab"] *');
    tabElements.forEach(element => {
        element.style.fontSize = '1.3rem';
        element.style.fontFamily = 'Poppins, sans-serif';
        element.style.fontWeight = '600';
    });
});
</script>
""", unsafe_allow_html=True)

# Add top banner like the original
st.markdown(
    '<div class="top-banner">'
    '<div class="banner-content">'
    '<div class="banner-text">LeaderInsight.ai</div>'
    '</div>'
    '</div>', 
    unsafe_allow_html=True
)
st.markdown('<div class="top-spacer"></div>', unsafe_allow_html=True)

# Navigation tabs
tabs = st.tabs(["👤 Leader Insights", "🔍 Talent Explorer", "📊 Organizational Pulse", "👥 Team Builder"])

with tabs[0]:  # Leader Insights tab
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Main content - no box wrapper
    st.markdown('<div class="leader-insights-header">👤 Leader Insights</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="insight-description">
    We will <strong>integrate the information</strong> that you provide—e.g., assessments, feedback, performance reviews, CVs, 360s, etc.—to <strong>answer questions you may have</strong> and <strong>generate a leadership profile</strong>.
    </div>
    """, unsafe_allow_html=True)
    
    # Upload section - no box wrapper
    st.markdown('<div class="upload-section-header">Documents about the Individual</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-description">
    Who are we profiling? Help us get to know this leader. The more data sources you share, the richer the integrated insights that we can provide.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-requirements">
        <p class="requirements-text">
        📁 <strong>File Upload Requirements:</strong> • File types: PDF, DOCX • Max file size: 50.0MB per file • Max total size: 200.0MB per upload session • Max files: 10 files at once • Min file size: 1KB
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<span class="upload-label">Upload PDF or DOCX</span>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Drag and drop files here",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="Limit 200MB per file • PDF, DOCX",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
        for file in uploaded_files:
            st.markdown(f"<div style='color: #0a2c4d; font-size: 1.1rem; margin: 0.5rem 0;'>📄 {file.name}</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:  # Talent Explorer tab
    render_talent_explorer()

with tabs[2]:  # Organizational Pulse tab
    st.markdown("""
    <div class="coming-soon">
        <h3>📊 Organizational Pulse</h3>
        <p>Comprehensive organizational analytics and insights coming soon!</p>
    </div>
    """, unsafe_allow_html=True)

with tabs[3]:  # Team Builder tab
    st.markdown("""
    <div class="coming-soon">
        <h3>👥 Team Builder</h3>
        <p>Intelligent team composition and optimization tools coming soon!</p>
    </div>
    """, unsafe_allow_html=True)
