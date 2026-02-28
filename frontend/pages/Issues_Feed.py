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
        
        with st.container(border=True):
            if issue.get("emergency"):
                st.markdown('<span class="emergency-badge">🚨 EMERGENCY</span>', unsafe_allow_html=True)
            
            st.markdown(f'<span class="category-badge">{issue.get("category", "General")}</span>', unsafe_allow_html=True)
            st.markdown(f'<h4 style="margin-top: 0.5rem; margin-bottom: 0.5rem;">{issue.get("description", "No description")}</h4>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f'<p style="margin-top:0.5rem;" class="secondary-text">Votes: <strong>{issue.get("votes", 0)}</strong></p>', unsafe_allow_html=True)
            with col2:
                if st.button("👍 Upvote", key=f"vote_{issue_id}", type="secondary"):
                    vote_issue(issue_id)
