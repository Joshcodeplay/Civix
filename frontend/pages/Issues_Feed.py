import streamlit as st
import requests
from streamlit_js_eval import get_geolocation

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

st.title("📋 Issues Dashboard")
st.markdown("<p style='color:#64748b;'>Browse, search, and track community issues.</p>", unsafe_allow_html=True)
st.divider()

API_URL = "http://localhost:8000"

@st.cache_data(ttl=60)
def fetch_issues(lat=None, lon=None, radius=None):
    url = f"{API_URL}/api/issues"
    if lat and lon and radius:
        url += f"?lat={lat}&lon={lon}&radius={radius}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        pass
    return []

# --- LOCATION BASED FILTERING ---
use_location = st.toggle("📍 Filter by My Location", value=False)

filter_lat, filter_lon, filter_radius = None, None, None

if use_location:
    if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
        location = get_geolocation("Fetch Location")
        if location and "coords" in location:
            st.session_state["user_lat"] = location["coords"]["latitude"]
            st.session_state["user_lon"] = location["coords"]["longitude"]
            st.rerun()
            
        l_col1, l_col2 = st.columns(2)
        man_lat = l_col1.number_input("Latitude", value=19.0760, format="%.4f", key="issues_lat")
        man_lon = l_col2.number_input("Longitude", value=72.8777, format="%.4f", key="issues_lon")
        if st.button("Use Manual Location", key="issues_loc_btn"):
            st.session_state["user_lat"] = man_lat
            st.session_state["user_lon"] = man_lon
            st.rerun()

    filter_lat = st.session_state.get("user_lat")
    filter_lon = st.session_state.get("user_lon")
    
    if filter_lat and filter_lon:
        filter_radius = st.slider("Select Radius (km)", 1, 20, 5)
        st.info(f"Showing issues within {filter_radius} km of your location")

raw_issues = fetch_issues(filter_lat, filter_lon, filter_radius)

# --- FILTERS ---
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    cat_filter = st.selectbox("Category", ["All"] + list(set(i.get('category', 'General') for i in raw_issues if 'category' in i)))
with col_f2:
    status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Resolved"])
with col_f3:
    search_q = st.text_input("Search", placeholder="Search keywords...")

# --- APPLY FILTERS ---
filtered_issues = []
for iss in raw_issues:
    if cat_filter != "All" and iss.get('category') != cat_filter: continue
    if status_filter != "All" and iss.get('status', 'Pending').lower() != status_filter.lower(): continue
    if search_q and search_q.lower() not in iss.get('description', '').lower() and search_q.lower() not in iss.get('title', '').lower(): continue
    filtered_issues.append(iss)

# --- DATA TABLE (List View) ---
if not filtered_issues:
    st.info("No issues match your filters.")
else:
    # Table Header
    header_cols = st.columns([1, 2.5, 1, 1, 1, 1])
    headers = ["ID & Status", "Description", "Location", "Date", "Votes", "Actions"]
    for col, title in zip(header_cols, headers):
        col.markdown(f"**{title}**")
    st.divider()
    
    # Table Rows
    for issue in filtered_issues:
        cols = st.columns([1, 2.5, 1, 1, 1, 1])
        
        # ID & Status
        status_color = "#f59e0b" if issue.get("status", "").lower() == "in progress" else ("#10b981" if issue.get("status", "").lower() == "resolved" else "#ef4444")
        cols[0].markdown(f"**#{issue['id']}**<br><span style='color:{status_color}; font-size:0.85rem; font-weight:600;'>{issue.get('status', 'Pending')}</span>", unsafe_allow_html=True)
        
        # Description
        desc_preview = issue.get('description', '')[:60] + "..." if len(issue.get('description', '')) > 60 else issue.get('description', '')
        cols[1].markdown(f"**{issue.get('title', 'Issue')}**<br><span style='font-size:0.85rem; color:#64748b;'>{desc_preview}</span>", unsafe_allow_html=True)
        
        # Location
        cols[2].markdown(f"<span style='font-size:0.9rem;'>{issue.get('ward', 'General')}</span>", unsafe_allow_html=True)
        
        # Date
        cols[3].markdown(f"<span style='font-size:0.9rem;'>{issue.get('date', 'Recent')}</span>", unsafe_allow_html=True)
        
        # Votes
        cols[4].markdown(f"<span style='font-size:1.1rem; font-weight:bold;'>{issue.get('votes', 0)}</span>👍", unsafe_allow_html=True)
        
        # Action Button (Navigate to details)
        with cols[5]:
            if st.button("View", key=f"view_{issue['id']}", use_container_width=True):
                # Using session state to pass context instead of query params if preferred, or query params in latest streamlit:
                st.query_params.update({"id": issue['id']})
                st.switch_page("pages/Issue_Detail.py")
                
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.5;'>", unsafe_allow_html=True)

render_footer()
