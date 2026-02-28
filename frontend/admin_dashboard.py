import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import altair as alt
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Vox Command Center", layout="wide", page_icon="�️", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Global container padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Styled Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px 20px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {
        color: #0f172a !important;
    }
    /* Dynamic colors for specific metrics based on position */
    div[data-testid="stMetric"]:nth-child(2) { border-left-color: #f59e0b; }
    div[data-testid="stMetric"]:nth-child(3) { border-left-color: #10b981; }
    div[data-testid="stMetric"]:nth-child(4) { border-left-color: #ef4444; }
    
    /* Typography */
    h1, h2, h3 { 
        font-family: 'Inter', sans-serif; 
        color: #0f172a;
    }
    .section-header {
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Vox Civic Control Center")
st.markdown("Real-time government analytics and grievance management platform.")

# --- DATA FETCHING ---
@st.cache_data(ttl=5)
def fetch_data():
    try:
        res = requests.get(f"{API_URL}/api/admin/stats", timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

data = fetch_data()

if not data or not data.get("all_complaints"):
    st.info("Waiting for data from the backend... Ensure FastAPI is running.")
    st.stop()

# Load into dataframe
df = pd.DataFrame(data["all_complaints"])

# Data cleaning/fill
df['ward'] = df['ward'].fillna('Unknown')
df['status'] = df['status'].fillna('Pending')
df['severity'] = df['severity'].fillna('Low')

# --- SIDEBAR FILTERS ---
st.sidebar.markdown("## Control Panel")
st.sidebar.markdown("Filter system data globally.")

categories = ["All"] + list(df['issue_type'].dropna().unique())
selected_cat = st.sidebar.selectbox("Issue Category", categories)

statuses = ["All", "Pending", "In Progress", "Resolved", "Closed"]
selected_status = st.sidebar.selectbox("Status", statuses)

wards = ["All"] + list(df['ward'].unique())
selected_ward = st.sidebar.selectbox("Ward", wards)

st.sidebar.divider()
if st.sidebar.button("Force Refresh Data", use_container_width=True, icon=":material/refresh:"):
    st.cache_data.clear()
    st.rerun()

# Apply filters
filtered_df = df.copy()
if selected_cat != "All":
    filtered_df = filtered_df[filtered_df['issue_type'] == selected_cat]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'].str.lower() == selected_status.lower()]
if selected_ward != "All":
    filtered_df = filtered_df[filtered_df['ward'] == selected_ward]

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reported", str(len(filtered_df)))
active_count = len(filtered_df[~filtered_df['status'].str.lower().isin(["resolved", "closed"])])
col2.metric("Active Cases", str(active_count))
resolved_count = len(filtered_df[filtered_df['status'].str.lower() == "resolved"])
col3.metric("Resolved", str(resolved_count))
critical_count = len(filtered_df[(filtered_df['severity'].str.lower() == "critical") & (~filtered_df['status'].str.lower().isin(["resolved", "closed"]))])
col4.metric("Critical Hazards", str(critical_count))

st.markdown("<h3 class='section-header'>Geographic Intelligence</h3>", unsafe_allow_html=True)

# --- MAP VISUALIZATION ---
map_col, chart_col = st.columns([1.5, 1])

with map_col:
    # PyDeck Map
    map_df = filtered_df.dropna(subset=['latitude', 'longitude']).copy()
    if not map_df.empty:
        map_df['lat'] = map_df['latitude'].astype(float)
        map_df['lon'] = map_df['longitude'].astype(float)
        
        # Color coding based on severity
        def get_color(sev):
            s = str(sev).lower()
            if s == "critical": return [239, 68, 68, 200]    # Red
            elif s == "high": return [245, 158, 11, 200]      # Orange
            elif s == "medium": return [59, 130, 246, 200]    # Blue
            return [16, 185, 129, 200]                        # Green
            
        map_df['color'] = map_df['severity'].apply(get_color)
        
        view_state = pdk.ViewState(
            latitude=map_df['lat'].mean() if not map_df.empty else 19.0760,
            longitude=map_df['lon'].mean() if not map_df.empty else 72.8777,
            zoom=11,
            pitch=45
        )
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=150,
            pickable=True,
            auto_highlight=True
        )
        
        st.pydeck_chart(pdk.Deck(
            map_style='light',
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"text": "{issue_type}\nWard: {ward}\nSeverity: {severity}\nVotes: {upvote_count}"}
        ))
    else:
        st.info("No spatial data available for the current filter.")

with chart_col:
    # Category Distribution Chart
    if not filtered_df.empty:
        cat_counts = filtered_df['issue_type'].value_counts().reset_index()
        cat_counts.columns = ['Category', 'Count']
        
        # Group categories with less than 15% of total into "Others"
        total_count = cat_counts['Count'].sum()
        cat_counts.loc[cat_counts['Count'] / total_count < 0.15, 'Category'] = 'Others'
        cat_counts = cat_counts.groupby('Category', as_index=False).sum()
        
        chart = alt.Chart(cat_counts).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", legend=alt.Legend(title="Type", orient="bottom")),
            tooltip=['Category', 'Count']
        ).properties(title="Volume by Category", height=320)
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("No data for charts")


st.markdown("<h3 class='section-header'>Active Master Grid & Action Desk</h3>", unsafe_allow_html=True)

table_col, action_col = st.columns([2, 1])

# --- MASTER TABLE ---
with table_col:
    st.markdown("#### Complaint Database")
    if not filtered_df.empty:
        display_df = filtered_df[['id', 'issue_type', 'ward', 'severity', 'upvote_count', 'status', 'created_at']].copy()
        
        # Format datetime
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df.sort_values(by="upvote_count", ascending=False, inplace=True)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("Track ID", format="%d"),
                "issue_type": "Category",
                "ward": "Ward",
                "severity": "Severity",
                "upvote_count": st.column_config.NumberColumn("Priority (Votes)", format="%d"),
                "status": "Status",
                "created_at": "Reported On"
            }
        )
    else:
        st.info("Table is empty based on current filters.")

