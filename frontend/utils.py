import streamlit as st

def apply_custom_css(home=True):

    st.markdown(f"""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');


    /* ================= BACKGROUND ================= */

    .stApp {{

        background-color: {"#0B0F14" if home else "#F8FAFC"};

        background-image:
        radial-gradient(circle at 1px 1px,
        {"rgba(255,255,255,0.6)" if home else "rgba(0,0,0,0.15)"} 1px,
        transparent 0);

        background-size: 28px 28px;

        background-attachment: fixed;
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
        {"rgba(15,23,42,0.75)" if home else "rgba(255,255,255,0.95)"};

        backdrop-filter: blur(8px);

        border-radius:20px;

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
        {"rgba(30,41,59,0.75)" if home else "white"};

        border-radius:18px;

        padding:1.7rem;

        margin-bottom:1.5rem;

        border:
        {"1px solid rgba(255,255,255,0.1)" if home else "1px solid #E2E8F0"};

        box-shadow:
        {"0px 20px 40px rgba(0,0,0,0.5)" if home else "0px 15px 30px rgba(0,0,0,0.08)"};

        transition:0.3s;
    }}


    .issues-card:hover {{

        transform:translateY(-6px);

        box-shadow:0px 30px 60px rgba(0,0,0,0.4);
    }}



    /* ================= TEXT ================= */

    .secondary-text {{

        color:
        {"#94A3B8" if home else "#64748B"} !important;

        font-size:1rem;

        font-weight:500;
    }}



    .highlight-text {{

        color:#3B82F6 !important;

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

        color:#2563EB !important;

        background:#DBEAFE;

        padding:6px 12px;

        border-radius:8px;

        font-size:0.75rem;

        font-weight:600;
    }}



    /* ================= BUTTONS ================= */

    .stButton > button {{

        font-family:'Poppins';

        font-weight:600;

        border-radius:10px;

        padding:10px 24px;

        background:linear-gradient(135deg,#2563EB,#1E40AF);

        color:white;

        border:none;

        transition:0.25s;
    }}



    .stButton > button:hover {{

        transform:translateY(-2px);

        box-shadow:0px 10px 25px rgba(37,99,235,0.5);
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
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }}

    /* Input Label Text */
    .stTextInput label p, .stTextArea label p, .stCheckbox label p {{
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500 !important;
        color: {"#E2E8F0" if home else "#1E293B"} !important;
    }}



    </style>

    """, unsafe_allow_html=True)