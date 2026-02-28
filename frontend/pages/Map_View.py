import streamlit as st
import requests
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
def fetch_issues():
    try:
        response = requests.get(f"{API_URL}/api/issues", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching issues: {e}")
    return []

raw_issues = fetch_issues()

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
