import streamlit as st
import sys
import os

# Ensure the frontend directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="CivicSense",
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
]

pg = st.navigation(pages)
pg.run()
