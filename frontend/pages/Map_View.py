import streamlit as st
import requests
from streamlit_folium import st_folium
import folium

from utils import apply_custom_css

apply_custom_css()

st.title("🗺️ Map View")
st.write("Visualize civic issues across the city.")

API_URL = "http://localhost:8000"

def fetch_issues():
    try:
        response = requests.get(f"{API_URL}/issues", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching issues: {e}")
    return []

issues = fetch_issues()

# Calculate center from data, or default to some coordinates
center_lat, center_lon = 19.0760, 72.8777 # Default to Mumbai
if issues:
    valid_coords = [(iss.get("latitude"), iss.get("longitude")) for iss in issues if iss.get("latitude") and iss.get("longitude")]
    if valid_coords:
        center_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
        center_lon = sum(c[1] for c in valid_coords) / len(valid_coords)

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

for issue in issues:
    lat = issue.get("latitude")
    lon = issue.get("longitude")
    if lat and lon:
        desc = issue.get("description", "No description")
        votes = issue.get("votes", 0)
        is_emergency = issue.get("emergency", False)
        
        color = "red" if is_emergency else "blue"
        icon = folium.Icon(color=color, icon="info-sign")
        
        popup_html = f"""
        <div style="width: 200px; font-family: sans-serif;">
            <b>{desc}</b><br/><br/>
            Votes: {votes}<br/>
            {'<b style="color:red; margin-top:5px; display:block;">🚨 EMERGENCY</b>' if is_emergency else ''}
        </div>
        """
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=desc[:30] + "...",
            icon=icon
        ).add_to(m)

st_data = st_folium(m, width=1200, height=600, returned_objects=[])
