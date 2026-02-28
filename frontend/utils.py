import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
    /* Background color */
    .stApp {
        background-color: #F7F9FC;
    }
    
    /* Cards */
    .issues-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #111827 !important;
    }
    
    /* Secondary Text */
    .secondary-text {
        color: #6B7280;
        margin-bottom: 0.5rem;
    }
    
    /* Highlight Color */
    .highlight-text {
        color: #2563EB;
        font-weight: 500;
    }
    
    /* Emergency Color */
    .emergency-badge {
        color: #EF4444 !important;
        font-weight: bold;
        background-color: #FEE2E2;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
    /* Category tag */
    .category-badge {
        color: #2563EB;
        background-color: #DBEAFE;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 0.5rem;
        margin-right: 0.5rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)
