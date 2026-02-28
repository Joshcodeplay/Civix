import streamlit as st
import requests
from streamlit_folium import st_folium
import folium
from streamlit_geolocation import streamlit_geolocation

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

st.title("📝 Report an Issue")
st.markdown("<p style='color:#64748b; font-size:1.1rem;'>Help us improve the city by reporting civic issues through our AI-assisted reporting wizard.</p>", unsafe_allow_html=True)

API_URL = "http://localhost:8000"

# Session state to store parsing results
if "parsed_category" not in st.session_state:
    st.session_state.parsed_category = None
if "parsed_description" not in st.session_state:
    st.session_state.parsed_description = None

# We use tabs to simulate a horizontal stepper flow
tab1, tab2, tab3, tab4 = st.tabs(["Step 1: Description", "Step 2: AI Analysis", "Step 3: Location", "Step 4: Submit"])

with tab1:
    st.markdown("### Reporter Details")
    col1, col2 = st.columns(2)
    with col1:
        reporter_name = st.text_input("Full Name", placeholder="Rahul Sharma")
    with col2:
        reporter_phone = st.text_input("Phone Number", placeholder="+91 9876543210")
    
    st.markdown("### Issue Description")
    user_input = st.text_area("Describe the Issue in your own words", placeholder="e.g. Garbage not collected near the local station for 3 days.", height=150)
    st.info("💡 Tip: Be as descriptive as possible. Our AI will automatically categorize and extract the core details in the next step!")

