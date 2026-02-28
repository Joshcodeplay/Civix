import streamlit as st
import sys
import os

# Ensure the frontend directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Vox",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define pages for navigation
pages = [
    st.Page("pages/Home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/Report_Issue.py", title="Report Issue", icon="📝"),
    st.Page("pages/Issues_Feed.py", title="Issues Feed", icon="📋"),
    st.Page("pages/Map_View.py", title="Map View", icon="🗺️"),
    st.Page("pages/Notices.py", title="Government Notices", icon="🏛️"),
    st.Page("pages/Issue_Detail.py", title="Issue Detail", icon="🔍"),
    st.Page("pages/My_Reports.py", title="My Reports", icon="👤")
]

try:
    pg = st.navigation(pages, position="hidden")
    pg.run()
except Exception as e:
    # Fallback to sidebar if position="hidden" fails (older streamlit version)
    pg = st.navigation(pages)
    pg.run()
