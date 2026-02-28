import streamlit as st
import requests
from streamlit_js_eval import get_geolocation
from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

API_URL = "http://localhost:8000"

st.markdown("""
<div style="text-align: center; margin: 2rem 0 3rem 0;">
    <h1 style='color: #1e293b; font-family: "Bebas Neue", sans-serif; letter-spacing: 2px; font-size: 4rem; margin-bottom: 0.5rem;'>AI-Powered Civic Intelligence</h1>
    <p style='color: #64748b; font-size: 1.2rem; max-width: 600px; margin: 0 auto;'>Report, track, and resolve community issues natively through real-time geo-spatial intelligence.</p>
</div>
""", unsafe_allow_html=True)

# --- STATS ROW ---
try:
    stats_res = requests.get(f"{API_URL}/api/dashboard_stats", timeout=5)
    stats = stats_res.json() if stats_res.status_code == 200 else {"total": 0, "active": 0, "resolved": 0, "emergency": 0}
except:
    stats = {"total": 0, "active": 0, "resolved": 0, "emergency": 0}

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 5px solid #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.15);'><p style='margin:0; color:#64748b; font-weight:700; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.85rem;'>Total Issues</p><h1 style='margin:15px 0 5px 0; color:#3b82f6; font-size: 3.8rem; line-height: 1;'>{stats['total']}</h1></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 5px solid #f59e0b; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.15);'><p style='margin:0; color:#64748b; font-weight:700; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.85rem;'>Active</p><h1 style='margin:15px 0 5px 0; color:#f59e0b; font-size: 3.8rem; line-height: 1;'>{stats['active']}</h1></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 5px solid #10b981; box-shadow: 0 10px 25px rgba(16, 185, 129, 0.15);'><p style='margin:0; color:#64748b; font-weight:700; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.85rem;'>Resolved</p><h1 style='margin:15px 0 5px 0; color:#10b981; font-size: 3.8rem; line-height: 1;'>{stats['resolved']}</h1></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='issues-card' style='text-align:center; border-top: 5px solid #ef4444; box-shadow: 0 10px 25px rgba(239, 68, 68, 0.15);'><p style='margin:0; color:#64748b; font-weight:700; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.85rem;'>Emergency</p><h1 style='margin:15px 0 5px 0; color:#ef4444; font-size: 3.8rem; line-height: 1;'>{stats['emergency']}</h1></div>", unsafe_allow_html=True)

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
<div class='issues-card' style='padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);'>
    <p style='margin:0 0 5px 0; font-size:1rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold; letter-spacing: 1px;'>Most Reported Issue Type</p>
    <h4 style='margin:0 0 1.5rem 0; font-size: 2.2rem; color: #0f172a;'>{insights['top_category']}</h4>
    <p style='margin:0 0 5px 0; font-size:1rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold; letter-spacing: 1px;'>Red Zone Area</p>
    <h4 style='margin:0 0 1.5rem 0; font-size: 2.2rem; color: #0f172a;'>{insights['top_ward']}</h4>
    <p style='margin:0 0 10px 0; font-size:1rem; color:#94a3b8 !important; text-transform:uppercase; font-weight:bold; letter-spacing: 1px;'>Trending Issues</p>
    <ul style='margin:0; padding-left:1.2rem; line-height:1.8; font-size: 1.1rem; color: #475569;'>
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
<div class="issues-card" style="margin-bottom: 1.5rem; border-left: 5px solid {badge_color}; padding: 20px 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.05);">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <span class="category-badge" style="background-color: {badge_color}15; color: {badge_color}; border: 1px solid {badge_color}30; margin:0; font-size: 0.85rem; padding: 4px 10px;">{status_text}</span>
                <span style="font-size:0.95rem; color:#64748b; font-weight: 500;">• {issue.get('date', 'Recent')}</span>
            </div>
            <h4 style="margin: 0 0 10px 0; color:#0f172a; font-size: 1.4rem;">{title_text}</h4>
            <p class="secondary-text" style="margin:0; font-size: 1.05rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.6;">{issue['description']}</p>
        </div>
        <div style="text-align: right; min-width: 70px;">
            <div style="background-color: #f8fafc; padding: 8px 12px; border-radius: 8px; display:inline-block; border: 1px solid #e2e8f0;">
                <span style="font-size:1.2rem; color:#475569; font-weight:bold;">⬆️ {issue['votes']}</span>
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
