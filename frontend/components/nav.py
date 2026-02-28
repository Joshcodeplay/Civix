import streamlit as st
import requests

API_URL = "http://localhost:8000"

# --- SOS EMERGENCY SYSTEM ---
@st.dialog("🚨 Report SOS Emergency")
def sos_dialog():
    st.markdown("<p style='color:#ef4444; font-weight:bold;'>WARNING: This will immediately alert all nearby users.</p>", unsafe_allow_html=True)
    sos_desc = st.text_input("What is the emergency?", placeholder="e.g. Fire in building, Severe accident...")
    if st.button("Send SOS Alert", type="primary", use_container_width=True):
        if not sos_desc:
            st.error("Please provide details of the emergency.")
            return
            
        user_lat = st.session_state.get("user_lat")
        user_lon = st.session_state.get("user_lon")
        
        if not user_lat or not user_lon:
            st.error("Location not available. Please allow location access first.")
            return
            
        try:
            res = requests.post(
                f"{API_URL}/api/sos", 
                json={"description": sos_desc, "latitude": user_lat, "longitude": user_lon},
                timeout=5
            )
            if res.status_code == 200:
                st.session_state["sos_sent"] = True
                st.rerun()
            else:
                st.error("Failed to send SOS. Please call local authorities manually.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
def render_nav():
    st.markdown("""
    <style>
        /* Hide sidebar toggle completely */
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
        /* Cleaner top header */
        header { display: none !important; }
        [data-testid="stHeader"] { display: none !important; }
        /* Hide footer */
        footer { display: none !important; }
        /* Move content up */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            margin-top: -1.5rem !important;
            margin-bottom: -2rem !important;
        }
        /* Custom red SOS button */
        .sos-btn button {
            background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            font-size: 1.05rem !important;
            padding: 8px 20px !important;
            box-shadow: 0px 4px 10px rgba(239, 68, 68, 0.4) !important;
            letter-spacing: 0.5px !important;
        }
        .sos-btn button:hover {
            transform: translateY(-2px);
            box-shadow: 0px 6px 15px rgba(239, 68, 68, 0.6) !important;
        }
        
        /* Style the page links to look better in the navbar */
        a[data-testid="stPageLink-NavLink"] {
            text-decoration: none !important;
            font-weight: 600 !important;
            font-size: 1.05rem !important;
            padding: 8px 8px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease-in-out !important;
            font-family: 'Poppins', sans-serif !important;
        }
        a[data-testid="stPageLink-NavLink"]:hover {
            background-color: rgba(37, 99, 235, 0.1) !important;
            transform: translateY(-1px) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display SOS confirmation or banner
    if st.session_state.get("sos_sent"):
        st.success("🚨 SOS alert successfully broadcasted to nearby users!")
        if st.button("Dismiss Alert", key="dismiss_sos_alert"):
            st.session_state["sos_sent"] = False
            st.rerun()

    user_lat = st.session_state.get("user_lat")
    user_lon = st.session_state.get("user_lon")
    
    # --- ACTIVE SOS ALERTS CHCECK ---
    if user_lat and user_lon:
        try:
            sos_res = requests.get(f"{API_URL}/api/active-sos?lat={user_lat}&lon={user_lon}&radius=5", timeout=3)
            if sos_res.status_code == 200:
                active_alerts = sos_res.json().get("alerts", [])
                
                if "notified_alerts" not in st.session_state:
                    st.session_state["notified_alerts"] = set()
                    
                import streamlit.components.v1 as components
                
                for alert in active_alerts:
                    alert_key = f"sos_{alert['id']}"
                    
                    st.error(f"**🚨 EMERGENCY NEARBY ({alert['distance_km']} km away):** {alert['description']} - Reported at {alert['time']}", icon="🚨")
                    
                    # If this is a new alert, trigger notifications
                    if alert_key not in st.session_state["notified_alerts"]:
                        st.toast(f"🚨 NEW EMERGENCY: {alert['description']}", icon="🚨")
                        
                        # Trigger native browser notification
                        js_code = f"""
                        <script>
                            if ("Notification" in window) {{
                                if (Notification.permission === "granted") {{
                                    new Notification("🚨 CivicSense Emergency!", {{
                                        body: "{alert['description']} ({alert['distance_km']} km away. Please stay safe!)"
                                    }});
                                }} else if (Notification.permission !== "denied") {{
                                    Notification.requestPermission().then(function (permission) {{
                                        if (permission === "granted") {{
                                            new Notification("🚨 CivicSense Emergency!", {{
                                                body: "{alert['description']} ({alert['distance_km']} km away. Please stay safe!)"
                                            }});
                                        }}
                                    }});
                                }}
                            }}
                        </script>
                        """
                        components.html(js_code, height=0, width=0)
                        st.session_state["notified_alerts"].add(alert_key)
                        
        except:
            pass # Silently fail SOS check if backend is down so it doesn't break the page
    
    col_logo, col_space, col1, col2, col3, col4, col5, col6, col_sos = st.columns([2.5, 0.1, 1, 1, 1, 1, 1, 1, 1.4])
    
    with col_logo:
        st.markdown("""
        <div style='display: flex; flex-direction: column; justify-content: center; height: 100%; margin-top: -5px;'>
            <h3 style='margin: 0; padding: 0; color: #2563EB !important; font-family: \"Bebas Neue\", sans-serif; letter-spacing: 1px;'>🏙️ CivicSense</h3>
            <p style='margin: 0; font-size: 0.8rem; color: #94a3b8 !important; line-height: 1;'>AI-Powered Civic Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col1:
        st.page_link("pages/Home.py", label="Home")
    with col2:
        st.page_link("pages/Report_Issue.py", label="Report")
    with col3:
        st.page_link("pages/Issues_Feed.py", label="Issues")
    with col4:
        st.page_link("pages/Map_View.py", label="Map")
    with col5:
        st.page_link("pages/Notices.py", label="Notices")
    with col6:
        st.page_link("pages/My_Reports.py", label="Profile")
    with col_sos:
        st.markdown("""
        <style>
        /* Hide the default button margin to align it with page_links */
        div.stButton {
            margin-top: -10px !important;
        }
        </style>
        <div class='sos-btn'>
        """, unsafe_allow_html=True)
        if st.button("🚨 S.O.S", key="nav_sos_btn", use_container_width=True):
            if not user_lat or not user_lon:
                st.error("Please enable location on Home page first.")
            else:
                sos_dialog()
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.divider()

def render_footer():
    # Footer removed as requested
    pass
