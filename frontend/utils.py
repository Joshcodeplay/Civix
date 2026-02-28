import streamlit as st

def apply_custom_css(home=True):

    st.markdown(f"""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');


    /* ================= BACKGROUND ================= */

    .stApp {{

        background-color: {"#0B0F14" if home else "#F8FAFC"};

    }}



    /* ================= FONTS ================= */

    .stApp, p, label, li {{

        font-family: 'Montserrat', sans-serif !important;

        color: {"#E2E8F0" if home else "#1E293B"} !important;

    }}

    /* Prevent overriding Streamlit built-in icons */
    .material-symbols-rounded, .stIcon, span[data-baseweb="icon"] {{
        font-family: 'Material Symbols Rounded' !important;
    }}


    h1, h2, h3, h4, h5, h6 {{

        font-family: 'Bebas Neue', sans-serif !important;

        letter-spacing:2px;

        text-transform:uppercase;

        color: {"white" if home else "#0F172A"} !important;
    }}


    h1 {{

        font-size:3rem !important;
    }}

    h2 {{

        font-size:2.2rem !important;
    }}

    h3 {{

        font-size:1.6rem !important;
    }}



    /* ================= CONTENT PANEL ================= */

    section.main > div {{

        background:
        {"#12161A" if home else "#FFFFFF"};

        border: {"1px solid #1E293B" if home else "1px solid #E2E8F0"};

        border-radius:12px;

        padding:2rem;

        margin-top:10px;

    }}



    /* ================= HERO TEXT ================= */

    .hero-title {{

        font-size:4.5rem;

        text-align:center;

        color:white;

        margin-bottom:10px;
    }}


    .hero-sub {{

        text-align:center;

        font-size:1.2rem;

        color:#94A3B8;

        margin-bottom:40px;
    }}




    /* ================= CARDS ================= */

    .issues-card {{

        background:
        {"#1E293B" if home else "white"};

        border-radius:12px;

        padding:1.5rem;

        margin-bottom:1.5rem;

        border:
        {"1px solid #334155" if home else "1px solid #E2E8F0"};

        box-shadow: none;

        transition:0.2s;
    }}


    .issues-card:hover {{

        transform:translateY(-2px);

        box-shadow: {"0px 4px 12px rgba(0,0,0,0.2)" if home else "0px 4px 12px rgba(0,0,0,0.05)"};
    }}



    /* ================= TEXT ================= */

    .secondary-text {{

        color:
        {"#94A3B8" if home else "#64748B"} !important;

        font-size:1rem;

        font-weight:500;
    }}



    .highlight-text {{

        color:#DC2626 !important;

        font-weight:600;

        font-family:'Poppins';
    }}




    /* ================= BADGES ================= */

    .emergency-badge {{

        font-family:'Poppins';

        color:white !important;

        background:#DC2626;

        padding:6px 12px;

        border-radius:8px;

        font-size:0.75rem;

        font-weight:700;

        box-shadow:0px 5px 15px rgba(220,38,38,0.5);
    }}


    .category-badge {{

        font-family:'Poppins';

        color:#DC2626 !important;

        background:#FEF2F2;

        padding:4px 10px;

        border-radius:6px;

        border: 1px solid #FCA5A5;

        font-size:0.75rem;

        font-weight:600;
    }}



    /* ================= BUTTONS ================= */

    .stButton > button {{

        font-family:'Poppins';

        font-weight:600;

        border-radius:6px;

        padding:8px 20px;

        background: #DC2626;

        color:white;

        border: 1px solid #B91C1C;

        transition:0.2s;
    }}



    .stButton > button:hover {{

        transform:translateY(-1px);

        background: #B91C1C;
        
        color: white;

        border-color: #991B1B;
    }}




    /* ================= SIDEBAR ================= */

    [data-testid="stSidebar"] {{

        background:
        {"rgba(15,23,42,0.95)" if home else "white"};

    }}

    [data-testid="stSidebarNav"] span {{

        font-family:'Poppins';

        font-size:1rem;
        
        color: {"white" if home else "#0F172A"};

    }}

    /* Specific fix for Sidebar Icons (collapse/expand, close) */
    [data-testid="collapsedControl"] svg,
    button[kind="header"] svg {{
        color: {"white" if home else "#0F172A"} !important;
        fill: {"white" if home else "#0F172A"} !important;
        stroke: {"white" if home else "#0F172A"} !important;
    }}


    /* ================= INPUTS ================= */

    .stTextInput input,
    .stTextArea textarea {{

        border-radius:10px;

        border: 1px solid {"#475569" if home else "#CBD5E1"} !important;

        padding:12px;

        font-family:'Montserrat';

        background:
        {"rgba(15,23,42,0.8)" if home else "white"} !important;

        color:
        {"white" if home else "#0F172A"} !important;
        
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05);
    }}
    
    .stTextInput input:focus,
    .stTextArea textarea:focus {{
        border-color: #DC2626 !important;
        box-shadow: 0 0 0 1px #DC2626 !important;
    }}

    /* Input Label Text */
    .stTextInput label p, .stTextArea label p, .stCheckbox label p {{
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500 !important;
        color: {"#E2E8F0" if home else "#1E293B"} !important;
    }}

    /* ================= TIMELINE ================= */
    .timeline-container {{
        border-left: 3px solid #334155;
        margin-left: 15px;
        padding-left: 25px;
        position: relative;
    }}

    .timeline-item {{
        position: relative;
        margin-bottom: 25px;
        background: {"#1E293B" if home else "#FFFFFF"};
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid {"#334155" if home else "#E2E8F0"};
    }}

    .timeline-item::before {{
        content: '';
        position: absolute;
        left: -34px; 
        top: 20px;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        background-color: #DC2626;
        border: 4px solid {"#0B0F14" if home else "#F8FAFC"};
        z-index: 2;
    }}

    .timeline-date {{
        font-size: 0.8rem;
        color: #94A3B8;
        font-family: 'Poppins';
        margin-bottom: 5px;
    }}

    .timeline-event {{
        font-size: 1.05rem;
        color: {"#E2E8F0" if home else "#0F172A"};
        font-weight: 600;
        margin: 0 0 5px 0;
    }}

    .timeline-desc {{
        font-size: 0.9rem;
        color: #64748B;
        margin: 0;
    }}

    </style>

    """, unsafe_allow_html=True)