import streamlit as st
import requests
from streamlit_js_eval import get_geolocation
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

st.title("🗺️ Civic Map Hub")
st.markdown("<p style='color:#64748b;'>Visualize and filter active civic issues across the metropolitan area.</p>", unsafe_allow_html=True)
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
        st.error(f"Error fetching issues: {e}")
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
        man_lat = l_col1.number_input("Latitude", value=19.0760, format="%.4f", key="map_lat")
        man_lon = l_col2.number_input("Longitude", value=72.8777, format="%.4f", key="map_lon")
        if st.button("Use Manual Location", key="map_loc_btn"):
            st.session_state["user_lat"] = man_lat
            st.session_state["user_lon"] = man_lon
            st.rerun()

    filter_lat = st.session_state.get("user_lat")
    filter_lon = st.session_state.get("user_lon")
    
    if filter_lat and filter_lon:
        filter_radius = st.slider("Select Radius (km)", 1, 20, 5)
        st.info(f"Showing issues within {filter_radius} km of your location")

raw_issues = fetch_issues(filter_lat, filter_lon, filter_radius)

# --- FILTERS ROW ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    view_mode = st.radio("View Mode", ["Markers", "Heatmap"], horizontal=True)
with col2:
    cat_filter = st.selectbox("Category", ["All"] + list(set(i.get('category', 'General') for i in raw_issues if 'category' in i)))
with col3:
    status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Resolved"])
with col4:
    emergency_filter = st.checkbox("🚨 Emergency Only")

# --- FILTER DATA ---
filtered_issues = []
heatmap_data = []

for iss in raw_issues:
    if cat_filter != "All" and iss.get('category') != cat_filter: continue
    if status_filter != "All" and iss.get('status', 'Pending').lower() != status_filter.lower(): continue
    if emergency_filter and not iss.get('emergency'): continue
    
    filtered_issues.append(iss)
    lat, lon = iss.get("latitude"), iss.get("longitude")
    if lat and lon:
        weight = 2 if iss.get('emergency') else 1
        heatmap_data.append([lat, lon, weight])

# --- MAP RENDERING ---
center_lat, center_lon = 19.0760, 72.8777 # Default to Mumbai
if heatmap_data:
    center_lat = sum(c[0] for c in heatmap_data) / len(heatmap_data)
    center_lon = sum(c[1] for c in heatmap_data) / len(heatmap_data)

m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

if view_mode == "Heatmap":
    if heatmap_data:
        HeatMap(heatmap_data, radius=15, blur=10).add_to(m)
    else:
        st.info("No data available for Heatmap in this specific filter view.")
else:
    for issue in filtered_issues:
        lat = issue.get("latitude")
        lon = issue.get("longitude")
        if lat and lon:
            desc = issue.get("description", "No description")
            votes = issue.get("votes", 0)
            is_emergency = issue.get("emergency", False)
            status = issue.get("status", "Pending")
            
            color = "red" if is_emergency else ("green" if status.lower() == "resolved" else "blue")
            icon = folium.Icon(color=color, icon="info-sign")
            
            html_popup = f"""
            <div style="font-family: sans-serif; min-width:200px;">
                <b style="color:#0f172a; font-size:14px;">{issue.get('title', 'Civic Issue')}</b><br>
                <span style="color:#64748b; font-size:12px;">{desc[:50]}...</span><br><br>
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:bold; color:#10b981;">{votes} Votes</span>
                    <span style="font-weight:bold; color:{color};">{status}</span>
                </div>
                { '<div style="margin-top:8px; color:#ef4444; font-weight:bold;">🚨 EMERGENCY HAZARD</div>' if is_emergency else '' }
            </div>
            """
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html_popup, max_width=300),
                tooltip=f"#{issue.get('id')} - {status}",
                icon=icon
            ).add_to(m)

st_data = st_folium(m, width=1200, height=600, returned_objects=[])

render_footer()
