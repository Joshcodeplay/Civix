import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
from streamlit_geolocation import streamlit_geolocation

from utils import apply_custom_css

apply_custom_css()

st.title("📝 Report an Issue")
st.write("Help us improve the city by reporting civic issues.")

API_URL = "http://localhost:8000"

# Session state to store parsing results
if "parsed_category" not in st.session_state:
    st.session_state.parsed_category = None
if "parsed_description" not in st.session_state:
    st.session_state.parsed_description = None

# Step 1: Description
st.header("Step 1 — Issue Description")
user_input = st.text_area("Describe the Issue", placeholder="Garbage not collected near station")

# Step 2: Analyze
st.header("Step 2 — Analyze Issue Button")
if st.button("Analyze Issue", type="primary"):
    if user_input.strip():
        try:
            with st.spinner("Analyzing..."):
                response = requests.post(f"{API_URL}/parse_issue", json={"text": user_input}, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.parsed_category = data.get("category", "Unknown")
                    st.session_state.parsed_description = data.get("description", user_input)
                else:
                    st.error("Failed to parse issue.")
        except Exception as e:
            st.error(f"API Error: {e}")
    else:
        st.warning("Please enter a description first.")

if st.session_state.parsed_category:
    st.success("Analysis Complete!")
    st.markdown(f"**Category:** <span class='highlight-text'>{st.session_state.parsed_category}</span>", unsafe_allow_html=True)
    st.markdown(f"**Clean Description:** {st.session_state.parsed_description}")

# Step 3: Location
st.header("Step 3 — Location Section")
st.write("Detect My Location")
location = streamlit_geolocation()

lat, lon = None, None
if location and location.get('latitude') and location.get('longitude'):
    lat = location['latitude']
    lon = location['longitude']
    st.success(f"Detected: Latitude {lat}, Longitude {lon}")
else:
    st.info("Location not detected yet. Click the button above to detect, or manually select on the map below.")

# Step 4: Map
st.header("Step 4 — Manual Map Selection")
# Default center (e.g., typical city center)
center_lat = lat if lat else 19.0760
center_lon = lon if lon else 72.8777

m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
if lat and lon:
    folium.Marker([lat, lon], tooltip="Detected Location").add_to(m)

st.write("Click on the map to set the exact location.")
map_data = st_folium(m, width=700, height=400)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"Selected: Latitude {lat}, Longitude {lon}")

# Step 5: Emergency
st.header("Step 5 — Emergency Option")
is_emergency = st.checkbox("Mark as Emergency")
if is_emergency:
    st.markdown("<p class='emergency-text'>Emergency Alert Enabled</p>", unsafe_allow_html=True)

# Step 6: Submit
st.header("Step 6 — Submit Issue")
if st.button("Submit Issue", type="primary", use_container_width=True):
    if not st.session_state.parsed_category:
        st.error("Please analyze the issue first (Step 2).")
    elif not lat or not lon:
        st.error("Please provide a location (Step 3 or 4).")
    else:
        payload = {
            "description": st.session_state.parsed_description or user_input,
            "category": st.session_state.parsed_category,
            "latitude": lat,
            "longitude": lon,
            "emergency": is_emergency
        }
        try:
            with st.spinner("Submitting..."):
                response = requests.post(f"{API_URL}/report_issue", json=payload, timeout=10)
                if response.status_code == 200:
                    st.success("Issue submitted successfully!")
                    # Reset state
                    st.session_state.parsed_category = None
                    st.session_state.parsed_description = None
                    st.info("You can refresh the page to clear the form completely.")
                else:
                    st.error("Failed to submit issue.")
        except Exception as e:
            st.error(f"API Error: {e}")
