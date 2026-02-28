import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

from components.nav import render_nav, render_footer
from utils import apply_custom_css

apply_custom_css()
render_nav()

API_URL = "http://localhost:8000"

# Fetch Issue ID from query params
query_params = st.query_params
issue_id = query_params.get("id", None)

if not issue_id:
    st.error("No Issue ID provided. Please select an issue from the Issues Dashboard.")
    if st.button("⬅️ Back to Dashboard"): st.switch_page("pages/Issues_Feed.py")
    render_footer()
    st.stop()

# --- FETCH DATA ---
try:
    with st.spinner("Loading ticket details..."):
        res = requests.get(f"{API_URL}/api/issues/{issue_id}", timeout=5)
        if res.status_code == 200:
            issue = res.json()
        else:
            st.error("Ticket not found or has been removed.")
            st.stop()
            
    # Also fetch comments
    comm_res = requests.get(f"{API_URL}/api/issues/{issue_id}/comments", timeout=5)
    comments = comm_res.json() if comm_res.status_code == 200 else []
except Exception as e:
    st.error(f"Failed to fetch data: {str(e)}")
    st.stop()

# --- HEADER SECTION ---
status_color = "#f59e0b" if issue.get("status", "").lower() == "in progress" else ("#10b981" if issue.get("status", "").lower() == "resolved" else "#ef4444")
bg_color = status_color + "15" # 15% opacity hex

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px;">
    <div>
        <p style="margin: 0; color: #64748b; font-weight: 600; font-size: 0.9rem;">ISSUE #{issue['id']} • {issue.get('date', 'Recent')}</p>
        <h2 style="margin: 5px 0 0 0; color: #0f172a;">{issue['title']}</h2>
    </div>
    <div style="text-align: right;">
        <span style="background-color: {bg_color}; color: {status_color}; padding: 8px 16px; border-radius: 20px; font-weight: 600; border: 1px solid {status_color}40;">
            {issue.get('status', 'Pending')}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- BODY SECTION (jira style 2-col) ---
col_main, col_side = st.columns([2.5, 1])

with col_main:
    st.markdown("### 📝 Description")
    st.markdown(f"<div class='issues-card' style='background-color: #f8fafc; color: #334155; font-size: 1.05rem; line-height: 1.6;'>{issue['description']}</div>", unsafe_allow_html=True)
    
    if issue.get('image_url'):
        st.markdown("### 📸 Evidence Photo")
        st.image(issue['image_url'], use_container_width=True)
        st.write("")
        
    st.markdown("### 💬 Activity & Comments")
    
    # Render comments timeline
    for c in comments:
        name = c.get('name', 'Anonymous')
        text = c.get('text', '')
        date = c.get('date', 'Unknown')
        
        icon = "🤖" if name == "System" else "👤"
        st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
            <div style="font-size: 1.5rem; background: #e2e8f0; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">{icon}</div>
            <div style="flex: 1; background: #ffffff; border: 1px solid #e2e8f0; padding: 12px 15px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <strong>{name}</strong>
                    <span style="color: #94a3b8; font-size: 0.8rem;">{date}</span>
                </div>
                <div style="color: #475569;">{text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # Add comment box
    with st.expander("➕ Add a Comment", expanded=False):
        c_name = st.text_input("Name", placeholder="Your Name")
        c_text = st.text_area("Comment", placeholder="Add an update or context here...")
        if st.button("Post Comment"):
            if c_name and c_text:
                post_res = requests.post(f"{API_URL}/api/issues/{issue_id}/comments", json={"name": c_name, "text": c_text})
                if post_res.status_code == 200:
                    st.success("Comment added!")
                    st.rerun()
            else:
                st.warning("Provide both Name and Comment.")

with col_side:
    st.markdown("### 📊 Details")
    st.markdown(f"""
    <div class='issues-card' style='margin-bottom: 20px;'>
        <p style='margin:0 0 5px 0; font-size:0.85rem; color:#64748b; font-weight:bold;'>CATEGORY</p>
        <p style='margin:0 0 15px 0; color:#0f172a; font-weight:500;'>{issue['category']}</p>
        
        <p style='margin:0 0 5px 0; font-size:0.85rem; color:#64748b; font-weight:bold;'>LOCATION (WARD)</p>
        <p style='margin:0 0 15px 0; color:#0f172a; font-weight:500;'>{issue.get('ward', 'General')}</p>
        
        <p style='margin:0 0 5px 0; font-size:0.85rem; color:#64748b; font-weight:bold;'>COMMUNITY SUPPORT</p>
        <div style="display: flex; align-items: center; gap: 10px; margin:0 0 15px 0;">
            <span style='font-size:1.2rem; font-weight:bold; color:#0f172a;'>{issue.get('votes', 0)}</span>
            <span style='color:#64748b;'>Upvotes</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upvote Button
    if st.button("👍 Add My Upvote", use_container_width=True, type="primary"):
        try:
            vote_res = requests.post(f"{API_URL}/api/vote/{issue_id}", timeout=5)
            if vote_res.status_code == 200:
                st.success("Vote recorded successfully!")
                st.rerun()
        except:
            st.error("Failed to vote.")
            
    st.divider()
    
    # Mini Map
    st.markdown("### 🗺️ Location")
    lat, lon = issue.get('latitude'), issue.get('longitude')
    if lat and lon:
        m = folium.Map(location=[lat, lon], zoom_start=15, control_scale=True)
        color = "red" if issue.get("severity", "").lower() in ["high", "critical"] else "blue"
        folium.Marker([lat, lon], tooltip=issue['title'], icon=folium.Icon(color=color)).add_to(m)
        st_folium(m, width=300, height=250)
    else:
        st.info("No exact GPS coordinates provided.")

render_footer()
