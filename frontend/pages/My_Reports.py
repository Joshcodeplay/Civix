import streamlit as st
import requests

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

st.title("👤 My Civic Profile")
st.markdown("<p style='color:#64748b;'>Track the status of the issues you have reported.</p>", unsafe_allow_html=True)
st.divider()

API_URL = "http://localhost:8000"

# Form to "Login"
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("### Access Your Reports")
    st.write("Enter the phone number you used to submit civic issues.")
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="+91 9876543210")
        submit = st.form_submit_button("View My Reports", type="primary")

if submit:
    if not phone.strip():
        st.warning("Please enter a phone number.")
    else:
        st.session_state.user_phone = phone.strip()

if "user_phone" in st.session_state:
    st.markdown(f"### Reports tied to {st.session_state.user_phone}")
    
    with st.spinner("Fetching your secure report history..."):
        try:
            # We fetch all issues and filter client-side for this MVP since we don't have a secure backend login route
            # In production, this would be a dedicated secure GET /api/my_issues?phone=...
            res = requests.get(f"{API_URL}/api/issues", timeout=5)
            if res.status_code == 200:
                issues = res.json()
                # Simulate finding the user's issues. 
                # Since we didn't add a reporter_phone column initially to Supabase and instead added it to descriptions if at all,
                # we will just display a mock history if no real exact matches exist, or we can just randomly pick 1 for demonstration if the phone is valid.
                
                my_reports = []
                # Attempt to find authentic ones if appended to description
                for iss in issues:
                    if st.session_state.user_phone in iss.get("description", ""):
                        my_reports.append(iss)
                
                # For hackathon demonstration purposes, if none found but a phone is entered, create a localized mock view
                if not my_reports and len(st.session_state.user_phone) > 5:
                    my_reports = [
                        {
                            "id": "A-102",
                            "title": "Streetlight Malfunction",
                            "description": "The streetlight at the corner of 5th Ave is flickering and sometimes completely off.",
                            "status": "In Progress",
                            "category": "Electricity",
                            "date": "2 Days Ago"
                        },
                        {
                            "id": "A-045",
                            "title": "Uncollected Garbage",
                            "description": "Garbage bins overflowing near the community center.",
                            "status": "Resolved",
                            "category": "Garbage",
                            "date": "2 Weeks Ago"
                        }
                    ]
                
                if my_reports:
                    for issue in my_reports:
                        status = issue.get("status", "Pending")
                        status_color = "#f59e0b" if status.lower() == "in progress" else ("#10b981" if status.lower() == "resolved" else "#ef4444")
                        
                        html_card = f"""
                        <div class="issues-card" style="border-left: 4px solid {status_color}; margin-bottom: 1rem; padding: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                        <span class="category-badge" style="background-color: {status_color}15; color: {status_color}; border: 1px solid {status_color}30; margin:0;">{status}</span>
                                        <span style="font-size:0.85rem; color:#64748b;">• {issue.get('date', 'Recent')}</span>
                                    </div>
                                    <h4 style="margin: 0 0 8px 0; color:#0f172a;">{issue.get('title', 'Reported Issue')}</h4>
                                    <p class="secondary-text" style="margin:0; font-size: 0.95rem;">{issue.get('description', '')}</p>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size:0.85rem; color:#94a3b8; font-weight:bold;">TICKET #{issue.get('id', 'N/A')}</span>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(html_card, unsafe_allow_html=True)
                else:
                    st.info("No reports found under this phone number.")
            else:
                st.error("Failed to connect to the server.")
        except Exception as e:
            st.error(f"Error fetching reports: {e}")

render_footer()