with tab2:
    st.markdown("### AI Analysis")
    st.write("Let our AI agent extract the official civic category and clean description from your report.")
    
    if st.button("🧠 Analyze Issue", type="primary"):
        if user_input.strip():
            try:
                with st.spinner("Analyzing text with Gemini AI..."):
                    response = requests.post(f"{API_URL}/api/parse_issue", json={"text": user_input}, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.parsed_category = data.get("category", "Unknown")
                        st.session_state.parsed_description = data.get("description", user_input)
                    else:
                        st.error("Failed to parse issue.")
            except Exception as e:
                st.error(f"API Error: {e}")
        else:
            st.warning("Please enter a description in Step 1 first.")

    if st.session_state.parsed_category:
        st.markdown(f"""
        <div class='issues-card' style='border-left: 4px solid #3b82f6;'>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Detected Category</p>
            <h4 style='margin:0 0 15px 0; color:#1e293b;'>{st.session_state.parsed_category}</h4>
            <p style='margin:0 0 5px 0; font-size:0.9rem; color:#64748b; text-transform:uppercase;'>Clean Description</p>
            <p style='margin:0; color:#334155;'>{st.session_state.parsed_description}</p>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### Pinpoint Location")
    st.write("We need exact coordinates to route your issue correctly.")
    
    col_loc1, col_loc2 = st.columns([1, 2])
    with col_loc1:
        st.write("**Auto Detect**")
        location = streamlit_geolocation()
        lat, lon = None, None
        if location and location.get('latitude') and location.get('longitude'):
            lat = location['latitude']
            lon = location['longitude']
            st.success("✅ GPS Detected")
        else:
            st.info("Click the button to fetch GPS.")
            
    with col_loc2:
        st.write("**Manual Override (Map)**")
        center_lat = lat if lat else 19.0760
        center_lon = lon if lon else 72.8777

        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
        if lat and lon:
            folium.Marker([lat, lon], tooltip="Detected Location", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)

        map_data = st_folium(m, width=500, height=300)

        if map_data and map_data.get("last_clicked"):
            lat = map_data["last_clicked"]["lat"]
            lon = map_data["last_clicked"]["lng"]
            st.success("✅ Map Pin Dropped")

with tab4:
    st.markdown("### Finalize and Submit")
    
    is_emergency = st.toggle("🚨 Mark as an Emergency (Immediate Hazard)")
    
    # Portal mapping
    PORTAL_MAP = {
        "Garbage": ("BMC Solid Waste Management", "https://portal.mcgm.gov.in/"),
        "Road Damage": ("BMC Roads & Traffic", "https://portal.mcgm.gov.in/"),
        "Water": ("BMC Hydraulic Engineer", "https://portal.mcgm.gov.in/"),
        "Electricity": ("BEST Undertaking", "https://www.bestundertaking.com/"),
    }

    if st.button("📤 Submit Official Report", type="primary", use_container_width=True):
        if not reporter_name or not reporter_phone:
            st.error("Please provide your Name and Phone Number in Step 1.")
        elif not st.session_state.parsed_category:
            st.error("Please analyze the issue in Step 2.")
        elif not lat or not lon:
            st.error("Please provide a location in Step 3.")
        else:
            desc_to_use = st.session_state.parsed_description or user_input
            cat_to_use = st.session_state.parsed_category
            
            dedupe_payload = {
                "description": desc_to_use,
                "latitude": lat,
                "longitude": lon
            }
            
            try:
                with st.spinner("Checking for similar issues to prevent duplicates..."):
                    dupe_res = requests.post(f"{API_URL}/api/check_duplicate", json=dedupe_payload, timeout=10)
                    
                    if dupe_res.status_code == 200:
                        dupe_data = dupe_res.json()
                        if dupe_data.get("duplicate"):
                            st.info("⚠️ Similar Issue Found")
                            issue_id = dupe_data.get('issue_id')
                            html_card = f"""
                            <div class="issues-card" style="border-left: 4px solid #f59e0b;">
                                <h4 style="margin-top: 0.5rem; color:#b45309;">{dupe_data.get('description')}</h4>
                                <p class="secondary-text">Votes: <strong>{dupe_data.get('votes')}</strong></p>
                                <p class="secondary-text" style="color:#ef4444; font-size:0.8rem;">Distance: ~{dupe_data.get('distance')}m away</p>
                            </div>
                            """
                            st.markdown(html_card, unsafe_allow_html=True)
                            st.warning("This issue has already been reported! Your report has automatically been converted into an upvote to escalate priority.")
                            
                            vote_res = requests.post(f"{API_URL}/api/vote/{issue_id}", timeout=5)
                            if vote_res.status_code == 200:
                                st.success("✅ Vote Added Successfully.")
                            else:
                                st.error("Failed to add vote to existing issue.")
                                
                            render_footer()
                            st.stop()
                            
                with st.spinner("Registering new civic complaint..."):
                    submit_payload = {
                        "description": desc_to_use,
                        "category": cat_to_use,
                        "latitude": lat,
                        "longitude": lon,
                        "emergency": is_emergency,
                        "reporter_name": reporter_name,
                        "reporter_phone": reporter_phone
                    }
                    submit_res = requests.post(f"{API_URL}/api/submit-issue", json=submit_payload, timeout=10)
                    
                    if submit_res.status_code == 200:
                        st.success("🎉 Issue submitted successfully!")
                        
                        with st.spinner("Generating official complaint letter PDF..."):
                            pdf_payload = {
                                "name": reporter_name,
                                "phone": reporter_phone,
                                "description": desc_to_use,
                                "category": cat_to_use,
                                "location": f"Lat: {lat}, Lon: {lon}"
                            }
                            pdf_res = requests.post(f"{API_URL}/api/generate_pdf", json=pdf_payload, timeout=15)
                            
                            if pdf_res.status_code == 200:
                                st.markdown("### 📄 Complaint Letter Ready")
                                html_card_pdf = """
                                <div class="issues-card" style="border-left: 4px solid #10b981;">
                                    <h4 style="margin-top:0;">Download Official Report</h4>
                                    <p class="secondary-text">A formatted PDF complaint letter has been generated with your details.</p>
                                </div>
                                """
                                st.markdown(html_card_pdf, unsafe_allow_html=True)
                                st.download_button(
                                    label="📥 Download Complaint Letter PDF",
                                    data=pdf_res.content,
                                    file_name="civicsense_complaint.pdf",
                                    mime="application/pdf",
                                    type="primary"
                                )
                            else:
                                st.error("Issue submitted, but failed to generate the PDF.")
                                
                        st.divider()
                        st.markdown("### 🏛️ Official Portal Guidance")
                        portal_info = PORTAL_MAP.get(cat_to_use)
                        if not portal_info:
                            if "pothole" in cat_to_use.lower() or "road" in cat_to_use.lower():
                                portal_info = PORTAL_MAP.get("Road Damage")
                            elif "garbage" in cat_to_use.lower() or "waste" in cat_to_use.lower():
                                portal_info = PORTAL_MAP.get("Garbage")
                            elif "water" in cat_to_use.lower() or "leak" in cat_to_use.lower():
                                portal_info = PORTAL_MAP.get("Water")
                            else:
                                portal_info = ("Municipal Corporation Contact Center", "https://portal.mcgm.gov.in/")
                        
                        st.markdown(f"""
                        <div class="issues-card" style="background-color:#eff6ff; border: 1px solid #bfdbfe;">
                            <span class="category-badge" style="background-color:#dbeafe; color:#1d4ed8; border:none;">Guidance</span>
                            <h4 style="margin-top: 0.5rem; color:#1e40af;">{portal_info[0]}</h4>
                            <p class="secondary-text" style="color:#475569;">Based on your category, this is the official department handling this request. You can optionally cross-file it directly with their civic portal.</p>
                            <a href="{portal_info[1]}" target="_blank" style="text-decoration:none;">
                                <button class="stButton" style="padding: 0.4rem 0.8rem; border-radius: 6px; border: 1px solid #93c5fd; background-color: white; color: #1e40af; font-weight: 500; cursor: pointer;">🔗 Visit Official Portal</button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Reset state
                        st.session_state.parsed_category = None
                        st.session_state.parsed_description = None
                    else:
                        st.error("Failed to submit issue.")
            except Exception as e:
                st.error(f"API Error: {e}")

render_footer()
