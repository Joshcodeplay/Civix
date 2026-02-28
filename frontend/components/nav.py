import streamlit as st

def render_nav():
    st.markdown("""
    <style>
        /* Hide sidebar toggle completely */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        /* Cleaner top header */
        header { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)
    
    col_logo, col_space, col1, col2, col3, col4, col5, col6 = st.columns([2.5, 0.5, 1, 1, 1, 1, 1.2, 1.2])
    
    with col_logo:
        st.markdown("<h3 style='margin: 0; padding: 0; color: #2563EB; font-family: \"Bebas Neue\", sans-serif; letter-spacing: 1px;'>🏙️ CivicSense</h3><p style='margin: 0; font-size: 0.8rem; color: #6b7280;'>AI-Powered Civic Intelligence Platform</p>", unsafe_allow_html=True)
        
    with col1:
        st.page_link("pages/Home.py", label="Home")
    with col2:
        st.page_link("pages/Report_Issue.py", label="Report")
    with col3:
        st.page_link("pages/Issues_Feed.py", label="Issues")
    with col4:
        st.page_link("pages/Map_View.py", label="Map")
    with col5:
        st.page_link("pages/Notices.py", label="Notices")
    with col6:
        st.page_link("pages/My_Reports.py", label="My Profile")
        
    st.divider()

def render_footer():
    st.markdown("""
    <div style="background-color: #f8fafc; text-align: center; color: #64748b; margin-top: 60px; padding: 30px; border-top: 1px solid #e2e8f0; border-radius: 8px;">
        <h4 style="margin: 0; color: #334155;">CivicSense v1.0</h4>
        <p style="margin: 5px 0 0 0; font-weight: 500;">Ready for deployment.</p>
        <p style="font-size: 0.85rem; margin: 10px 0 0 0;">Public Transparency • AI Reporting Workflow • Government API Integration</p>
    </div>
    """, unsafe_allow_html=True)
