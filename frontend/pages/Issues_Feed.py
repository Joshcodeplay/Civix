import streamlit as st
import requests

from utils import apply_custom_css

apply_custom_css()

st.title("📋 Issues Feed")
st.write("Browse and support community issues.")
st.divider()

API_URL = "http://localhost:8000"

def fetch_issues():
    try:
        response = requests.get(f"{API_URL}/api/issues", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching issues: {e}")
    return []

def vote_issue(issue_id):
    try:
        response = requests.post(f"{API_URL}/api/vote/{issue_id}", timeout=5)
        if response.status_code == 200:
            st.success("Vote recorded successfully!")
            st.rerun()
        else:
            st.error("Failed to record vote.")
    except Exception as e:
        st.error(f"Error voting: {e}")

issues = fetch_issues()

if not issues:
    st.info("No issues found. Be the first to report one!")
else:
    for issue in issues:
        issue_id = issue.get("id")
        desc = issue.get("description", "No description")
        cat = issue.get("category", "General")
        votes = issue.get("votes", 0)
        em_badge = '<span class="emergency-badge">🚨 EMERGENCY</span>\n' if issue.get("emergency") else ""
        
        html_card = (
"<div class=\"issues-card\">\n"
f"{em_badge}"
f"<span class=\"category-badge\">{cat}</span>\n"
f"<h4 style=\"margin-top: 0.5rem;\">{desc}</h4>\n"
f"<p class=\"secondary-text\">Votes: <strong>{votes}</strong></p>\n"
"</div>"
        )
        st.markdown(html_card, unsafe_allow_html=True)
        
        if st.button("👍 Upvote", key=f"vote_{issue_id}", type="secondary"):
                    vote_issue(issue_id)
