# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import numpy as np
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
from datetime import datetime
import io
import base64
import struct
import xml.etree.ElementTree as ET
import math
import wave
from PIL import Image

# ============================================================
# PAGE CONFIGURATION (MUST BE FIRST STREAMLIT CALL)
# ============================================================
st.set_page_config(
    page_title="Boiler AI - Testing & Simulation Digital Twin",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROCESS THRESHOLDS (CALIBRATION CONSTANTS)
# ============================================================
TEMP_LOW = 30.0
TEMP_NORMAL_MAX = 75.0
TEMP_HIGH = 85.0

FLOW_LOW = 0.30
FLOW_NORMAL_MAX = 5.00

# ============================================================
# STATE INITIALIZATION
# ============================================================
if "sim_temp" not in st.session_state:
    st.session_state.sim_temp = 60.0
if "sim_flow" not in st.session_state:
    st.session_state.sim_flow = 1.50
if "sim_total" not in st.session_state:
    st.session_state.sim_total = 2.00
if "test_history" not in st.session_state:
    st.session_state.test_history = []
if "test_bmt" not in st.session_state:
    st.session_state.test_bmt = None
if "test_bmt_name" not in st.session_state:
    st.session_state.test_bmt_name = ""

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

# ============================================================
# PROFESSIONAL SCADA UI STYLES (DYNAMIC DARK & LIGHT THEMES)
# ============================================================
def get_theme_css(theme="dark"):
    is_dark = (theme == "dark")
    if is_dark:
        return r"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(circle at 50% 0%, rgba(0, 190, 255, .10), transparent 30%),
        linear-gradient(135deg, #02060c 0%, #06111b 52%, #02050a 100%);
    color: #eaf8ff;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #040e18 0%, #02060c 100%) !important;
    border-right: 1px solid rgba(75, 220, 255, 0.15) !important;
}

[data-testid="stToolbar"] {visibility:hidden !important;}
footer {visibility:hidden !important;}
#MainMenu {visibility:hidden !important;}
header[data-testid="stHeader"] {background: transparent !important;}

/* ============================================================
   SCADA NAVIGATION BUTTONS (DARK)
   ============================================================ */
div[data-testid="stPageLink"] {
    display: flex;
    justify-content: center;
    width: 100%;
}

div[data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 12px !important;
    width: 100% !important;
    min-height: 48px !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #092032 0%, #04121d 100%) !important;
    border: 1.5px solid rgba(69, 231, 255, 0.45) !important;
    color: #f0fbff !important;
    text-decoration: none !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45), inset 0 0 15px rgba(69, 231, 255, 0.10) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

div[data-testid="stPageLink"] a:hover {
    border-color: #45e7ff !important;
    background: linear-gradient(135deg, #0d314d 0%, #071c2d 100%) !important;
    box-shadow: 0 0 25px rgba(69, 231, 255, 0.55), inset 0 0 20px rgba(69, 231, 255, 0.25) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stPageLink"] a p, 
div[data-testid="stPageLink"] a span {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    color: #edfaff !important;
    margin: 0 !important;
}

div[data-testid="stPageLink"] a[aria-disabled="true"],
div[data-testid="stPageLink"] a.disabled {
    background: linear-gradient(135deg, rgba(8, 48, 35, 0.95) 0%, rgba(3, 24, 18, 0.95) 100%) !important;
    border: 1.5px solid #55ffc0 !important;
    box-shadow: 0 0 20px rgba(85, 255, 192, 0.35), inset 0 0 15px rgba(85, 255, 192, 0.20) !important;
    opacity: 1 !important;
    cursor: default !important;
}

div[data-testid="stPageLink"] a[aria-disabled="true"] p,
div[data-testid="stPageLink"] a[aria-disabled="true"] span {
    color: #55ffc0 !important;
}

.block-container {
    max-width: 1700px;
    padding: 14px 2rem 30px 2rem;
}

* {
    font-family: 'Inter', sans-serif;
}

h1,h2,h3,h4 {
    font-family: 'Orbitron', sans-serif !important;
}

.topbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:13px 18px;
    border:1px solid rgba(75,220,255,.22);
    border-radius:12px;
    background:rgba(3,12,21,.94);
    box-shadow:0 8px 30px rgba(0,0,0,.25);
    min-height: 48px;
}

.brand {
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    letter-spacing:1.5px;
    color:#f0fbff;
}

.brand span {color:#46e7ff;}

.online {
    color:#63ffc0;
    font-weight:700;
    letter-spacing:1px;
    text-shadow:0 0 10px rgba(80,255,190,.35);
}

.sim-tag {
    color:#ffd66b;
    font-weight:700;
    letter-spacing:1px;
    text-shadow:0 0 10px rgba(255,214,107,.35);
}

.offline {color:#ff7777;font-weight:700;}

.hero {
    padding:24px 28px;
    border-radius:18px;
    border:1px solid rgba(65,220,255,.18);
    background:
      linear-gradient(110deg,rgba(8,28,44,.96),rgba(4,13,23,.95)),
      radial-gradient(circle at right,rgba(255,90,20,.12),transparent 30%);
    box-shadow:0 10px 35px rgba(0,0,0,.3);
    animation:fadein .7s ease;
}

.hero-title {
    font-family:'Orbitron',sans-serif;
    font-size:clamp(23px,3vw,38px);
    font-weight:800;
    line-height:1.15;
    color:#ffffff;
}

.hero-title span {color:#45e7ff;text-shadow:0 0 20px rgba(69,231,255,.4);}

.hero-sub {
    color:#8faabb;
    margin-top:8px;
    font-size:16px;
}

.team-line {
    margin-top:14px;
    color:#7793a3;
    font-size:13px;
}

.section-title {
    margin:22px 0 10px;
    padding:9px 13px;
    border-left:3px solid #45e7ff;
    background:linear-gradient(90deg,rgba(69,231,255,.08),transparent);
    font-family:'Orbitron',sans-serif;
    font-size:14px;
    letter-spacing:1.4px;
    color:#eaf8ff;
}

.panel {
    background:linear-gradient(145deg,rgba(8,23,37,.96),rgba(3,10,18,.96));
    border:1px solid rgba(95,190,220,.14);
    border-radius:15px;
    padding:17px;
    box-shadow:0 9px 30px rgba(0,0,0,.24);
    color:#eaf8ff;
}

.panel-head {
    color:#70eaff;
    font-family:'Orbitron',sans-serif;
    font-size:12px;
    letter-spacing:1.4px;
    margin-bottom:10px;
}

.param {
    padding:11px 0;
    border-bottom:1px solid rgba(120,170,190,.10);
}

.param:last-child {border-bottom:none;}

.param-name {color:#7894a5;font-size:12px;}
.param-value {
    font-family:'Orbitron',sans-serif;
    font-size:25px;
    font-weight:700;
    color:#edfaff;
}

.boiler-area {
    min-height:385px;
    display:flex;
    justify-content:center;
    align-items:center;
    position:relative;
    overflow:hidden;
}

.boiler-body {
    width:205px;
    height:270px;
    position:relative;
    border:3px solid #78909b;
    border-radius:30px 30px 45px 45px;
    background:linear-gradient(90deg,#17252e,#4d626c 48%,#15242d);
    box-shadow:
        inset 0 0 28px rgba(0,0,0,.55),
        0 0 25px rgba(70,210,255,.10);
}

.dome {
    position:absolute;
    width:92px;
    height:34px;
    top:-35px;
    left:53px;
    border:3px solid #78909b;
    border-radius:50%;
    background:#17242d;
}

.water {
    position:absolute;
    left:13px;
    right:13px;
    bottom:13px;
    height:57%;
    border-radius:0 0 30px 30px;
    background:linear-gradient(#07506a,#062e40);
    border-top:2px solid #42ddff;
    overflow:hidden;
    transition: height 0.4s ease;
}

.wave {
    position:absolute;
    width:180%;
    height:30px;
    left:-40%;
    top:-8px;
    border-radius:50%;
    border-top:3px solid rgba(70,230,255,.7);
    animation:wave 2s linear infinite;
}

.heater {
    position:absolute;
    width:112px;
    height:15px;
    left:46px;
    bottom:7px;
    border-radius:50%;
    background:#ff6d1b;
    box-shadow:0 0 18px #ff6414,0 0 48px rgba(255,75,0,.62);
    animation:heater 1.1s ease-in-out infinite alternate;
}

.thermal-zone {
    position:absolute;
    width:120px;
    height:120px;
    right:-2px;
    top:47px;
    border-radius:50%;
    background:radial-gradient(circle,rgba(255,72,10,.48),transparent 67%);
    filter:blur(3px);
    animation:thermal 1.8s ease-in-out infinite alternate;
}

.sensor-dot {
    position:absolute;
    width:13px;
    height:13px;
    border-radius:50%;
    background:#51eaff;
    box-shadow:0 0 15px #51eaff;
    animation:pulse 1.5s infinite;
    z-index:5;
}

.pt100 {right:-25px;top:95px;}
.flow {left:-25px;bottom:100px;}
.thermal {right:28px;top:28px;background:#ff7b26;box-shadow:0 0 15px #ff7b26;}

.pipe-left {
    position:absolute;
    width:90px;
    height:30px;
    left:calc(50% - 220px);
    border:3px solid #718a96;
    border-right:0;
    border-radius:16px 0 0 16px;
}

.pipe-right {
    position:absolute;
    width:90px;
    height:30px;
    right:calc(50% - 220px);
    border:3px solid #718a96;
    border-left:0;
    border-radius:0 16px 16px 0;
}

.flow-arrow {
    position:absolute;
    left:calc(50% - 245px);
    color:#52eaff;
    font-size:22px;
    animation:moveflow 2s linear infinite;
}

.health {
    text-align:center;
}

.health-circle {
    width:150px;
    height:150px;
    margin:8px auto 15px;
    border-radius:50%;
    background:conic-gradient(#55ffc0 0 94%,#122632 94% 100%);
    display:flex;
    align-items:center;
    justify-content:center;
    box-shadow:0 0 30px rgba(80,255,190,.12);
}

.health-inner {
    width:116px;
    height:116px;
    border-radius:50%;
    background:#06101a;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family:'Orbitron',sans-serif;
    font-size:28px;
    font-weight:800;
    color:#edfaff;
}

.range-box {
    padding:10px 13px;
    border-radius:10px;
    margin-top:9px;
    background:rgba(9,24,37,.8);
    border:1px solid rgba(100,190,220,.12);
}

.range-title {
    color:#7894a5;
    font-size:12px;
}

.range-value {
    font-family:'Orbitron',sans-serif;
    color:#eafaff;
    font-size:16px;
    font-weight:700;
}

.info-box {
    padding:20px;
    border-radius:14px;
    border:1px solid rgba(75,220,255,.20);
    background:rgba(5,24,35,.55);
    color:#eaf8ff;
}

.footer {
    text-align:center;
    color:#587284;
    margin-top:25px;
    padding-top:18px;
    border-top:1px solid rgba(100,160,180,.10);
    font-size:12px;
    letter-spacing:1px;
}

.bench-card {
    padding: 16px 20px;
    border-radius: 14px;
    border: 1px solid rgba(75,220,255,.24);
    background: linear-gradient(135deg, rgba(8,26,40,.96), rgba(4,14,24,.96));
    margin-bottom: 14px;
    color:#eaf8ff;
}

/* Theme Switcher Styling in Top-Right Corner (DARK) */
div[data-testid="stSegmentedControl"] {
    background: rgba(3, 12, 21, 0.94) !important;
    border: 1.5px solid rgba(75, 220, 255, 0.35) !important;
    border-radius: 12px !important;
    padding: 3px !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4) !important;
}

div[data-testid="stSegmentedControl"] button {
    border-radius: 9px !important;
    color: #8faabb !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    border: none !important;
    background: transparent !important;
}

div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #092032 0%, #04121d 100%) !important;
    color: #45e7ff !important;
    border: 1px solid rgba(69, 231, 255, 0.6) !important;
    box-shadow: 0 0 15px rgba(69, 231, 255, 0.35) !important;
}

@keyframes fadein {from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes wave {to{transform:translateX(45px)}}
@keyframes heater {from{transform:scaleX(.88);opacity:.65}to{transform:scaleX(1.08);opacity:1}}
@keyframes thermal {from{transform:scale(.82);opacity:.45}to{transform:scale(1.16);opacity:1}}
@keyframes pulse {50%{transform:scale(1.55);opacity:.62}}
@keyframes moveflow {from{transform:translateX(0);opacity:0}15%{opacity:1}80%{opacity:1}to{transform:translateX(175px);opacity:0}}
</style>"""
    else:
        return r"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');

/* Base App Background & Typography */
.stApp {
    background:
        radial-gradient(circle at 50% 0%, rgba(2, 132, 199, .09), transparent 35%),
        linear-gradient(135deg, #f8fafc 0%, #edf5fb 52%, #f1f6fa 100%) !important;
    color: #0f172a !important;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1.5px solid rgba(2, 132, 199, 0.22) !important;
    box-shadow: 2px 0 15px rgba(15, 23, 42, 0.04) !important;
}

[data-testid="stSidebar"] * {
    color: #0f172a !important;
}

[data-testid="stToolbar"] {visibility:hidden !important;}
footer {visibility:hidden !important;}
#MainMenu {visibility:hidden !important;}
header[data-testid="stHeader"] {background: transparent !important;}

/* Navigation Links */
div[data-testid="stPageLink"] {
    display: flex;
    justify-content: center;
    width: 100%;
}

div[data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 12px !important;
    width: 100% !important;
    min-height: 48px !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    background: linear-gradient(135deg, #ffffff 0%, #f4f8fc 100%) !important;
    border: 1.5px solid rgba(2, 132, 199, 0.35) !important;
    color: #0f172a !important;
    text-decoration: none !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06), inset 0 0 10px rgba(2, 132, 199, 0.04) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

div[data-testid="stPageLink"] a:hover {
    border-color: #0284c7 !important;
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
    box-shadow: 0 4px 18px rgba(2, 132, 199, 0.2) !important;
    transform: translateY(-2px) !important;
}

div[data-testid="stPageLink"] a p, 
div[data-testid="stPageLink"] a span {
    font-family: 'Orbitron', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    color: #0f172a !important;
    margin: 0 !important;
}

div[data-testid="stPageLink"] a[aria-disabled="true"],
div[data-testid="stPageLink"] a.disabled {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
    border: 1.5px solid #059669 !important;
    box-shadow: 0 4px 15px rgba(5, 150, 105, 0.18), inset 0 0 12px rgba(5, 150, 105, 0.1) !important;
    opacity: 1 !important;
    cursor: default !important;
}

div[data-testid="stPageLink"] a[aria-disabled="true"] p,
div[data-testid="stPageLink"] a[aria-disabled="true"] span {
    color: #065f46 !important;
}

.block-container {
    max-width: 1700px;
    padding: 14px 2rem 30px 2rem;
}

* {
    font-family: 'Inter', sans-serif;
}

h1,h2,h3,h4 {
    font-family: 'Orbitron', sans-serif !important;
    color: #0f172a !important;
}

/* Topbar in Light Mode */
.topbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:13px 18px;
    border:1.5px solid rgba(2, 132, 199, 0.25) !important;
    border-radius:14px !important;
    background:#ffffff !important;
    box-shadow:0 6px 22px rgba(15, 23, 42, 0.06) !important;
    color:#0f172a !important;
    min-height: 48px;
}

.brand {
    font-family:'Orbitron',sans-serif;
    font-weight:700;
    letter-spacing:1.5px;
    color:#072740 !important;
}

.brand span {color:#0284c7 !important;}

.online {
    color:#059669 !important;
    font-weight:700 !important;
    letter-spacing:1px;
}

.sim-tag {
    color:#b45309 !important;
    font-weight:700 !important;
    letter-spacing:1px;
}

.offline {color:#dc2626 !important; font-weight:700 !important;}

/* Hero Header in Light Mode */
.hero {
    padding:24px 28px;
    border-radius:18px;
    border:1.5px solid rgba(2, 132, 199, 0.22) !important;
    background:
      linear-gradient(110deg,#ffffff 0%, #f0f7fe 100%),
      radial-gradient(circle at right,rgba(255,100,20,.06),transparent 30%) !important;
    box-shadow:0 10px 30px rgba(15, 23, 42, 0.06) !important;
    animation:fadein .7s ease;
}

.hero-title {
    font-family:'Orbitron',sans-serif;
    font-size:clamp(23px,3vw,38px);
    font-weight:800;
    line-height:1.15;
    color:#0f172a !important;
}

.hero-title span {color:#0284c7 !important; text-shadow:none !important;}

.hero-sub {
    color:#475569 !important;
    margin-top:8px;
    font-size:16px;
}

.team-line {
    margin-top:14px;
    color:#64748b !important;
    font-size:13px;
}

.section-title {
    margin:22px 0 10px;
    padding:9px 13px;
    border-left:4px solid #0284c7 !important;
    background:linear-gradient(90deg,rgba(2, 132, 199, 0.12),transparent) !important;
    font-family:'Orbitron',sans-serif;
    font-size:14px;
    letter-spacing:1.4px;
    color:#0f172a !important;
    font-weight:700 !important;
}

/* Panels and Cards in Light Mode */
.panel {
    background:#ffffff !important;
    border:1.5px solid rgba(2, 132, 199, 0.22) !important;
    border-radius:16px !important;
    padding:17px;
    box-shadow:0 8px 25px rgba(15, 23, 42, 0.06) !important;
    color:#0f172a !important;
}

.panel-head {
    color:#0284c7 !important;
    font-family:'Orbitron',sans-serif;
    font-size:12px;
    letter-spacing:1.4px;
    margin-bottom:10px;
    font-weight:700 !important;
}

.param {
    padding:11px 0;
    border-bottom:1px solid rgba(2, 132, 199, 0.12) !important;
}

.param:last-child {border-bottom:none;}

.param-name {color:#475569 !important; font-size:12px; font-weight:600 !important;}
.param-value {
    font-family:'Orbitron',sans-serif;
    font-size:25px;
    font-weight:800;
    color:#0f172a !important;
}

.range-box {
    padding:10px 13px;
    border-radius:10px;
    margin-top:9px;
    background:#f1f7fd !important;
    border:1px solid rgba(2, 132, 199, 0.22) !important;
}

.range-title {
    color:#475569 !important;
    font-size:12px;
    font-weight:600 !important;
}

.range-value {
    font-family:'Orbitron',sans-serif;
    color:#0f172a !important;
    font-size:16px;
    font-weight:700;
}

.info-box {
    padding:20px;
    border-radius:14px;
    border:1.5px solid rgba(2, 132, 199, 0.22) !important;
    background:#ffffff !important;
    box-shadow:0 6px 20px rgba(15, 23, 42, 0.05) !important;
    color:#0f172a !important;
}

.bench-card {
    padding: 16px 20px;
    border-radius: 14px;
    border: 1.5px solid rgba(2, 132, 199, 0.22) !important;
    background: #ffffff !important;
    margin-bottom: 14px;
    box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05) !important;
    color:#0f172a !important;
}

/* Action / Preset Buttons in Light Mode */
div.stButton > button {
    background: #ffffff !important;
    border: 1.5px solid rgba(2, 132, 199, 0.35) !important;
    color: #0f172a !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06) !important;
    transition: all 0.2s ease !important;
}

div.stButton > button:hover {
    background: #e0f2fe !important;
    border-color: #0284c7 !important;
    color: #0284c7 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.2) !important;
}

div.stButton > button:active,
div.stButton > button:focus {
    background: #e0f2fe !important;
    color: #0284c7 !important;
    border-color: #0284c7 !important;
}

/* Sliders in Light Mode */
div[data-testid="stSlider"] label p {
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
}

div[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: #0284c7 !important;
    font-weight: 700 !important;
}

div[data-testid="stSlider"] [data-testid="stTickBarMin"],
div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: #64748b !important;
}

/* Input Fields in Light Mode */
div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border: 1.5px solid rgba(2, 132, 199, 0.3) !important;
    border-radius: 10px !important;
}

div[data-baseweb="input"] input {
    color: #0f172a !important;
}

div[data-testid="stFileUploader"] {
    background-color: #ffffff !important;
    border: 1.5px dashed rgba(2, 132, 199, 0.45) !important;
    border-radius: 14px !important;
}

div[data-testid="stFileUploader"] * {
    color: #0f172a !important;
}

div[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1.5px solid rgba(2, 132, 199, 0.22) !important;
    border-radius: 12px !important;
}

div[data-testid="stExpander"] * {
    color: #0f172a !important;
}

/* Captions and Paragraphs */
.stCaption, p, span, label {
    color: #475569 !important;
}

/* Theme Switcher Styling (LIGHT) */
div[data-testid="stSegmentedControl"] {
    background: #ffffff !important;
    border: 1.5px solid rgba(2, 132, 199, 0.3) !important;
    border-radius: 12px !important;
    padding: 3px !important;
    box-shadow: 0 4px 15px rgba(15, 23, 42, 0.06) !important;
}

div[data-testid="stSegmentedControl"] button {
    border-radius: 9px !important;
    color: #64748b !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    border: none !important;
    background: transparent !important;
}

div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
    color: #0284c7 !important;
    border: 1px solid rgba(2, 132, 199, 0.45) !important;
    box-shadow: 0 2px 10px rgba(2, 132, 199, 0.2) !important;
}

/* Boiler Graphic in Light Mode */
.boiler-area {
    min-height:385px;
    display:flex;
    justify-content:center;
    align-items:center;
    position:relative;
    overflow:hidden;
}

.boiler-body {
    width:205px;
    height:270px;
    position:relative;
    border:3px solid #94a3b8;
    border-radius:30px 30px 45px 45px;
    background:linear-gradient(90deg,#e2e8f0,#cbd5e1 48%,#e2e8f0);
    box-shadow:
        inset 0 0 20px rgba(0,0,0,.15),
        0 0 25px rgba(2, 132, 199, 0.12);
}

.dome {
    position:absolute;
    width:92px;
    height:34px;
    top:-35px;
    left:53px;
    border:3px solid #94a3b8;
    border-radius:50%;
    background:#e2e8f0;
}

.water {
    position:absolute;
    left:13px;
    right:13px;
    bottom:13px;
    height:57%;
    border-radius:0 0 30px 30px;
    background:linear-gradient(#38bdf8,#0284c7);
    border-top:2px solid #0369a1;
    overflow:hidden;
    transition: height 0.4s ease;
}

.wave {
    position:absolute;
    width:180%;
    height:30px;
    left:-40%;
    top:-8px;
    border-radius:50%;
    border-top:3px solid rgba(255,255,255,.9);
    animation:wave 2s linear infinite;
}

.heater {
    position:absolute;
    width:112px;
    height:15px;
    left:46px;
    bottom:7px;
    border-radius:50%;
    background:#f97316;
    box-shadow:0 0 18px #ea580c,0 0 40px rgba(234,88,12,.5);
    animation:heater 1.1s ease-in-out infinite alternate;
}

.thermal-zone {
    position:absolute;
    width:120px;
    height:120px;
    right:-2px;
    top:47px;
    border-radius:50%;
    background:radial-gradient(circle,rgba(249,115,22,.4),transparent 67%);
    filter:blur(3px);
    animation:thermal 1.8s ease-in-out infinite alternate;
}

.sensor-dot {
    position:absolute;
    width:13px;
    height:13px;
    border-radius:50%;
    background:#0284c7;
    box-shadow:0 0 15px #0284c7;
    animation:pulse 1.5s infinite;
    z-index:5;
}

.pt100 {right:-25px;top:95px;}
.flow {left:-25px;bottom:100px;}
.thermal {right:28px;top:28px;background:#f97316;box-shadow:0 0 15px #f97316;}

.pipe-left {
    position:absolute;
    width:90px;
    height:30px;
    left:calc(50% - 220px);
    border:3px solid #94a3b8;
    border-right:0;
    border-radius:16px 0 0 16px;
}

.pipe-right {
    position:absolute;
    width:90px;
    height:30px;
    right:calc(50% - 220px);
    border:3px solid #94a3b8;
    border-left:0;
    border-radius:0 16px 16px 0;
}

.flow-arrow {
    position:absolute;
    left:calc(50% - 245px);
    color:#0284c7;
    font-size:22px;
    animation:moveflow 2s linear infinite;
}

.health {
    text-align:center;
}

.health-circle {
    width:150px;
    height:150px;
    margin:8px auto 15px;
    border-radius:50%;
    background:conic-gradient(#10b981 0 94%,#e2e8f0 94% 100%);
    display:flex;
    align-items:center;
    justify-content:center;
    box-shadow:0 0 25px rgba(16, 185, 129, 0.2);
}

.health-inner {
    width:116px;
    height:116px;
    border-radius:50%;
    background:#ffffff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family:'Orbitron',sans-serif;
    font-size:28px;
    font-weight:800;
    color:#0f172a;
}

.footer {
    text-align:center;
    color:#64748b;
    margin-top:25px;
    padding-top:18px;
    border-top:1px solid rgba(2, 132, 199, 0.18);
    font-size:12px;
    letter-spacing:1px;
}

@keyframes fadein {from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes wave {to{transform:translateX(45px)}}
@keyframes heater {from{transform:scaleX(.88);opacity:.65}to{transform:scaleX(1.08);opacity:1}}
@keyframes thermal {from{transform:scale(.82);opacity:.45}to{transform:scale(1.16);opacity:1}}
@keyframes pulse {50%{transform:scale(1.55);opacity:.62}}
@keyframes moveflow {from{transform:translateX(0);opacity:0}15%{opacity:1}80%{opacity:1}to{transform:translateX(175px);opacity:0}}
</style>"""

st.markdown(get_theme_css(st.session_state.theme_mode), unsafe_allow_html=True)


# ============================================================
# HELPER DATA STRUCTURE
# ============================================================
class ParameterStates(dict):
    """Dictionary supporting both key access ('temperature', etc.) and tuple unpacking."""
    def __iter__(self):
        yield self["temperature"]
        yield self["flow"]
        yield self["total_water"]

# ============================================================
# TESTO 872 BMT PARSER HELPERS
# ============================================================
def _bmt_find_tofo(data):
    start = data.find(b"<ToFo")
    if start < 0:
        raise ValueError("BMT ToFo header not found.")
    end = data.find(b"ToFo>", start)
    if end < 0:
        raise ValueError("BMT ToFo header is incomplete.")
    end += len(b"ToFo>")
    return start, end, ET.fromstring(data[start:end].decode(errors="strict"))


def _bmt_metadata_tree(xml_bytes):
    root = ET.fromstring(xml_bytes)

    def convert(el):
        children = list(el)
        attrs = dict(el.attrib)
        if "name" not in attrs:
            return None

        if "type" in attrs and "size" in attrs:
            return {
                "kind": "item",
                "name": attrs["name"],
                "type": attrs["type"],
                "size": int(attrs["size"]),
            }

        group = {
            "kind": "group",
            "name": attrs["name"],
            "children": [],
        }
        for child in children:
            node = convert(child)
            if node is not None:
                group["children"].append(node)
        return group

    return convert(root)


def _bmt_read_int(f, size, endian):
    b = f.read(size)
    if len(b) != size:
        raise EOFError("Unexpected end of BMT while reading integer.")
    return int.from_bytes(b, endian, signed=False)


def _bmt_read_float(f, size, endian):
    b = f.read(size)
    if len(b) != size or size % 4:
        raise ValueError("Invalid BMT float field.")
    fmt = (">" if endian == "big" else "<") + ("f" * (size // 4))
    vals = struct.unpack(fmt, b)
    return vals[0] if len(vals) == 1 else vals


def _bmt_skip(f, size):
    f.seek(size, io.SEEK_CUR)


def _bmt_parse_mat(f, size, endian, is_ir):
    header = f.read(24)
    if len(header) != 24:
        raise EOFError("Incomplete BMT matrix header.")

    fmt = (">" if endian == "big" else "<") + "6I"
    dims, rows, cols, depth, channels, element_size = struct.unpack(fmt, header)

    payload_size = size - 24
    raw = f.read(payload_size)

    if not is_ir:
        return None

    if rows <= 0 or cols <= 0 or channels <= 0:
        raise ValueError("Invalid BMT IR matrix dimensions.")

    dtype = np.dtype(">i2" if endian == "big" else "<i2")
    count = rows * cols * channels
    arr = np.frombuffer(raw, dtype=dtype, count=count)

    if arr.size != count:
        raise ValueError("BMT IR matrix has an unexpected size.")

    arr = arr.reshape((rows, cols, channels)).astype(np.float32)
    temp = arr * ((1001.0 - (-101.0)) / 65535.0) - 101.0
    return temp[:, :, 0]


def _bmt_parse_item(f, item):
    name = item["name"]
    typ = item["type"]
    size = item["size"]
    low = typ.lower()

    if "vecuint8" in low:
        if "vis" in name.lower():
            n = _bmt_read_int(f, 4, "little")
            blob = f.read(n)
            if len(blob) != n:
                raise EOFError("Incomplete embedded visual image.")
            return {"visual_jpeg": blob}
        _bmt_skip(f, size)
        return None

    if "cvmat" in low:
        return _bmt_parse_mat(f, size, "little", name.lower() == "ir")

    if low == "string" or low == "uuid":
        raw = f.read(size)
        return raw.decode(errors="ignore").split("\x00")[-1]

    if low == "version":
        vals = [_bmt_read_int(f, 4, "little") for _ in range(3)]
        return ".".join(map(str, vals))

    if low == "cvpoint":
        return (_bmt_read_int(f, 4, "little"), _bmt_read_int(f, 4, "little"))

    if low == "cvrect":
        p1 = (_bmt_read_int(f, 4, "little"), _bmt_read_int(f, 4, "little"))
        p2 = (_bmt_read_int(f, 4, "little"), _bmt_read_int(f, 4, "little"))
        return (p1, p2)

    if "float" in low:
        value = _bmt_read_float(f, size, "little")
        if "temperature" in low:
            if isinstance(value, tuple):
                value = tuple(v - 273.15 for v in value)
            else:
                value -= 273.15
        return value

    raw = f.read(size)
    if len(raw) != size:
        raise EOFError("Unexpected end of BMT while reading field.")
    return int.from_bytes(raw, "little", signed=False)


def _bmt_parse_tree(f, node, endian):
    if node["kind"] == "item":
        if node["type"].lower().find("cvmat") >= 0:
            return _bmt_parse_mat(f, node["size"], endian, node["name"].lower() == "ir")
        return _bmt_parse_item_endian(f, node, endian)

    out = {}
    for child in node["children"]:
        out[child["name"]] = _bmt_parse_tree(f, child, endian)
    return out


def _bmt_parse_item_endian(f, item, endian):
    name = item["name"]
    typ = item["type"]
    size = item["size"]
    low = typ.lower()

    if "vecuint8" in low:
        if "vis" in name.lower():
            n = _bmt_read_int(f, 4, endian)
            blob = f.read(n)
            if len(blob) != n:
                raise EOFError("Incomplete embedded visual image.")
            return {"visual_jpeg": blob}
        _bmt_skip(f, size)
        return None

    if "cvmat" in low:
        return _bmt_parse_mat(f, size, endian, name.lower() == "ir")

    if low in ("string", "uuid"):
        raw = f.read(size)
        return raw.decode(errors="ignore").split("\x00")[-1]

    if low == "version":
        vals = [_bmt_read_int(f, 4, endian) for _ in range(3)]
        return ".".join(map(str, vals))

    if low == "cvpoint":
        return (_bmt_read_int(f, 4, endian), _bmt_read_int(f, 4, endian))

    if low == "cvrect":
        p1 = (_bmt_read_int(f, 4, endian), _bmt_read_int(f, 4, endian))
        p2 = (_bmt_read_int(f, 4, endian), _bmt_read_int(f, 4, endian))
        return (p1, p2)

    if "float" in low:
        value = _bmt_read_float(f, size, endian)
        if "temperature" in low:
            if isinstance(value, tuple):
                value = tuple(v - 273.15 for v in value)
            else:
                value -= 273.15
        return value

    raw = f.read(size)
    if len(raw) != size:
        raise EOFError("Unexpected end of BMT while reading field.")
    return int.from_bytes(raw, endian, signed=False)


def parse_testo_bmt(bmt_bytes):
    start, tofo_end, tofo = _bmt_find_tofo(bmt_bytes)

    xml_node = next(
        (child for child in list(tofo)
         if child.tag.lower().endswith("xml")),
        None
    )
    data_node = next(
        (child for child in list(tofo)
         if child.tag.lower().endswith("data")),
        None
    )

    if xml_node is None or data_node is None:
        raise ValueError("BMT metadata/data descriptors not found.")

    xml_size = int(xml_node.attrib["size"])
    endian = data_node.attrib.get("endianness", "little").lower()
    if endian not in ("little", "big"):
        endian = "little"

    metadata_start = tofo_end
    metadata_end = metadata_start + xml_size
    metadata_xml = bmt_bytes[metadata_start:metadata_end]

    root = _bmt_metadata_tree(metadata_xml)
    if root is None:
        raise ValueError("Could not parse BMT metadata.")

    f = io.BytesIO(bmt_bytes)
    f.seek(metadata_end)
    f.read(1)

    parsed = _bmt_parse_tree(f, root, endian)

    ir = None
    visual = None

    def walk(obj):
        nonlocal ir, visual
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == "ir" and isinstance(v, np.ndarray):
                    ir = v
                elif isinstance(v, dict) and "visual_jpeg" in v:
                    visual = v["visual_jpeg"]
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(parsed)

    if ir is None:
        raise ValueError("No radiometric IR matrix was found in this BMT.")

    return {
        "temperature_matrix": ir,
        "visual_jpeg": visual,
        "metadata": parsed,
        "file_size": len(bmt_bytes),
        "endianness": endian,
    }


def bmt_summary(result):
    if result is None or "temperature_matrix" not in result:
        return None
    a = np.asarray(result["temperature_matrix"], dtype=float)
    finite = np.isfinite(a)
    if not finite.any():
        raise ValueError("BMT temperature matrix contains no valid values.")

    ys, xs = np.where(finite)
    flat_index = np.nanargmax(np.where(finite, a, np.nan))
    y, x = np.unravel_index(flat_index, a.shape)

    return {
        "tmax": float(np.nanmax(a)),
        "tmin": float(np.nanmin(a)),
        "tavg": float(np.nanmean(a)),
        "hot_x": int(x),
        "hot_y": int(y),
        "hotspot_x": int(x),
        "hotspot_y": int(y),
        "matrix": a,
        "rows": int(a.shape[0]),
        "cols": int(a.shape[1]),
    }


def warning_beep_html():
    """Generate a synthesized audio beep for audible fault alarming."""
    sample_rate = 22050
    duration = 0.22
    frequency = 880
    samples = int(sample_rate * duration)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        frames = bytearray()
        for i in range(samples):
            attack = min(1.0, i / (sample_rate * 0.015))
            release = min(1.0, (samples - i) / (sample_rate * 0.035))
            envelope = min(attack, release)
            value = int(
                15000 * envelope *
                math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            frames += int(value).to_bytes(2, byteorder="little", signed=True)

        wav.writeframes(frames)

    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    return f"""
    <audio autoplay loop>
        <source src="data:audio/wav;base64,{encoded}" type="audio/wav">
    </audio>
    """


def get_parameter_states(f, t, total_water):
    """Return individual process states supporting dict indexing and tuple unpacking."""
    temp_state = (
        "LOW" if t < TEMP_LOW
        else "NORMAL" if t <= TEMP_NORMAL_MAX
        else "HIGH" if t < TEMP_HIGH
        else "CRITICAL"
    )
    flow_state = (
        "LOW" if f < FLOW_LOW
        else "NORMAL" if f <= FLOW_NORMAL_MAX
        else "HIGH"
    )
    water_state = (
        "LOW" if total_water < 0.50
        else "NORMAL" if total_water <= 5.00
        else "HIGH"
    )
    return ParameterStates({
        "temperature": temp_state,
        "flow": flow_state,
        "total_water": water_state
    })


def sensor_fusion(f, t, thermal_tmax=None, hotspot=False, total_water=None):
    """
    Rule-based boiler fault diagnosis using:
      PT100 temperature + YF-S201 flow + cumulative total water + Testo 872 Tmax.
    """
    # ---------- Process states ----------
    temp_state = (
        "LOW" if t < TEMP_LOW
        else "NORMAL" if t <= TEMP_NORMAL_MAX
        else "HIGH" if t < TEMP_HIGH
        else "CRITICAL"
    )

    flow_state = (
        "LOW" if f < FLOW_LOW
        else "NORMAL" if f <= FLOW_NORMAL_MAX
        else "HIGH"
    )

    water_state = (
        "LOW" if (total_water is not None and total_water < 0.50)
        else "NORMAL" if (total_water is None or total_water <= 5.00)
        else "HIGH"
    )

    # ---------- Thermal state ----------
    if thermal_tmax is None:
        thermal_state = "NO THERMAL DATA"
    elif thermal_tmax >= TEMP_HIGH:
        thermal_state = "CRITICAL"
    elif thermal_tmax > TEMP_NORMAL_MAX:
        thermal_state = "HIGH"
    else:
        thermal_state = "NORMAL"

    thermal_hot = (
        thermal_tmax is not None
        and thermal_tmax > TEMP_NORMAL_MAX
    )
    thermal_critical = (
        thermal_tmax is not None
        and thermal_tmax >= TEMP_HIGH
    )

    # ============================================================
    # PRIORITY 1 — DANGEROUS / STRONG MULTI-SENSOR CONDITIONS
    # ============================================================
    if temp_state in ("HIGH", "CRITICAL") and flow_state == "LOW" and water_state == "LOW":
        if thermal_critical or hotspot:
            return (
                "INLET/PUMP FAILURE — LOW FLOW + LOW WATER + OVERHEATING",
                "CRITICAL"
            )
        return (
            "INLET/PUMP FAILURE OR FLOW RESTRICTION — LOW FLOW + LOW WATER",
            "WARNING"
        )

    if temp_state in ("HIGH", "CRITICAL") and flow_state == "LOW":
        if thermal_critical or hotspot:
            return (
                "FLOW RESTRICTION / POSSIBLE INLET-PUMP FAULT WITH OVERHEATING",
                "CRITICAL"
            )
        return (
            "LOW FLOW WITH HIGH TEMPERATURE — CHECK INLET/PUMP",
            "WARNING"
        )

    if temp_state in ("HIGH", "CRITICAL") and water_state == "LOW":
        if thermal_critical or hotspot:
            return (
                "LOW WATER / DRY-RUN RISK — OVERHEATING",
                "CRITICAL"
            )
        return (
            "LOW TOTAL WATER WITH HIGH TEMPERATURE",
            "WARNING"
        )

    # ============================================================
    # PRIORITY 2 — FLOW / WATER SUPPLY PROBLEMS
    # ============================================================
    if temp_state == "NORMAL" and flow_state == "LOW" and water_state == "LOW":
        return (
            "INLET FLOW / PUMP PROBLEM — LOW FLOW AND LOW TOTAL WATER",
            "WARNING"
        )

    if temp_state == "NORMAL" and flow_state == "LOW" and water_state == "NORMAL":
        return (
            "LOW INLET FLOW — CHECK PUMP, INLET VALVE OR FLOW RESTRICTION",
            "WARNING"
        )

    if temp_state == "LOW" and flow_state == "LOW" and water_state == "LOW":
        return (
            "WATER SUPPLY / PUMP NOT DELIVERING — LOW FLOW AND LOW WATER",
            "WARNING"
        )

    if temp_state == "LOW" and flow_state == "LOW" and water_state == "NORMAL":
        return (
            "LOW HEATING / LOW INLET FLOW — CHECK HEATER AND PUMP",
            "WARNING"
        )

    if temp_state == "NORMAL" and flow_state == "NORMAL" and water_state == "LOW":
        return (
            "LOW TOTAL WATER — INSUFFICIENT CUMULATIVE WATER INPUT",
            "WARNING"
        )

    if flow_state == "HIGH" and temp_state == "LOW":
        return (
            "EXCESSIVE FLOW / WATER OVERFEED — LOW TEMPERATURE",
            "WARNING"
        )

    if flow_state == "HIGH" and temp_state == "NORMAL":
        return (
            "HIGH FLOW — CHECK INLET CONTROL",
            "WARNING"
        )

    if flow_state == "HIGH" and temp_state in ("HIGH", "CRITICAL"):
        return (
            "HIGH FLOW WITH HIGH TEMPERATURE — CHECK PROCESS CONTROL",
            "WARNING"
        )

    # ============================================================
    # PRIORITY 3 — HEATER / TEMPERATURE PROBLEMS
    # ============================================================
    if temp_state == "LOW" and flow_state == "NORMAL" and water_state == "NORMAL":
        return (
            "LOW BOILER TEMPERATURE — CHECK HEATER / HEATING POWER",
            "WARNING"
        )

    if temp_state == "LOW" and water_state == "HIGH":
        return (
            "LOW TEMPERATURE WITH HIGH WATER INPUT — POSSIBLE HEATER CAPACITY ISSUE",
            "WARNING"
        )

    if temp_state == "HIGH" and flow_state == "NORMAL" and water_state == "NORMAL":
        if thermal_critical or hotspot:
            return (
                "HEATER CONTROL FAULT / OVERHEATING — THERMAL IMAGE CONFIRMS HOT REGION",
                "CRITICAL"
            )
        return (
            "HIGH BOILER TEMPERATURE — CHECK HEATER CONTROL",
            "WARNING"
        )

    if temp_state == "CRITICAL":
        if thermal_critical or hotspot:
            return (
                "CRITICAL OVERHEATING — HEATER CONTROL FAULT",
                "CRITICAL"
            )
        return (
            "CRITICAL PT100 TEMPERATURE — CHECK HEATER IMMEDIATELY",
            "CRITICAL"
        )

    # ============================================================
    # PRIORITY 4 — THERMAL-IMAGE-ONLY / LOCALIZED FAULTS
    # ============================================================
    if temp_state == "NORMAL" and thermal_hot:
        return (
            "LOCALIZED THERMAL HOTSPOT — POSSIBLE FOULING / INSULATION PROBLEM",
            "WARNING"
        )

    if temp_state == "LOW" and thermal_hot:
        return (
            "THERMAL SENSOR DISAGREEMENT — CHECK PT100 MOUNTING AND HOTSPOT",
            "WARNING"
        )

    # ============================================================
    # PRIORITY 5 — OTHER WATER COMBINATIONS
    # ============================================================
    if water_state == "HIGH" and flow_state == "NORMAL":
        return (
            "HIGH TOTAL WATER — CHECK CUMULATIVE WATER INPUT",
            "WARNING"
        )

    if water_state == "HIGH" and flow_state == "LOW":
        return (
            "HIGH TOTAL WATER WITH LOW CURRENT FLOW — CHECK FLOW INTERRUPTION",
            "WARNING"
        )

    return "NORMAL OPERATION", "NORMAL"


def fusion(f, t, thermal_tmax=None, hotspot=False, total_water=None):
    """Return (status, severity, diagnosis, action)."""
    status, severity = sensor_fusion(f, t, thermal_tmax=thermal_tmax, hotspot=hotspot, total_water=total_water)
    states = get_parameter_states(f, t, total_water if total_water is not None else 0.0)
    temp_state = states["temperature"]
    flow_state = states["flow"]
    water_state = states["total_water"]
    
    thermal_text = f"{thermal_tmax:.1f} °C" if thermal_tmax is not None else "Not available"

    if severity == "CRITICAL":
        diagnosis = (
            f"Rule-based sensor fusion detected {status}. "
            f"PT100 is {temp_state} ({t:.2f} °C), YF-S201 flow is {flow_state} "
            f"({f:.2f} L/min), total water is {water_state} ({total_water:.3f} L), "
            f"and Testo 872 Tmax is {thermal_text}. "
            "Multiple sensor conditions agree with the diagnosed fault."
        )
    elif severity == "WARNING":
        diagnosis = (
            f"Rule-based sensor fusion detected {status}. "
            f"PT100 is {temp_state} ({t:.2f} °C), YF-S201 flow is {flow_state} "
            f"({f:.2f} L/min), total water is {water_state} ({total_water:.3f} L), "
            f"and Testo 872 Tmax is {thermal_text}. "
            "The combination of these measurements indicates a condition that should be checked."
        )
    else:
        diagnosis = (
            f"No abnormal combination detected. "
            f"PT100 is {temp_state} ({t:.2f} °C), YF-S201 flow is {flow_state} "
            f"({f:.2f} L/min), total water is {water_state} ({total_water:.3f} L), "
            f"and Testo 872 Tmax is {thermal_text}."
        )

    if "INLET" in status or "PUMP" in status or "FLOW RESTRICTION" in status:
        action = "Inspect inlet valve, check pump power and relay line, clean sediment filter, and check water supply line."
    elif "OVERHEATING" in status or "CRITICAL PT100" in status or "HEATER CONTROL" in status:
        action = "Immediately shut down heating coils, verify thermostat/PT100 calibration, and inspect solid-state relay (SSR)."
    elif "DRY-RUN" in status or "LOW WATER" in status:
        action = "Stop heater immediately to protect tube bundle. Prime water feed pump and refill feed tank."
    elif "HOTSPOT" in status or "FOULING" in status:
        action = "Schedule boiler descaling and clean shell tube surfaces. Inspect insulation around hotspot coordinates."
    elif "LOW BOILER TEMPERATURE" in status or "LOW HEATING" in status:
        action = "Check heating elements for continuity or phase loss. Inspect contactor and temperature controller."
    elif "EXCESSIVE FLOW" in status or "HIGH FLOW" in status:
        action = "Throttle water intake valve and verify pump pressure regulator."
    elif severity == "WARNING":
        action = "Perform routine diagnostic check on indicated sensor channel and inspect physical connections."
    else:
        action = "System operating within normal parameters. Continue standard supervisory monitoring."

    return status, severity, diagnosis, action


# ============================================================
# SIDEBAR NAVIGATION & SETTINGS
# ============================================================
st.sidebar.markdown("## 🧭 Navigation")
st.sidebar.page_link("dashboard.py", label="🏭 Live Monitoring", icon="🏭")
st.sidebar.page_link("pages/2_Testing_Simulation.py", label="🧪 Testing / Simulation", icon="🧪")
st.sidebar.markdown("---")

st.sidebar.header("⚙️ SIMULATION CONFIGURATION")
st.sidebar.caption("Offline Digital Twin Mode: Inject manual sensor readings without physical hardware.")
st.sidebar.markdown("---")
st.sidebar.subheader("🌡️ Temperature Range")
TEMP_LOW = st.sidebar.number_input("Minimum / Low (°C)", value=TEMP_LOW)
TEMP_NORMAL_MAX = st.sidebar.number_input("Normal upper limit (°C)", value=TEMP_NORMAL_MAX)
TEMP_HIGH = st.sidebar.number_input("High / Fault limit (°C)", value=TEMP_HIGH)

st.sidebar.markdown("---")
st.sidebar.subheader("💧 Flow Range")
FLOW_LOW = st.sidebar.number_input("Low-flow limit (L/min)", value=FLOW_LOW)
FLOW_NORMAL_MAX = st.sidebar.number_input("Normal upper limit (L/min)", value=FLOW_NORMAL_MAX)

# ============================================================
# TOP BAR (MATCHES PAGE 1 EXACTLY)
# ============================================================
clock = datetime.now().strftime("%H:%M:%S")

top_col1, top_col2 = st.columns([3.85, 1.15], vertical_alignment="center")

with top_col1:
    st.markdown(f"""
    <div class="topbar">
        <div class="brand">🔥 <span>BOILER AI</span> / CONTROL & DIAGNOSTICS</div>
        <div><span class="sim-tag">🧪 OFFLINE TEST & SIMULATION MODE</span> &nbsp; | &nbsp; <span class="online">● DIGITAL TWIN ONLINE</span> &nbsp; | &nbsp; {clock}</div>
    </div>
    """, unsafe_allow_html=True)

with top_col2:
    cur_theme = st.session_state.get("theme_mode", "dark")
    mode_selection = st.segmented_control(
        "Theme Mode",
        options=["🌙 Dark", "☀️ Light"],
        default="🌙 Dark" if cur_theme == "dark" else "☀️ Light",
        key=f"sim_theme_ctrl_{cur_theme}",
        label_visibility="collapsed"
    )
    if mode_selection:
        chosen = "light" if "Light" in mode_selection else "dark"
        if chosen != cur_theme:
            st.session_state.theme_mode = chosen
            st.rerun()

# ============================================================
# HERO HEADER (MATCHES PAGE 1 EXACTLY)
# ============================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">AI-BASED <span>BOILER</span> PREDICTIVE FAULT DETECTION</div>
    <div class="hero-sub">Offline cyber-physical digital twin • Interactive fault injection • Multi-sensor fusion</div>
    <div class="team-line">MENTOR: <b>N INDHU</b> &nbsp; | &nbsp; MENTEES: <b>RUJITH RS</b> • <b>SANJUSRINITHA T</b> • <b>RHOGETHRAM S T</b></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# PROPER GLOWING SCADA NAVIGATION BAR (MAIN SCREEN)
# ============================================================
nav_c1, nav_c2 = st.columns([1, 1])
with nav_c1:
    st.page_link("dashboard.py", label="🏭 ➔ RETURN TO LIVE MONITORING", icon="🏭")
with nav_c2:
    st.page_link("pages/2_Testing_Simulation.py", label="🧪 TESTING / SIMULATION MODE (ACTIVE)", icon="🧪", disabled=True)

# ============================================================
# FAULT INJECTION & INTERACTIVE BENCHMARK
# ============================================================
st.markdown('<div class="section-title">🎛️ FAULT INJECTION & MANUAL SENSOR BENCHMARK</div>', unsafe_allow_html=True)

st.caption("⚡ Quick Test Presets: Click any preset button to immediately simulate that condition across the entire digital twin.")

p1, p2, p3, p4, p5 = st.columns(5)
with p1:
    if st.button("🟢 NORMAL OPERATION", use_container_width=True):
        st.session_state.sim_temp = 60.0
        st.session_state.sim_flow = 1.50
        st.session_state.sim_total = 2.00
        st.rerun()
with p2:
    if st.button("🟡 LOW INLET FLOW", use_container_width=True):
        st.session_state.sim_temp = 60.0
        st.session_state.sim_flow = 0.15
        st.session_state.sim_total = 2.00
        st.rerun()
with p3:
    if st.button("🔴 OVERHEATING", use_container_width=True):
        st.session_state.sim_temp = 90.0
        st.session_state.sim_flow = 1.50
        st.session_state.sim_total = 2.00
        st.rerun()
with p4:
    if st.button("🚨 DRY-RUN HAZARD", use_container_width=True):
        st.session_state.sim_temp = 92.0
        st.session_state.sim_flow = 0.10
        st.session_state.sim_total = 0.20
        st.rerun()
with p5:
    if st.button("⚠️ SUPPLY FAILURE", use_container_width=True):
        st.session_state.sim_temp = 25.0
        st.session_state.sim_flow = 0.10
        st.session_state.sim_total = 0.15
        st.rerun()

sl1, sl2, sl3 = st.columns(3)
with sl1:
    sim_flow = st.slider("💧 YF-S201 Flow Rate (L/min)", 0.00, 20.00, float(st.session_state.sim_flow), 0.05, key="sl_flow")
    st.session_state.sim_flow = sim_flow
with sl2:
    sim_temp = st.slider("🌡️ PT100 Temperature (°C)", 0.0, 150.0, float(st.session_state.sim_temp), 0.5, key="sl_temp")
    st.session_state.sim_temp = sim_temp
with sl3:
    sim_total = st.slider("💧 Cumulative Total Water (L)", 0.00, 20.00, float(st.session_state.sim_total), 0.05, key="sl_total")
    st.session_state.sim_total = sim_total

# Optional Testo 872 BMT upload
thermal_tmax = None
hotspot = False
bmt_stats = None
if st.session_state.test_bmt is not None:
    bmt_stats = bmt_summary(st.session_state.test_bmt)
    if bmt_stats:
        thermal_tmax = float(bmt_stats.get("tmax")) if bmt_stats.get("tmax") is not None else None
        hotspot = thermal_tmax is not None and thermal_tmax >= TEMP_HIGH

# Execute sensor fusion calculation
status, severity, diagnosis, action = fusion(
    sim_flow,
    sim_temp,
    thermal_tmax=thermal_tmax,
    hotspot=hotspot,
    total_water=sim_total
)

# Append to history
st.session_state.test_history.append({
    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Flow (L/min)": sim_flow,
    "PT100 (°C)": sim_temp,
    "Total Water (L)": sim_total,
    "Testo Tmax (°C)": thermal_tmax,
    "Status": status,
    "Severity": severity
})
st.session_state.test_history = st.session_state.test_history[-1000:]

# ============================================================
# MAIN PROCESS VISUALIZATION (IDENTICAL DIGITAL TWIN TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">LIVE PROCESS OVERVIEW (SIMULATED DIGITAL TWIN)</div>', unsafe_allow_html=True)

left, middle, right = st.columns([1.0, 1.55, 1.0])

with left:
    st.markdown("""
<div class="panel">
<div class="panel-head">SIMULATED INPUTS</div>
<div class="param">
<div class="param-name">YF-S201 FLOW</div>
<div class="param-value">%.2f <span style="font-size:13px;color:#7795a5;">L/min</span></div>
</div>
<div class="param">
<div class="param-name">PT100 TEMPERATURE</div>
<div class="param-value">%.2f <span style="font-size:13px;color:#7795a5;">°C</span></div>
</div>
<div class="param">
<div class="param-name">TOTAL WATER</div>
<div class="param-value">%.3f <span style="font-size:13px;color:#7795a5;">L</span></div>
</div>
</div>
""" % (sim_flow, sim_temp, sim_total), unsafe_allow_html=True)

with middle:
    # Dynamically adjust water height and heater flame based on simulated values
    water_height_pct = min(85, max(15, int((sim_total / 5.0) * 57))) if sim_total is not None else 57
    heater_glow_color = "#ff2200" if sim_temp >= TEMP_HIGH else ("#ff6d1b" if sim_temp >= TEMP_NORMAL_MAX else "#ff9933")
    heater_glow_shadow = f"0 0 25px {heater_glow_color}, 0 0 55px {heater_glow_color}"
    flow_opacity = "1.0" if sim_flow >= FLOW_LOW else "0.3"

    st.markdown(f"""
<div class="panel">
<div class="panel-head">DIGITAL BOILER MODEL (INTERACTIVE)</div>
<div class="boiler-area">
    <div class="pipe-left"></div>
    <div class="pipe-right"></div>
    <div class="flow-arrow" style="opacity:{flow_opacity};">➜</div>
    <div class="boiler-body">
        <div class="dome"></div>
        <div class="thermal-zone"></div>
        <div class="sensor-dot pt100"></div>
        <div class="sensor-dot flow"></div>
        <div class="sensor-dot thermal"></div>
        <div class="water" style="height:{water_height_pct}%;"><div class="wave"></div></div>
        <div class="heater" style="background:{heater_glow_color};box-shadow:{heater_glow_shadow};"></div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

with right:
    # Dynamic Health Index calculation
    if severity == "CRITICAL":
        health_text = "24%"
        health_color = "#ff5555"
        health_deg = 24
    elif severity == "WARNING":
        health_text = "68%"
        health_color = "#ffd66b"
        health_deg = 68
    else:
        health_text = "96%"
        health_color = "#55ffc0"
        health_deg = 96

    health_message = "NORMAL" if severity == "NORMAL" else severity

    st.markdown(f"""
<div class="panel health">
<div class="panel-head">AI HEALTH INDEX</div>
<div class="health-circle" style="background:conic-gradient({health_color} 0 {health_deg}%, #122632 {health_deg}% 100%);">
    <div class="health-inner">{health_text}</div>
</div>
<div style="font-family:Orbitron,sans-serif;font-size:18px;font-weight:700;color:{health_color};">{health_message}</div>
<div style="color:#7894a5;margin-top:7px;font-size:13px;">Sensor-fusion assessment</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# THRESHOLD MONITORING (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">THRESHOLD MONITORING</div>', unsafe_allow_html=True)

t1, t2, t3 = st.columns(3)

with t1:
    temp_state = (
        "CRITICAL" if sim_temp >= TEMP_HIGH
        else "HIGH" if sim_temp > TEMP_NORMAL_MAX
        else "LOW" if sim_temp < TEMP_LOW
        else "NORMAL"
    )
    temp_color = (
        "#ff5555" if temp_state in ("LOW", "CRITICAL")
        else "#ffd66b" if temp_state == "HIGH"
        else "#63ffc0"
    )
    st.markdown(f"""
<div class="panel">
<div class="panel-head">🌡️ TEMPERATURE</div>
<div class="range-box"><div class="range-title">CURRENT SIMULATED</div><div class="range-value">{sim_temp:.2f} °C</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">{TEMP_LOW:.0f} – {TEMP_NORMAL_MAX:.0f} °C</div></div>
<div class="range-box"><div class="range-title">FAULT LIMIT</div><div class="range-value" style="color:{temp_color};">{TEMP_HIGH:.0f} °C • {temp_state}</div></div>
</div>
""", unsafe_allow_html=True)

with t2:
    flow_state = (
        "LOW" if sim_flow < FLOW_LOW
        else "HIGH" if sim_flow > FLOW_NORMAL_MAX
        else "NORMAL"
    )
    flow_color = "#ff7777" if flow_state == "LOW" else "#63ffc0"
    st.markdown(f"""
<div class="panel">
<div class="panel-head">💧 FLOW</div>
<div class="range-box"><div class="range-title">CURRENT SIMULATED</div><div class="range-value">{sim_flow:.2f} L/min</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">{FLOW_LOW:.2f} – {FLOW_NORMAL_MAX:.2f} L/min</div></div>
<div class="range-box"><div class="range-title">STATUS</div><div class="range-value" style="color:{flow_color};">{flow_state}</div></div>
</div>
""", unsafe_allow_html=True)

with t3:
    water_state = (
        "LOW" if sim_total < 0.50
        else "HIGH" if sim_total > 5.00
        else "NORMAL"
    )
    water_color = "#ff5555" if water_state != "NORMAL" else "#63ffc0"
    st.markdown(f"""
<div class="panel">
<div class="panel-head">💧 TOTAL WATER</div>
<div class="range-box"><div class="range-title">CURRENT SIMULATED</div><div class="range-value">{sim_total:.3f} L</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">0.50 – 5.00 L</div></div>
<div class="range-box"><div class="range-title">STATUS</div><div class="range-value" style="color:{water_color};">{water_state}</div></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FUSION ENGINE CHANNELS (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">🧠 SENSOR FUSION & FAULT DIAGNOSTICS</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)

with f1:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">FLOW CHANNEL</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>YF-S201</span><b style="color:{'#63ffc0' if flow_state == 'NORMAL' else '#ff7777'};">{flow_state}</b>
</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>Threshold</span><b>{FLOW_LOW:.2f} L/min</b>
</div>
</div>
""", unsafe_allow_html=True)

with f2:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">TEMPERATURE CHANNEL</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>PT100</span><b style="color:{'#ff5555' if temp_state in ('LOW', 'CRITICAL') else '#ffd66b' if temp_state == 'HIGH' else '#63ffc0'};">{sim_temp:.2f} °C • {temp_state}</b>
</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>Limit</span><b>{TEMP_HIGH:.0f} °C</b>
</div>
</div>
""", unsafe_allow_html=True)

with f3:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">THERMAL CHANNEL • TESTO 872 BMT</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>Testo 872</span><b style="color:{'#63ffc0' if thermal_tmax is not None else '#ffd66b'};">
{'BMT LOADED' if thermal_tmax is not None else 'WAITING'}
</b>
</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>Radiometric Tmax</span><b>{f"{thermal_tmax:.2f} °C" if thermal_tmax is not None else "-- °C"}</b>
</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:9px 0;">
<span>Hotspot</span><b>{f"X={bmt_stats['hot_x']}, Y={bmt_stats['hot_y']}" if bmt_stats else "--"}</b>
</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TESTO 872 RADIOMETRIC BMT INPUT (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">📁 TESTO 872 RADIOMETRIC BMT INPUT</div>', unsafe_allow_html=True)
bu1, bu2 = st.columns([1.2, 1.0])

with bu1:
    bmt_file = st.file_uploader(
        "Upload Testo 872 .BMT file — BMT only",
        type=["bmt"],
        key="testo_bmt_upload_sim",
        help="Upload the BMT captured by the Testo 872 to evaluate radiometric thermal sensor fusion."
    )

    if bmt_file is not None:
        try:
            bmt_res = parse_testo_bmt(bmt_file.getvalue())
            st.session_state.test_bmt = bmt_res
            st.session_state.test_bmt_name = bmt_file.name
            st.success(f"Loaded: {bmt_file.name}")
            st.rerun()
        except Exception as e:
            st.session_state.test_bmt = None
            st.session_state.test_bmt_name = ""
            st.error(f"BMT parsing failed: {e}")

with bu2:
    if st.session_state.test_bmt is not None and bmt_stats:
        st.markdown(f"""
<div class="panel">
<div class="panel-head">RADIOMETRIC RESULTS</div>
<div class="param"><div class="param-name">FILE</div>
<div style="color:#eafaff;font-size:13px;">{st.session_state.test_bmt_name}</div></div>
<div class="param"><div class="param-name">TMAX</div>
<div class="param-value">{bmt_stats["tmax"]:.2f} °C</div></div>
<div class="param"><div class="param-name">TMIN</div>
<div class="param-value">{bmt_stats["tmin"]:.2f} °C</div></div>
<div class="param"><div class="param-name">AVERAGE</div>
<div class="param-value">{bmt_stats["tavg"]:.2f} °C</div></div>
<div class="param"><div class="param-name">HOTSPOT PIXEL</div>
<div style="color:#eafaff;font-size:16px;">X={bmt_stats["hot_x"]}, Y={bmt_stats["hot_y"]}</div></div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">📷 REAL IMAGE + 🌡️ THERMAL IMAGE</div>', unsafe_allow_html=True)
        img1, img2 = st.columns(2)

        with img1:
            st.markdown('<div class="panel"><div class="panel-head">REAL IMAGE (EMBEDDED VISUAL JPEG)</div>', unsafe_allow_html=True)
            vis = st.session_state.test_bmt.get("visual_jpeg")
            if vis:
                try:
                    img = Image.open(io.BytesIO(vis))
                    st.image(img, use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to display visual JPEG: {e}")
            else:
                st.info("No embedded visual image in this BMT.")
            st.markdown("</div>", unsafe_allow_html=True)

        with img2:
            st.markdown('<div class="panel"><div class="panel-head">RADIOMETRIC THERMAL MATRIX HEATMAP</div>', unsafe_allow_html=True)
            try:
                matrix = st.session_state.test_bmt["temperature_matrix"]
                fig, ax = plt.subplots(figsize=(7, 4.5))
                fig.patch.set_facecolor('#040e18')
                ax.set_facecolor('#040e18')
                im = ax.imshow(matrix, cmap="inferno", aspect="auto")
                ax.plot(
                    bmt_stats["hot_x"],
                    bmt_stats["hot_y"],
                    marker="x",
                    color="#00ffff",
                    markersize=12,
                    markeredgewidth=2
                )
                ax.text(
                    bmt_stats["hot_x"] + 5,
                    bmt_stats["hot_y"] + 5,
                    f"Tmax {bmt_stats['tmax']:.1f}°C",
                    fontsize=9,
                    color="#ffffff"
                )
                cbar = fig.colorbar(im, ax=ax)
                cbar.set_label("Temperature (°C)", color="#89a8b8")
                cbar.ax.yaxis.set_tick_params(color="#89a8b8")
                plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color="#89a8b8")
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            except Exception as e:
                st.error(f"Thermal image rendering failed: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

        # Download CSV
        matrix = st.session_state.test_bmt["temperature_matrix"]
        csv_buf = io.StringIO()
        np.savetxt(csv_buf, matrix, delimiter=",", fmt="%.3f")
        st.download_button(
            "⬇️ Download Radiometric Matrix (CSV)",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name="testo_872_sim_matrix.csv",
            mime="text/csv"
        )
    else:
        st.info("Upload a Testo 872 BMT file to include raw radiometric IR matrix evaluation in the simulation.")

# ============================================================
# FAULT ANALYSIS / CONCLUSION (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">🔎 FAULT ANALYSIS — THERMAL IMAGE + SENSOR FUSION</div>', unsafe_allow_html=True)
a1, a2 = st.columns([1.15, 1.0])

with a1:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">WHAT PROBLEM IS DETECTED?</div>
<div style="font-size:25px;font-weight:800;margin:8px 0 12px;color:{'#ff5555' if severity == 'CRITICAL' else ('#ffd66b' if severity == 'WARNING' else '#63ffc0')};">{status}</div>
<div style="color:#b8cbd5;font-size:14px;line-height:1.65;">{diagnosis}</div>
<div style="margin-top:16px;padding:12px;border-radius:10px;background:rgba(2,10,18,.8);border:1px solid rgba(69,231,255,.2);">
    <b style="color:#45e7ff;">Recommended Action:</b><br>
    <span style="color:#eaf8ff;font-size:13.5px;">{action}</span>
</div>
</div>
""", unsafe_allow_html=True)

with a2:
    thermal_str = f"{thermal_tmax:.2f} °C" if thermal_tmax is not None else "Not available"
    st.markdown(f"""
<div class="panel">
<div class="panel-head">FUSION EVIDENCE</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>PT100</span><b>{sim_temp:.2f} °C</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>YF-S201 Flow</span><b>{sim_flow:.2f} L/min</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Total Water</span><b>{sim_total:.3f} L</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Testo 872 Tmax</span><b>{thermal_str}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Temperature State</span><b>{temp_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Flow State</span><b>{flow_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Total Water State</span><b>{water_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Fusion Decision</span><b style="color:{'#ff5555' if severity == 'CRITICAL' else ('#ffd66b' if severity == 'WARNING' else '#63ffc0')};">{severity}</b></div>
</div>
""", unsafe_allow_html=True)

if severity == "CRITICAL":
    st.error(f"🚨 CRITICAL FAULT: {status}")
    st.markdown(warning_beep_html(), unsafe_allow_html=True)
    st.markdown('<div style="font-weight:700;font-size:15px;margin-top:-8px;">🔊 WARNING SOUND: CRITICAL ALARM BEEP</div>', unsafe_allow_html=True)
elif severity == "WARNING":
    st.warning(f"⚠️ WARNING: {status}")
    st.markdown(warning_beep_html(), unsafe_allow_html=True)
    st.markdown(f'<div style="font-weight:700;font-size:15px;margin-top:-8px;">🔊 WARNING SOUND: {status}</div>', unsafe_allow_html=True)
else:
    st.success("✅ SYSTEM STATUS: NORMAL OPERATION")

# ============================================================
# SIMULATION PROCESS TRENDS (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown('<div class="section-title">📈 SIMULATION PROCESS TRENDS</div>', unsafe_allow_html=True)

df_hist = pd.DataFrame(st.session_state.test_history)

if len(df_hist) >= 2:
    x = pd.to_datetime(df_hist["Time"])
    g1, g2 = st.columns(2)

    is_dark = (st.session_state.get("theme_mode", "dark") == "dark")
    with g1:
        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#040e18' if is_dark else '#ffffff')
        ax.set_facecolor('#040e18' if is_dark else '#f8fafc')
        ax.plot(x, df_hist["PT100 (°C)"], color="#ff7b26" if is_dark else "#d97706", linewidth=2, label="PT100")
        ax.axhline(TEMP_NORMAL_MAX, color="#ffd166" if is_dark else "#b45309", linestyle="--", label="Normal limit")
        ax.axhline(TEMP_HIGH, color="#ff6868" if is_dark else "#dc2626", linestyle="--", label="Fault limit")
        ax.set_title("Simulated Temperature", color="#9eefff" if is_dark else "#082138", fontweight='bold')
        ax.set_ylabel("°C", color="#89a8b8" if is_dark else "#486581")
        ax.tick_params(colors="#89a8b8" if is_dark else "#486581")
        ax.grid(True, color="#122533" if is_dark else "#cbd5e1", linestyle=":")
        for spine in ax.spines.values():
            spine.set_color('#1e3a5f' if is_dark else '#cbd5e1')
        ax.legend(facecolor='#030d17' if is_dark else '#ffffff', edgecolor='#4bdcff' if is_dark else '#cbd5e1', labelcolor='#ffffff' if is_dark else '#082138', fontsize=8)
        plt.xticks(rotation=30)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with g2:
        fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#040e18' if is_dark else '#ffffff')
        ax.set_facecolor('#040e18' if is_dark else '#f8fafc')
        ax.plot(x, df_hist["Flow (L/min)"], color="#46e7ff" if is_dark else "#0284c7", linewidth=2, label="YF-S201")
        ax.axhline(FLOW_LOW, color="#ff6868" if is_dark else "#dc2626", linestyle="--", label="Low-flow limit")
        ax.set_title("Simulated Water Flow", color="#9eefff" if is_dark else "#082138", fontweight='bold')
        ax.set_ylabel("L/min", color="#89a8b8" if is_dark else "#486581")
        ax.tick_params(colors="#89a8b8" if is_dark else "#486581")
        ax.grid(True, color="#122533" if is_dark else "#cbd5e1", linestyle=":")
        for spine in ax.spines.values():
            spine.set_color('#1e3a5f' if is_dark else '#cbd5e1')
        ax.legend(facecolor='#030d17' if is_dark else '#ffffff', edgecolor='#4bdcff' if is_dark else '#cbd5e1', labelcolor='#ffffff' if is_dark else '#082138', fontsize=8)
        plt.xticks(rotation=30)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
else:
    st.info("Collecting simulated sensor history points...")

# ============================================================
# ENGINEERING DATA (IDENTICAL TO PAGE 1)
# ============================================================
with st.expander("📋 Engineering Data / Simulation Log"):
    st.dataframe(df_hist.tail(30), use_container_width=True)
    st.download_button(
        "⬇️ Download Simulation Log (CSV)",
        data=df_hist.to_csv(index=False).encode("utf-8"),
        file_name="boiler_simulation_log.csv",
        mime="text/csv"
    )

# ============================================================
# FOOTER (IDENTICAL TO PAGE 1)
# ============================================================
st.markdown("""
<div class="footer">
AI-BASED BOILER PREDICTIVE FAULT DETECTION<br>
SENSOR FUSION • PT100 • YF-S201 • TESTO 872 THERMAL IMAGING<br><br>
TESTING & SIMULATION ENVIRONMENT &nbsp; | &nbsp; MENTOR: N INDHU &nbsp; | &nbsp; RUJITH RS • SANJUSRINITHA T • RHOGETHRAM S T
</div>
""", unsafe_allow_html=True)
