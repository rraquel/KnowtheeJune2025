import streamlit as st
from backend.services.individual_profile_services import save_uploaded_files

def render_individual_profile():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

    # Section: Header
    st.markdown('<div class="leader-insights-header">👤 Leader Insights</div>', unsafe_allow_html=True)

    # Section: Description
    st.markdown("""
    <div class="insight-description">
    We will <strong>integrate the information</strong> that you provide—e.g., assessments, feedback, performance reviews, CVs, 360s, etc.—to <strong>answer questions you may have</strong> and <strong>generate a leadership profile</strong>.
    </div>
    """, unsafe_allow_html=True)

    # Section: Upload title
    st.markdown('<div class="upload-section-header">Documents about the Individual</div>', unsafe_allow_html=True)

    # Section: Upload description
    st.markdown("""
    <div class="upload-description">
    Who are we profiling? Help us get to know this leader. The more data sources you share, the richer the integrated insights that we can provide.
    </div>
    """, unsafe_allow_html=True)

    # Section: Requirements
    st.markdown("""
    <div class="upload-requirements">
        <p class="requirements-text">
        📁 <strong>File Upload Requirements:</strong> • File types: PDF, DOCX • Max file size: 50.0MB per file • Max total size: 200.0MB per upload session • Max files: 10 files at once • Min file size: 1KB
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Upload field
    st.markdown('<span class="upload-label">Upload PDF or DOCX</span>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Drag and drop files here",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="Limit 200MB per file • PDF, DOCX",
        label_visibility="collapsed"
    )

    if uploaded_files:
        saved_paths = save_uploaded_files(uploaded_files)
        st.success(f"✅ {len(saved_paths)} file(s) uploaded and saved successfully!")
        for path in saved_paths:
            st.markdown(
                f"<div style='color: #0a2c4d; font-size: 1.1rem; margin: 0.5rem 0;'>📄 {path}</div>",
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
