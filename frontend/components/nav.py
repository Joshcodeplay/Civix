import streamlit as st

def render_nav():
    st.markdown("""
    <style>
        /* Hide sidebar toggle completely */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        /* Cleaner top header */
        header { visibility: hidden !important; }
        /* Move content up */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_logo, col_space, col1, col2, col3, col4, col5, col6 = st.columns([2.5, 0.5, 1, 1, 1, 1, 1.2, 1.2])
    
    with col_logo:
        st.markdown("<h3 style='margin: 0; padding: 0; color: #2563EB !important; font-family: \"Bebas Neue\", sans-serif; letter-spacing: 1px;'>🏙️ CivicSense</h3><p style='margin: 0; font-size: 0.8rem; color: #94a3b8 !important;'>AI-Powered Civic Intelligence Platform</p>", unsafe_allow_html=True)
        
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
    # Footer removed as requested
    pass
