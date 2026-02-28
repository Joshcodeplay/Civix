import streamlit as st
import requests

from utils import apply_custom_css

apply_custom_css()

st.title("🏙️ CivicSense")
st.markdown("<h3 class='secondary-text'>AI-powered Civic Intelligence Platform</h3>", unsafe_allow_html=True)
st.divider()

st.header("Recent Issues")

API_URL = "http://localhost:8000"

try:
    response = requests.get(f"{API_URL}/api/issues", timeout=5)
    if response.status_code == 200:
        issues = response.json()
        if not issues:
            st.info("No recent issues found.")
        else:
            for issue in issues:
                html_card = (
"<div class=\"issues-card\">\n"
f"{'<span class=\"emergency-badge\">🚨 EMERGENCY</span>' if issue.get('emergency') else ''}\n"
f"<span class=\"category-badge\">{issue.get('category', 'General')}</span>\n"
f"<h4 style=\"margin-top: 0.5rem;\">{issue.get('description', 'No description')}</h4>\n"
f"<p class=\"secondary-text\">Votes: <strong>{issue.get('votes', 0)}</strong></p>\n"
"</div>"
                )
                st.markdown(html_card, unsafe_allow_html=True)
    else:
        st.error(f"Failed to fetch issues. Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    st.error(f"Could not connect to the backend API: {e}. Ensure the FastAPI server is running.")
