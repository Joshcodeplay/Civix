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
        response = requests.get(f"{API_URL}/api/notices", timeout=5)
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
        
        html_card = (
"<div class=\"issues-card\">\n"
f"<h3 style=\"margin-top: 0; margin-bottom: 0.5rem; color: #1f2937;\">{title}</h3>\n"
"<div style=\"display: flex; gap: 10px; margin-bottom: 1rem; font-size: 0.85rem; color: #6b7280;\">\n"
f"<span><strong>Source:</strong> {source}</span>\n"
"<span>•</span>\n"
f"<span><strong>Date:</strong> {date}</span>\n"
"</div>\n"
f"<p style=\"color: #4b5563; line-height: 1.5; margin-bottom: 0;\">{summary}</p>\n"
"</div>"
        )
        st.markdown(html_card, unsafe_allow_html=True)
