import streamlit as st
import requests
from streamlit_js_eval import get_geolocation

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

st.title("Issues Dashboard")
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
use_location = st.toggle("Filter by My Location", value=False)

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

# --- DATA TABLE (With Inline Expansion) ---
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
        raw_desc = issue.get('description', '').replace('\n', ' ')
        desc_preview = raw_desc[:75] + "..." if len(raw_desc) > 75 else raw_desc
        img_html = f"<div style='margin-top:8px;'><img src='{issue.get('image_url')}' style='width:100px; height:60px; object-fit:cover; border-radius:6px; border:1px solid #e2e8f0;'/></div>" if issue.get("image_url") else ""
        cols[1].markdown(f"**{desc_preview}**<br><span style='font-size:0.85rem; color:#64748b;'>{issue.get('title', 'Issue')}</span>{img_html}", unsafe_allow_html=True)
        
        # Location
        cols[2].markdown(f"<span style='font-size:0.9rem;'>{issue.get('ward', 'General')}</span>", unsafe_allow_html=True)
        
        # Date
        cols[3].markdown(f"<span style='font-size:0.9rem;'>{issue.get('date', 'Recent')}</span>", unsafe_allow_html=True)
        
        # Votes
        cols[4].markdown(f"<span style='font-size:1.1rem; font-weight:bold;'>{issue.get('votes', 0)}</span>", unsafe_allow_html=True)
        
        # Action Button (Inline Expand)
        is_expanded = st.session_state.get(f"expand_{issue['id']}", False)
        
        with cols[5]:
            # Instead of navigating, toggle the state
            if st.button("Close" if is_expanded else "Expand", key=f"view_{issue['id']}", use_container_width=True, type="primary" if is_expanded else "secondary"):
                st.session_state[f"expand_{issue['id']}"] = not is_expanded
                st.rerun()
                
        # --- INLINE EXPANDED DETAILS ---
        if st.session_state.get(f"expand_{issue['id']}", False):
            with st.container(border=True):
                # Fetch Timeline Data dynamically
                tl_data = []
                try:
                    tl_res = requests.get(f"{API_URL}/api/timeline/{issue['id']}", timeout=3)
                    if tl_res.status_code == 200:
                        tl_data = tl_res.json()
                except:
                    pass
                    
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.markdown(f"<h3 style='margin-bottom:0px;'>{issue.get('title', 'Issue Details')}</h3>", unsafe_allow_html=True)
                    
                    # Badges row
                    b_color = "#f59e0b" if status_color == "#f59e0b" else ("#10b981" if status_color == "#10b981" else "#ef4444")
                    badge_html = f"<span style='background-color:{b_color}15; color:{b_color}; padding:4px 10px; border-radius:4px; font-weight:600; font-size:0.8rem; border:1px solid {b_color}40;'>{issue.get('status', 'Pending')}</span>"
                    if str(issue.get("status", "")).lower() in ["in progress", "resolved"]:
                        badge_html += f" <span style='background-color:#10b98115; color:#10b981; padding:4px 10px; border-radius:4px; font-weight:600; font-size:0.8rem; border:1px solid #10b98140;'>:material/verified: Verified Authority Update</span>"
                    
                    st.markdown(f"<div style='margin:10px 0 20px 0;'>{badge_html}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**Description:** {issue.get('description', '')}")
                    if issue.get('latitude') and issue.get('longitude'):
                        st.markdown(f"**GPS Coordinates:** {issue['latitude']}, {issue['longitude']}")
                    st.markdown(f"**Category:** {issue.get('category', 'General')}")
                    
                    if issue.get('image_url'):
                        st.image(issue['image_url'], caption="High-Res Evidence", use_container_width=True)
                        
                    # --- CIVIC TIMELINE ---
                    st.markdown("<h4 style='margin-top:20px; border-bottom:1px solid #334155; padding-bottom:5px;'>Issue Timeline</h4>", unsafe_allow_html=True)
                    if not tl_data:
                        st.markdown("<p style='color:#64748b;'>Timeline context processing...</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='timeline-container'>", unsafe_allow_html=True)
                        for ev in tl_data:
                            st.markdown(f"""
                            <div class='timeline-item'>
                                <div class='timeline-date'>{ev.get('date', '')}</div>
                                <h5 class='timeline-event'>{ev.get('event', '')}</h5>
                                <p class='timeline-desc'>{ev.get('description', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                
                with col_right:
                    # Transparency Info Box
                    auth_name = f"{issue.get('ward', 'Mumbai')} Municipal Dept" if str(issue.get("status", "")).lower() != "pending" else "Pending Allocation"
                    st.markdown(f"""
                    <div style='background-color:#1e293b; padding:20px; border-radius:10px; border:1px solid #334155; margin-bottom:20px;'>
                        <h4 style='margin-top:0; color:#e2e8f0; font-size:1.1rem;'>Transparency Info</h4>
                        <hr style='border-color:#334155; margin:10px 0;'>
                        <p style='margin:5px 0; font-size:0.9rem; color:#94a3b8;'><strong>Publicly Tracked Since:</strong><br>{issue.get('date', 'Recent')}</p>
                        <p style='margin:15px 0 5px 0; font-size:0.9rem; color:#94a3b8;'><strong>Total Supporters:</strong><br><span style='color:#e2e8f0; font-weight:bold; font-size:1.1rem;'>{issue.get('votes', 0)} citizens</span></p>
                        <p style='margin:15px 0 0 0; font-size:0.9rem; color:#94a3b8;'><strong>Authority Responsible:</strong><br><span style='color:#3b82f6;'>{auth_name}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    v_btn = st.button("Upvote to Escalate", key=f"upvote_{issue['id']}", type="primary", use_container_width=True, icon=":material/thumb_up:")
                    if v_btn:
                        try:
                            res = requests.post(f"{API_URL}/api/vote/{issue['id']}")
                            if res.status_code == 200:
                                st.toast("Vote Added Successfully!", icon=":material/check_circle:")
                                st.rerun()
                            else:
                                st.error("Failed to register vote.")
                        except:
                            st.error("Network error.")
                            
                    if st.button("Fullscreen Map", key=f"details_{issue['id']}", use_container_width=True, icon=":material/open_in_new:"):
                        st.query_params.update({"id": issue['id']})
                        st.switch_page("pages/Issue_Detail.py")
                        
        st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.5;'>", unsafe_allow_html=True)

render_footer()