# --- ACTION DESK ---
with action_col:
    st.markdown("#### Issue Control Desk")
    st.write("Select a Track ID to escalate or resolve.")
    
    if not filtered_df.empty:
        issue_ids = filtered_df['id'].tolist()
        selected_id = st.selectbox("Select Track ID", [None] + issue_ids)
        
        if selected_id:
            issue_record = filtered_df[filtered_df['id'] == selected_id].iloc[0]
            
            with st.container(border=True):
                st.markdown(f"**Description:** {issue_record.get('description', 'No description provided')}")
                
                reporter_text = issue_record.get('reporter_name')
                phone_text = issue_record.get('reporter_phone')
                st.markdown(f"**Reporter Entry:** {reporter_text if pd.notna(reporter_text) else 'Anonymous'} | {phone_text if pd.notna(phone_text) else 'No Contact'}")
                
                # Show image if exists
                img_url = issue_record.get('image_url')
                if img_url and pd.notna(img_url) and str(img_url).startswith("http"):
                    st.image(str(img_url), caption="Field Evidence", use_container_width=True)
                
                st.divider()
                
                current_status = str(issue_record['status']).title()
                valid_options = ["Pending", "In Progress", "Resolved", "Closed"]
                try:
                    default_idx = valid_options.index(current_status)
                except ValueError:
                    default_idx = 0
                    
                new_status = st.selectbox("Deploy Status Update", valid_options, index=default_idx)
                
                if st.button("Commit System Update", type="primary", use_container_width=True):
                    try:
                        patch_res = requests.patch(
                            f"{API_URL}/api/admin/update-status/{selected_id}", 
                            json={"status": new_status},
                            timeout=5
                        )
                        if patch_res.status_code == 200:
                            st.success(f"Track ID #{selected_id} status escalated to {new_status}!", icon=":material/check_circle:")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error updating database: {patch_res.text}")
                    except Exception as e:
                        st.error(f"Network Error: {e}")
    else:
        st.info("Select filters to load issues.")
