import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
from streamlit_geolocation import streamlit_geolocation

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

API_URL = "http://localhost:8000"

st.title("📝 Report an Issue")
st.markdown("<p style='color:#64748b; font-size:1.1rem;'>Help us improve the city by reporting civic issues through our AI-assisted reporting wizard.</p>", unsafe_allow_html=True)

# State Management
if "step" not in st.session_state:
    st.session_state.step = 1

if "report_data" not in st.session_state:
    st.session_state.report_data = {
        "description": "",
        "parsed_category": "",
        "parsed_description": "",
        "authority": "",
        "department": "",
        "expected_time": "",
        "lat": None,
        "lon": None,
        "name": "",
        "phone": "",
        "email": "",
        "photo": None,
        "emergency": False
    }

def next_step():
    st.session_state.step += 1
    st.rerun()

def prev_step():
    st.session_state.step -= 1
    st.rerun()

data = st.session_state.report_data

# Step 1: Describe Issue
if st.session_state.step == 1:
    st.markdown("### Report Issue – Step 1")
    with st.form("step1_form"):
        desc = st.text_area("Issue Description", value=data.get("description", ""), placeholder="e.g. Garbage not collected near the local station for 3 days.", height=150)
        
        if st.form_submit_button("Next →", type="primary"):
            if desc.strip():
                st.session_state.report_data["description"] = desc
                st.session_state.report_data["parsed_category"] = "" # Reset analysis on text change
                st.session_state.step += 1
                st.rerun()
            else:
                st.warning("Please enter a description.")

