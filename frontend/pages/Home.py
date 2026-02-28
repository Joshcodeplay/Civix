import streamlit as st
import requests
from streamlit_js_eval import get_geolocation
from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

API_URL = "http://localhost:8000"

st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; color: #1e293b; font-family: \"Bebas Neue\", sans-serif; letter-spacing: 1px;'>AI-Powered Civic Intelligence</h1>", unsafe_allow_html=True)

# --- STATS ROW ---
try:
    stats_res = requests.get(f"{API_URL}/api/dashboard_stats", timeout=5)
    stats = stats_res.json() if stats_res.status_code == 200 else {"total": 0, "active": 0, "resolved": 0, "emergency": 0}
except:
    stats = {"total": 0, "active": 0, "resolved": 0, "emergency": 0}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 4px solid #3b82f6;'><p style='margin:0; color:#64748b; font-weight:600;'>Total Issues</p><h1 style='margin:10px 0; color:#3b82f6;'>{stats['total']}</h1></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 4px solid #f59e0b;'><p style='margin:0; color:#64748b; font-weight:600;'>Active</p><h1 style='margin:10px 0; color:#f59e0b;'>{stats['active']}</h1></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 4px solid #10b981;'><p style='margin:0; color:#64748b; font-weight:600;'>Resolved</p><h1 style='margin:10px 0; color:#10b981;'>{stats['resolved']}</h1></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 4px solid #ef4444;'><p style='margin:0; color:#64748b; font-weight:600;'>Emergency</p><h1 style='margin:10px 0; color:#ef4444;'>{stats['emergency']}</h1></div>", unsafe_allow_html=True)

st.divider()

# --- INSIGHTS & RECENT ---
left_col, right_col = st.columns([1, 2])

with left_col:
    st.markdown("### 🧠 Civic Intelligence")
    try:
        ins_res = requests.get(f"{API_URL}/api/insights", timeout=5)
        insights = ins_res.json() if ins_res.status_code == 200 else {"top_category": "Loading...", "top_ward": "Loading...", "trending": []}
    except:
        insights = {"top_category": "Unknown", "top_ward": "Unknown", "trending": []}
        
    st.markdown(f"""
<div class='issues-card' style='padding: 20px;'>
    <p style='margin:0 0 5px 0; font-size:0.9rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold;'>Most Reported Issue Type</p>
    <h4 style='margin:0 0 1.5rem 0;'>{insights['top_category']}</h4>
    <p style='margin:0 0 5px 0; font-size:0.9rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold;'>Red Zone Area</p>
    <h4 style='margin:0 0 1.5rem 0;'>{insights['top_ward']}</h4>
    <p style='margin:0 0 10px 0; font-size:0.9rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold;'>Trending Issues</p>
    <ul style='margin:0; padding-left:1.2rem; line-height:1.6;'>
        {''.join([f"<li>{t}</li>" for t in insights.get('trending', [])])}
    </ul>
</div>
""", unsafe_allow_html=True)

with right_col:
    st.markdown("### 📋 Recent Platform Activity")
    
    # --- LOCATION BASED FILTERING ---
   
    
    if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
        location = get_geolocation("Fetch Location")
        if location and "coords" in location:
            st.session_state["user_lat"] = location["coords"]["latitude"]
            st.session_state["user_lon"] = location["coords"]["longitude"]
            st.rerun()
            
        l_col1, l_col2 = st.columns(2)
        man_lat = l_col1.number_input("Latitude", value=19.0760, format="%.4f", key="home_lat")
        man_lon = l_col2.number_input("Longitude", value=72.8777, format="%.4f", key="home_lon")
        if st.button("Use Manual Location", key="home_loc_btn"):
            st.session_state["user_lat"] = man_lat
            st.session_state["user_lon"] = man_lon
            st.rerun()
            
    user_lat = st.session_state.get("user_lat")
    user_lon = st.session_state.get("user_lon")
    
    radius = st.slider("Select Radius (km)", 1, 20, 5)
    
    issues_url = f"{API_URL}/api/issues"
    if user_lat and user_lon:
        issues_url += f"?lat={user_lat}&lon={user_lon}&radius={radius}"
        st.info(f"Showing issues within {radius} km of your location")
    else:
        st.info("Showing all Mumbai issues")
    
    try:
        response = requests.get(issues_url, timeout=5)
        if response.status_code == 200:
            issues = response.json()[:3]  # Only show top 3
            if not issues:
                st.info("No reported issues yet.")
            else:
                for issue in issues:
                    badge_color = "#ef4444" if issue['emergency'] else ("#10b981" if issue.get("status") == "Resolved" else "#3b82f6")
                    status_text = issue.get("status", "Pending")
                    title_text = issue.get('title', f"Issue #{issue['id']}")
                    
                    html_card = f"""
<div class="issues-card" style="margin-bottom: 1rem; border-left: 4px solid {badge_color}; padding: 15px 20px;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span class="category-badge" style="background-color: {badge_color}15; color: {badge_color}; border: 1px solid {badge_color}30; margin:0;">{status_text}</span>
                <span style="font-size:0.85rem; color:#64748b;">• {issue.get('date', 'Recent')}</span>
            </div>
            <h4 style="margin: 0 0 8px 0; color:#0f172a;">{title_text}</h4>
            <p class="secondary-text" style="margin:0; font-size: 0.95rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{issue['description']}</p>
        </div>
        <div style="text-align: right; min-width: 60px;">
            <div style="background-color: #f1f5f9; padding: 5px 10px; border-radius: 6px; display:inline-block;">
                <span style="font-size:1.1rem; color:#475569; font-weight:bold;">⬆️ {issue['votes']}</span>
            </div>
        </div>
    </div>
</div>
"""
                    st.markdown(html_card, unsafe_allow_html=True)
                
                if st.button("View All Issues ➔", use_container_width=True):
                    st.switch_page("pages/Issues_Feed.py")
        else:
            st.error("Error fetching issues.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

render_footer()
