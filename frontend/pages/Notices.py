import streamlit as st
import requests

from utils import apply_custom_css

apply_custom_css()

st.title("🏛️ Government Notices")
st.write("Stay updated with official announcements and notices.")
st.divider()

API_URL = "http://localhost:8000"

def fetch_notices():
    try:
        response = requests.get(f"{API_URL}/notices", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching notices: {e}")
    return []

notices = fetch_notices()

if not notices:
    st.info("No recent government notices found.")
else:
    for notice in notices:
        title = notice.get("title", "Untitled Notice")
        summary = notice.get("summary", "No summary provided.")
        source = notice.get("source", "Official Government")
        date = notice.get("date", "Recent")
        
        html_card = f"""
        <div class="issues-card">
            <h3 style="margin-top: 0; margin-bottom: 0.5rem; color: #1f2937;">{title}</h3>
            <div style="display: flex; gap: 10px; margin-bottom: 1rem; font-size: 0.85rem; color: #6b7280;">
                <span><strong>Source:</strong> {source}</span>
                <span>•</span>
                <span><strong>Date:</strong> {date}</span>
            </div>
            <p style="color: #4b5563; line-height: 1.5; margin-bottom: 0;">{summary}</p>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