# Step 2: AI Analysis
elif st.session_state.step == 2:
    st.markdown("### Report Issue – Step 2")
    
    if not data.get("parsed_category"):
        with st.spinner("Analyzing text with Gemini AI..."):
            try:
                res1 = requests.post(f"{API_URL}/api/parse_issue", json={"text": data["description"]}, timeout=10)
                if res1.status_code == 200:
                    parsed = res1.json()
                    st.session_state.report_data["parsed_category"] = parsed.get("category", "General")
                    st.session_state.report_data["parsed_description"] = parsed.get("description", data["description"])
                
                payload2 = {
                    "description": st.session_state.report_data["parsed_description"],
                    "category": st.session_state.report_data["parsed_category"],
                    "location": "Mumbai Region" 
                }
                res2 = requests.post(f"{API_URL}/api/responsible_authority", json=payload2, timeout=10)
                if res2.status_code == 200:
                    auth_data = res2.json()
                    st.session_state.report_data["authority"] = auth_data.get("authority", "Municipal Corporation")
                    st.session_state.report_data["department"] = auth_data.get("department", "General")
                    st.session_state.report_data["expected_time"] = auth_data.get("expected_time", "Unknown")
                st.rerun()
            except Exception as e:
                st.error(f"API Error: {e}")
                
    if data.get("parsed_category"):
        st.markdown(f"""
        <div class='issues-card' style='border-left: 4px solid #3b82f6;'>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Category</p>
            <h4 style='margin:0 0 15px 0; color:#1e293b;'>{data['parsed_category']}</h4>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Clean Description</p>
            <p style='margin:0 0 15px 0;; color:#334155;'>{data['parsed_description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    if data.get("authority"):
        st.markdown("### Responsible Authority")
        st.markdown(f"""
        <div class='issues-card' style='border-left: 4px solid #10b981;'>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Responsible Authority Name</p>
            <h4 class='highlight-text' style='margin:0 0 15px 0;'>{data['authority']}</h4>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Department</p>
            <p style='margin:0 0 15px 0; color:#334155;'>{data['department']}</p>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Expected Fix Time</p>
            <h4 class='highlight-text' style='margin:0 0 5px 0; color:#f59e0b !important;'>{data['expected_time']}</h4>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("← Back"):
            prev_step()
    with col2:
        if st.button("Next →", type="primary") and data.get("parsed_category"):
            next_step()

# Step 3: Location
elif st.session_state.step == 3:
    st.markdown("### Report Issue – Step 3")
    st.write("Select your location using the map, auto-detect, or by searching an address.")
    
    # --- SEARCH BAR ---
    search_query = st.text_input("🔍 Search Location manually", placeholder="Enter area, landmark, or street in Mumbai...", key="loc_search")
    if st.button("Search Address", key="btn_search_loc"):
        if search_query.strip():
            try:
                with st.spinner("Searching..."):
                    headers = {'User-Agent': 'CivicSense/1.0'}
                    res = requests.get(f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json&limit=1", headers=headers, timeout=5)
                    if res.status_code == 200 and len(res.json()) > 0:
                        result = res.json()[0]
                        st.session_state.report_data["lat"] = float(result["lat"])
                        st.session_state.report_data["lon"] = float(result["lon"])
                        st.success(f"✅ Found: {result.get('display_name', 'Location')}")
                    else:
                        st.error("Location not found. Please try another term or use the map below.")
            except Exception as e:
                st.error("Error searching location. Please pinpoint it on the map manually.")
        else:
            st.warning("Please enter an address to search.")
            
    st.write("---")
    col_loc1, col_loc2 = st.columns([1, 2])
    
    # Pre-fill
    lat = data.get("lat")
    lon = data.get("lon")
    
    with col_loc1:
        st.write("**Auto Detect**")
        location = streamlit_geolocation()
        if location and location.get('latitude') and location.get('longitude'):
            lat = location['latitude']
            lon = location['longitude']
            st.session_state.report_data["lat"] = lat
            st.session_state.report_data["lon"] = lon
            st.success("✅ GPS Detected")
        
        st.markdown(f"**Latitude:** {lat or 'Not set'}")
        st.markdown(f"**Longitude:** {lon or 'Not set'}")
            
    with col_loc2:
        st.write("**Map Selection**")
        center_lat = lat if lat else 19.0760
        center_lon = lon if lon else 72.8777
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
        if lat and lon:
            folium.Marker([lat, lon], tooltip="Detected Location", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
        map_data = st_folium(m, width=500, height=300)
        
        if map_data and map_data.get("last_clicked"):
            st.session_state.report_data["lat"] = map_data["last_clicked"]["lat"]
            st.session_state.report_data["lon"] = map_data["last_clicked"]["lng"]
            st.rerun()

    st.write("")
    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("← Back"):
            prev_step()
    with col2:
        if st.button("Next →", type="primary"):
            if st.session_state.report_data["lat"] and st.session_state.report_data["lon"]:
                next_step()
            else:
                st.warning("Please detect or click on the map to set a location.")

# Step 4: User Information
elif st.session_state.step == 4:
    st.markdown("### Report Issue – Step 4")
    
    with st.form("step4_form"):
        name = st.text_input("Name", value=data.get("name", ""))
        phone = st.text_input("Phone Number", value=data.get("phone", ""))
        email = st.text_input("Optional Email", value=data.get("email", ""))
        
        col1, col2, _ = st.columns([1, 1, 5])
        with col1:
            back_clicked = st.form_submit_button("← Back")
        with col2:
            next_clicked = st.form_submit_button("Next →", type="primary")
            
        if back_clicked:
            st.session_state.report_data["name"] = name
            st.session_state.report_data["phone"] = phone
            st.session_state.report_data["email"] = email
            st.session_state.step -= 1
            st.rerun()
            
        if next_clicked:
            if not name.strip() or not phone.strip():
                st.warning("Please provide Name and Phone Number.")
            else:
                st.session_state.report_data["name"] = name
                st.session_state.report_data["phone"] = phone
                st.session_state.report_data["email"] = email
                st.session_state.step += 1
                st.rerun()

# Step 5: Upload Photo
elif st.session_state.step == 5:
    st.markdown("### Report Issue – Step 5")
    
    photo = st.file_uploader("Upload Issue Photo", type=["jpg","jpeg","png"])
    
    if photo:
        st.session_state.report_data["photo"] = photo
    
    if data.get("photo"):
        st.image(data["photo"], caption="Currently Uploaded Photo", use_container_width=True)
        
    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        if st.button("← Back"):
            prev_step()
    with col2:
        if st.button("Next →", type="primary"):
            next_step()

# Step 6: Review & Submit
elif st.session_state.step == 6:
    st.markdown("### Report Issue – Review")
    
    data = st.session_state.report_data
    
    st.markdown(f"**Description:** {data['parsed_description']}")
    st.markdown(f"**Category:** {data['parsed_category']}")
    st.markdown(f"**Location:** {data['lat']}, {data['lon']}")
    st.markdown(f"**Name:** {data['name']}")
    st.markdown(f"**Phone:** {data['phone']}")
    st.markdown(f"**Responsible Authority:** {data['authority']}")
    
    if data.get("photo"):
        st.image(data["photo"], caption="Issue Photo", use_container_width=True)
        
    is_emergency = st.toggle("🚨 Mark as an Emergency (Immediate Hazard)", value=data.get("emergency", False))
    st.session_state.report_data["emergency"] = is_emergency

    col1, col2, _ = st.columns([1, 3, 3])
    with col1:
        if st.button("← Back"):
            prev_step()
    with col2:
        if st.button("Submit Issue", type="primary", use_container_width=True):
            with st.spinner("Submitting issue..."):
                try:
                    # Submit Multipart form
                    files = []
                    if data.get("photo"):
                        p = data["photo"]
                        p.seek(0)
                        files.append(('photo', (p.name, p, p.type)))
                        
                    form_data = {
                        "description": data["parsed_description"],
                        "category": data["parsed_category"],
                        "latitude": str(data["lat"]),
                        "longitude": str(data["lon"]),
                        "reporter_name": data["name"],
                        "reporter_phone": data["phone"],
                        "emergency": "true" if data["emergency"] else "false"
                    }
                    
                    rep_res = requests.post(f"{API_URL}/api/report_issue", data=form_data, files=files if files else None, timeout=15)
                    if rep_res.status_code == 200:
                        st.session_state.sub_success = True
                        if rep_res.json().get("action") == "deduplicated":
                            st.session_state.sub_dedup = True
                    else:
                        st.error("Failed to submit issue.")
                except Exception as e:
                    st.error(f"Error submitting issue: {e}")
                    
    if st.session_state.get("sub_success"):
        if st.session_state.get("sub_dedup"):
            st.info("🔄 We found an identical issue already reported nearby! We've automatically added your upvote to it to boost its priority without creating a duplicate.")
        else:
            st.success("🎉 Issue Submitted Successfully.")
        st.markdown("### Auto Evidence Report")
        st.info("Evidence Report Ready")
        
        with st.spinner("Generating document..."):
            pdf_payload = {
                "name": data["name"],
                "phone": data["phone"],
                "description": data["parsed_description"],
                "category": data["parsed_category"],
                "location": f"Mumbai ({data['lat']}, {data['lon']})",
                "latitude": data["lat"],
                "longitude": data["lon"],
                "votes": 1,
                "authority": data["authority"]
            }
            pdf_res = requests.post(f"{API_URL}/api/generate_evidence_pdf", json=pdf_payload, timeout=20)
            if pdf_res.status_code == 200:
                st.download_button(
                    label="📥 Download Evidence Report PDF",
                    data=pdf_res.content,
                    file_name="civicsense_evidence_report.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
                if st.button("Start New Report"):
                    for key in st.session_state.keys():
                        del st.session_state[key]
                    st.rerun()
            else:
                st.error("Could not generate evidence PDF.")

render_footer()
