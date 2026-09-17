import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
import io
import base64
import struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

# ============================================================
# AI-BASED BOILER PREDICTIVE FAULT DETECTION
# Professional SCADA / HMI Dashboard
# ============================================================

st.set_page_config(
    page_title="AI Boiler Predictive Fault Detection",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DEFAULT CONFIGURATION
# ============================================================
STM32_IP = "192.168.137.221"

# Prototype threshold ranges - calibrate experimentally.
TEMP_LOW = 30.0
TEMP_NORMAL_MAX = 75.0
TEMP_HIGH = 85.0

FLOW_LOW = 0.30
FLOW_NORMAL_MAX = 5.00


if "history" not in st.session_state:
    st.session_state.history = []

if "boot_done" not in st.session_state:
    st.session_state.boot_done = False

if "bmt_result" not in st.session_state:
    st.session_state.bmt_result = None

if "bmt_name" not in st.session_state:
    st.session_state.bmt_name = ""

if "thermography_video_name" not in st.session_state:
    st.session_state.thermography_video_name = ""

# ============================================================
# PROFESSIONAL UI
# ============================================================
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(circle at 50% 0%, rgba(0, 190, 255, .10), transparent 30%),
        linear-gradient(135deg, #02060c 0%, #06111b 52%, #02050a 100%);
    color: #eaf8ff;
}

header {visibility:hidden;}
footer {visibility:hidden;}
#MainMenu {visibility:hidden;}

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
    margin-bottom:14px;
    border:1px solid rgba(75,220,255,.18);
    border-radius:12px;
    background:rgba(3,12,21,.92);
    box-shadow:0 8px 30px rgba(0,0,0,.25);
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
}

.panel {
    background:linear-gradient(145deg,rgba(8,23,37,.96),rgba(3,10,18,.96));
    border:1px solid rgba(95,190,220,.14);
    border-radius:15px;
    padding:17px;
    box-shadow:0 9px 30px rgba(0,0,0,.24);
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

.footer {
    text-align:center;
    color:#587284;
    margin-top:25px;
    padding-top:18px;
    border-top:1px solid rgba(100,160,180,.10);
    font-size:12px;
    letter-spacing:1px;
}

@keyframes fadein {from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes wave {to{transform:translateX(45px)}}
@keyframes heater {from{transform:scaleX(.88);opacity:.65}to{transform:scaleX(1.08);opacity:1}}
@keyframes thermal {from{transform:scale(.82);opacity:.45}to{transform:scale(1.16);opacity:1}}
@keyframes pulse {50%{transform:scale(1.55);opacity:.62}}
@keyframes moveflow {from{transform:translateX(0);opacity:0}15%{opacity:1}80%{opacity:1}to{transform:translateX(175px);opacity:0}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# BOOT SCREEN
# ============================================================
if not st.session_state.boot_done:
    st.markdown("""
<div style="height:72vh;display:flex;align-items:center;justify-content:center;text-align:center;">
<div>
<div style="font-size:76px;filter:drop-shadow(0 0 25px rgba(255,90,20,.7));animation:pulse 1.5s infinite;">🔥</div>
<div style="font-family:Orbitron,sans-serif;font-size:38px;font-weight:800;margin-top:18px;">
AI-BASED <span style="color:#45e7ff;">BOILER</span><br>PREDICTIVE FAULT DETECTION
</div>
<div style="color:#7f9aaa;margin-top:12px;letter-spacing:2px;">
SENSOR FUSION • THERMAL IMAGING • INTELLIGENT MONITORING
</div>
<div style="color:#63ffc0;margin-top:28px;font-weight:700;letter-spacing:2px;">
● SYSTEM INITIALIZATION...
</div>
<div style="color:#718b9b;margin-top:18px;font-size:13px;">
MENTOR: N INDHU &nbsp; | &nbsp; RUJITH RS • SANJUSRINITHA T • RHOGETHRAM S T
</div>
</div>
</div>
""", unsafe_allow_html=True)
    time.sleep(3)
    st.session_state.boot_done = True
    st.rerun()

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.header("⚙️ SYSTEM CONFIGURATION")

STM32_IP = st.sidebar.text_input("STM32 IP Address", value=STM32_IP)

st.sidebar.markdown("---")
st.sidebar.subheader("🌡️ Temperature Range")

TEMP_LOW = st.sidebar.number_input("Minimum / Low (°C)", value=TEMP_LOW)
TEMP_NORMAL_MAX = st.sidebar.number_input("Normal upper limit (°C)", value=TEMP_NORMAL_MAX)
TEMP_HIGH = st.sidebar.number_input("High / Fault limit (°C)", value=TEMP_HIGH)

st.sidebar.markdown("---")
st.sidebar.subheader("💧 Flow Range")

FLOW_LOW = st.sidebar.number_input("Low-flow limit (L/min)", value=FLOW_LOW)
FLOW_NORMAL_MAX = st.sidebar.number_input("Normal upper limit (L/min)", value=FLOW_NORMAL_MAX)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)


# ============================================================
# TESTO BMT RADIOMETRIC PARSER
# Based on Testo's public read_bmt sample for 865/868/871/872/883.
# A BMT contains radiometric temperature data; JPEG does not.
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

    # Testo's public sample maps the IR CV_16U matrix to -101..1001 °C.
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
        # Most current Testo BMTs use little-endian data; if the file says
        # otherwise, matrix parsing below is handled by the supplied endian.
        if node["type"].lower().find("cvmat") >= 0:
            return _bmt_parse_mat(f, node["size"], endian, node["name"].lower() == "ir")

        # Re-run scalar parsing with the file endianness by temporarily using
        # the same scalar helpers through a dedicated local implementation.
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
    f.read(1)  # separator used by Testo's BMT layout

    parsed = _bmt_parse_tree(f, root, endian)

    # Recursively find the IR matrix and embedded visual JPEG.
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
        "rows": int(a.shape[0]),
        "cols": int(a.shape[1]),
    }



# ============================================================
# WARNING SOUND
# ============================================================
def warning_beep_html():
    """
    Generate a short repeating warning beep.
    The browser may block autoplay until the user interacts with the page.
    """
    import math
    import wave

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
            # Smooth envelope to avoid clicks.
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

# ============================================================
# STM32 DATA
# ============================================================
def get_data():
    try:
        rSTMonse = requests.get(
            f"http://{STM32_IP}/data",
            timeout=2
        )
        rSTMonse.raise_for_status()
        d = rSTMonse.json()
        return (
            float(d.get("flow", 0)),
            float(d.get("temperature", 0)),
            float(d.get("totalLiters", 0)),
            True
        )
    except Exception:
        return 0.0, 0.0, 0.0, False

flow, temp, total, connected = get_data()

# ============================================================
# SENSOR FUSION
# ============================================================

def boiler_status(value, minimum, maximum, low_label, high_label):
    """Return LOW, NORMAL, or HIGH status for a boiler parameter."""
    if value < minimum:
        return low_label
    if value > maximum:
        return high_label
    return "NORMAL"

def sensor_fusion(f, t, thermal_tmax=None, hotspot=False, total_water=None):
    """
    Rule-based boiler fault diagnosis using:
      PT100 temperature + YF-S201 flow + cumulative total water + Testo 872 Tmax.

    The important point is that a LOW total-water value by itself is not
    automatically called a boiler fault. The combination of process
    conditions determines the most likely problem.
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

    # High/critical temperature + low flow + low cumulative water:
    # likely inlet/pump failure, restriction, or dry-run tendency.
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

    # High/critical process temperature + low flow:
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

    # High/critical temperature + low water:
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

    # This is the user's requested example:
    # temperature NORMAL + flow LOW + total water LOW
    if temp_state == "NORMAL" and flow_state == "LOW" and water_state == "LOW":
        return (
            "INLET FLOW / PUMP PROBLEM — LOW FLOW AND LOW TOTAL WATER",
            "WARNING"
        )

    # Normal temperature + low flow + normal water:
    if temp_state == "NORMAL" and flow_state == "LOW" and water_state == "NORMAL":
        return (
            "LOW INLET FLOW — CHECK PUMP, INLET VALVE OR FLOW RESTRICTION",
            "WARNING"
        )

    # Low temperature + low flow + low water:
    if temp_state == "LOW" and flow_state == "LOW" and water_state == "LOW":
        return (
            "WATER SUPPLY / PUMP NOT DELIVERING — LOW FLOW AND LOW WATER",
            "WARNING"
        )

    # Low temperature + low flow + normal water:
    if temp_state == "LOW" and flow_state == "LOW" and water_state == "NORMAL":
        return (
            "LOW HEATING / LOW INLET FLOW — CHECK HEATER AND PUMP",
            "WARNING"
        )

    # Normal temperature + normal flow + low cumulative water:
    # This can simply mean insufficient water has been accumulated so far.
    if temp_state == "NORMAL" and flow_state == "NORMAL" and water_state == "LOW":
        return (
            "LOW TOTAL WATER — INSUFFICIENT CUMULATIVE WATER INPUT",
            "WARNING"
        )

    # High flow conditions.
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

    # PT100 normal but Testo sees a high/localized surface temperature:
    # useful for detecting a local hotspot that the point sensor misses.
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

    # No abnormal process state.
    return "NORMAL OPERATION", "NORMAL"


def get_parameter_states(f, t, total_water):
    """Return the individual process states used by the fusion rules."""
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
    return temp_state, flow_state, water_state

# BMT thermal state
thermal_tmax = None
thermal_hotspot = False
bmt_result = st.session_state.get("bmt_result")
if bmt_result is not None:
    try:
        bmt_stats = bmt_summary(bmt_result)
        thermal_tmax = bmt_stats["tmax"]
        thermal_hotspot = thermal_tmax >= TEMP_HIGH
    except Exception:
        bmt_stats = None

status, severity = sensor_fusion(flow, temp, thermal_tmax, thermal_hotspot, total)

# ============================================================
# TOP BAR
# ============================================================
clock = datetime.now().strftime("%H:%M:%S")
connection = (
    '<span class="online">● SYSTEM ONLINE</span>'
    if connected else
    '<span class="offline">● STM32 OFFLINE</span>'
)

st.markdown(f"""
<div class="topbar">
    <div class="brand">🔥 <span>BOILER AI</span> / CONTROL & DIAGNOSTICS</div>
    <div>{connection} &nbsp; | &nbsp; {clock}</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
    <div class="hero-title">AI-BASED <span>BOILER</span> PREDICTIVE FAULT DETECTION</div>
    <div class="hero-sub">Professional process monitoring • Thermal image analysis • Sensor fusion</div>
    <div class="team-line">MENTOR: <b>N INDHU</b> &nbsp; | &nbsp; MENTEES: <b>RUJITH RS</b> • <b>SANJUSRINITHA T</b> • <b>RHOGETHRAM S T</b></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# MAIN PROCESS VISUALIZATION
# ============================================================
st.markdown('<div class="section-title">LIVE PROCESS OVERVIEW</div>', unsafe_allow_html=True)

left, middle, right = st.columns([1.0, 1.55, 1.0])

with left:
    st.markdown("""
<div class="panel">
<div class="panel-head">PROCESS INPUTS</div>
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
""" % (flow, temp, total), unsafe_allow_html=True)

with middle:
    st.markdown("""
<div class="panel">
<div class="panel-head">DIGITAL BOILER MODEL</div>
<div class="boiler-area">
    <div class="pipe-left"></div>
    <div class="pipe-right"></div>
    <div class="flow-arrow">➜</div>
    <div class="boiler-body">
        <div class="dome"></div>
        <div class="thermal-zone"></div>
        <div class="sensor-dot pt100"></div>
        <div class="sensor-dot flow"></div>
        <div class="sensor-dot thermal"></div>
        <div class="water"><div class="wave"></div></div>
        <div class="heater"></div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)

with right:
    health_text = "94%"
    health_message = "NORMAL" if severity == "NORMAL" else severity

    st.markdown(f"""
<div class="panel health">
<div class="panel-head">AI HEALTH INDEX</div>
<div class="health-circle"><div class="health-inner">{health_text}</div></div>
<div style="font-family:Orbitron,sans-serif;font-size:18px;font-weight:700;">{health_message}</div>
<div style="color:#7894a5;margin-top:7px;font-size:13px;">Sensor-fusion assessment</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# THRESHOLD MONITOR
# ============================================================
st.markdown('<div class="section-title">THRESHOLD MONITORING</div>', unsafe_allow_html=True)

t1, t2, t3 = st.columns(3)

with t1:
    temp_state = (
        "CRITICAL" if temp >= TEMP_HIGH
        else "HIGH" if temp > TEMP_NORMAL_MAX
        else "LOW" if temp < TEMP_LOW
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
<div class="range-box"><div class="range-title">CURRENT</div><div class="range-value">{temp:.2f} °C</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">{TEMP_LOW:.0f} – {TEMP_NORMAL_MAX:.0f} °C</div></div>
<div class="range-box"><div class="range-title">FAULT LIMIT</div><div class="range-value" style="color:{temp_color};">{TEMP_HIGH:.0f} °C • {temp_state}</div></div>
</div>
""", unsafe_allow_html=True)

with t2:
    flow_state = (
        "LOW" if flow < FLOW_LOW
        else "HIGH" if flow > FLOW_NORMAL_MAX
        else "NORMAL"
    )
    flow_color = "#ff7777" if flow_state == "LOW" else "#63ffc0"
    st.markdown(f"""
<div class="panel">
<div class="panel-head">💧 FLOW</div>
<div class="range-box"><div class="range-title">CURRENT</div><div class="range-value">{flow:.2f} L/min</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">{FLOW_LOW:.2f} – {FLOW_NORMAL_MAX:.2f} L/min</div></div>
<div class="range-box"><div class="range-title">STATUS</div><div class="range-value" style="color:{flow_color};">{flow_state}</div></div>
</div>
""", unsafe_allow_html=True)

with t3:
    water_state = (
        "LOW" if total < 0.50
        else "HIGH" if total > 5.00
        else "NORMAL"
    )
    water_color = "#ff5555" if water_state != "NORMAL" else "#63ffc0"
    st.markdown(f"""
<div class="panel">
<div class="panel-head">💧 TOTAL WATER</div>
<div class="range-box"><div class="range-title">CURRENT TOTAL</div><div class="range-value">{total:.3f} L</div></div>
<div class="range-box"><div class="range-title">OPERATING RANGE</div><div class="range-value">0.50 – 5.00 L</div></div>
<div class="range-box"><div class="range-title">STATUS</div><div class="range-value" style="color:{water_color};">{water_state}</div></div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FUSION ENGINE
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
<span>PT100</span><b style="color:{'#ff5555' if temp_state in ('LOW', 'CRITICAL') else '#ffd66b' if temp_state == 'HIGH' else '#63ffc0'};">{temp:.2f} °C • {temp_state}</b>
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
<span>Hotspot</span><b>{f"X={bmt_stats['hot_x']}, Y={bmt_stats['hot_y']}" if bmt_result is not None and bmt_stats else "--"}</b>
</div>
</div>
""", unsafe_allow_html=True)

# BMT uploader sits directly under the fusion channel.
st.markdown('<div class="section-title">📁 TESTO 872 RADIOMETRIC BMT INPUT</div>', unsafe_allow_html=True)
bu1, bu2 = st.columns([1.2, 1.0])

with bu1:
    bmt_file = st.file_uploader(
        "Upload Testo 872 .BMT file — BMT only",
        type=["bmt"],
        key="testo_bmt_upload",
        help="Upload the BMT captured by the Testo 872. The dashboard reads the radiometric temperature matrix from the BMT."
    )

    if bmt_file is not None:
        try:
            result = parse_testo_bmt(bmt_file.getvalue())
            stats = bmt_summary(result)
            st.session_state.bmt_result = result
            st.session_state.bmt_name = bmt_file.name
            st.success(f"Loaded: {bmt_file.name}")
        except Exception as e:
            st.session_state.bmt_result = None
            st.session_state.bmt_name = ""
            st.error(f"BMT parsing failed: {e}")

with bu2:
    if st.session_state.bmt_result is not None:
        result = st.session_state.bmt_result
        stats = bmt_summary(result)

        st.markdown(f"""
<div class="panel">
<div class="panel-head">RADIOMETRIC RESULTS</div>
<div class="param"><div class="param-name">FILE</div>
<div style="color:#eafaff;font-size:13px;">{st.session_state.bmt_name}</div></div>
<div class="param"><div class="param-name">TMAX</div>
<div class="param-value">{stats["tmax"]:.2f} °C</div></div>
<div class="param"><div class="param-name">TMIN</div>
<div class="param-value">{stats["tmin"]:.2f} °C</div></div>
<div class="param"><div class="param-name">AVERAGE</div>
<div class="param-value">{stats["tavg"]:.2f} °C</div></div>
<div class="param"><div class="param-name">HOTSPOT PIXEL</div>
<div style="color:#eafaff;font-size:16px;">X={stats["hot_x"]}, Y={stats["hot_y"]}</div></div>
</div>
""", unsafe_allow_html=True)

        # ============================================================
        # DUAL IMAGE DISPLAY
        # 1) Real/visible image embedded in the BMT
        # 2) Radiometric thermal image generated from the BMT IR matrix
        # ============================================================
        st.markdown(
            '<div class="section-title">📷 REAL IMAGE + 🌡️ THERMAL IMAGE</div>',
            unsafe_allow_html=True
        )

        img1, img2 = st.columns(2)

        with img1:
            st.markdown(
                '<div class="panel"><div class="panel-head">📷 REAL / VISIBLE IMAGE</div>',
                unsafe_allow_html=True
            )
            if result.get("visual_jpeg"):
                try:
                    vis = Image.open(io.BytesIO(result["visual_jpeg"]))
                    st.image(
                        vis,
                        caption="Testo 872 visible image from BMT",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"Visible image could not be displayed: {e}")
            else:
                st.info(
                    "This BMT does not contain an embedded visible JPEG. "
                    "The radiometric thermal image is still available."
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with img2:
            st.markdown(
                '<div class="panel"><div class="panel-head">🌡️ RADIOMETRIC THERMAL IMAGE</div>',
                unsafe_allow_html=True
            )
            try:
                thermal_matrix = np.asarray(
                    result["temperature_matrix"], dtype=float
                )

                fig, ax = plt.subplots(figsize=(6, 4.5))
                im = ax.imshow(
                    thermal_matrix,
                    cmap="inferno",
                    interpolation="nearest"
                )
                ax.set_title(
                    f"Testo 872 Thermal Map | Tmax {stats['tmax']:.2f} °C"
                )
                ax.set_xlabel("Pixel X")
                ax.set_ylabel("Pixel Y")

                # Mark the hottest pixel.
                ax.plot(
                    stats["hot_x"],
                    stats["hot_y"],
                    marker="x",
                    markersize=12,
                    markeredgewidth=2
                )
                ax.text(
                    stats["hot_x"] + 5,
                    stats["hot_y"] + 5,
                    f"Tmax {stats['tmax']:.1f}°C",
                    fontsize=9
                )

                cbar = fig.colorbar(im, ax=ax)
                cbar.set_label("Temperature (°C)")
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                st.caption(
                    "Thermal image is reconstructed directly from the "
                    "radiometric temperature matrix stored in the BMT."
                )
            except Exception as e:
                st.error(f"Thermal image generation failed: {e}")

            st.markdown("</div>", unsafe_allow_html=True)

        # Radiometric matrix download
        matrix = result["temperature_matrix"]
        csv_buf = io.StringIO()
        np.savetxt(csv_buf, matrix, delimiter=",", fmt="%.3f")
        st.download_button(
            "⬇️ Download Radiometric Temperature Matrix (CSV)",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name="testo_872_radiometric_temperature.csv",
            mime="text/csv"
        )
    else:
        st.info("Upload a Testo 872 BMT file to obtain the real radiometric Tmax, Tmin and average temperature.")



# ============================================================
# THERMOGRAPHY VIDEO INPUT
# ============================================================
st.markdown(
    '<div class="section-title">🎥 THERMOGRAPHY VIDEO INPUT</div>',
    unsafe_allow_html=True
)

v1, v2 = st.columns([1.05, 1.0])

with v1:
    thermo_video = st.file_uploader(
        "Upload thermography video",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="thermography_video_upload",
        help="Upload a recorded thermography/thermal video for visual review."
    )

    if thermo_video is not None:
        video_bytes = thermo_video.getvalue()
        st.session_state.thermography_video_name = thermo_video.name
        st.markdown(
            """
            <div style="max-width:560px;margin:0 auto;">
            """,
            unsafe_allow_html=True
        )
        st.video(video_bytes)
        st.markdown("</div>", unsafe_allow_html=True)
        st.success(f"Thermography video loaded: {thermo_video.name}")

with v2:
    if thermo_video is not None:
        st.markdown(
            f"""
            <div class="panel">
            <div class="panel-head">THERMOGRAPHY VIDEO STATUS</div>
            <div class="param">
                <div class="param-name">FILE</div>
                <div style="color:#eafaff;font-size:13px;">{thermo_video.name}</div>
            </div>
            <div class="param">
                <div class="param-name">INPUT TYPE</div>
                <div class="param-value">THERMOGRAPHY VIDEO</div>
            </div>
            <div class="param">
                <div class="param-name">USE</div>
                <div style="color:#b8cbd5;font-size:14px;line-height:1.5;">
                    Visual thermal-video review alongside the Testo 872 BMT
                    radiometric analysis and STM32 sensor-fusion results.
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.info(
            "The uploaded video is displayed for thermography review. "
            "The fault diagnosis continues to use PT100, YF-S201, total water "
            "and radiometric Testo 872 BMT data."
        )
    else:
        st.markdown(
            """
            <div class="panel">
            <div class="panel-head">THERMOGRAPHY VIDEO STATUS</div>
            <div style="color:#8faabb;padding:20px 0;">
                No thermography video uploaded.
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# FAULT ANALYSIS / SENSOR FUSION CONCLUSION
# ============================================================
thermal_text = f"{thermal_tmax:.2f} °C" if thermal_tmax is not None else "Not available"

if thermal_tmax is None:
    analysis_text = (
        "Thermal evidence is not yet available. Upload a Testo 872 BMT file to combine "
        "the radiometric thermal image with the PT100 and YF-S201 measurements."
    )
eltemp_state, flow_state, water_state = get_parameter_states(flow, temp, total)

if thermal_tmax is None:
    thermal_for_text = "not available"
else:
    thermal_for_text = f"{thermal_tmax:.2f} °C"

if severity == "CRITICAL":
    analysis_text = (
        f"Rule-based sensor fusion detected {status}. "
        f"PT100 is {temp_state} ({temp:.2f} °C), YF-S201 flow is {flow_state} "
        f"({flow:.2f} L/min), total water is {water_state} ({total:.3f} L), "
        f"and Testo 872 Tmax is {thermal_for_text}. "
        "Multiple sensor conditions agree with the diagnosed fault."
    )
elif severity == "WARNING":
    analysis_text = (
        f"Rule-based sensor fusion detected {status}. "
        f"PT100 is {temp_state} ({temp:.2f} °C), YF-S201 flow is {flow_state} "
        f"({flow:.2f} L/min), total water is {water_state} ({total:.3f} L), "
        f"and Testo 872 Tmax is {thermal_for_text}. "
        "The combination of these measurements indicates a condition that should be checked."
    )
else:
    analysis_text = (
        f"No abnormal combination detected. "
        f"PT100 is {temp_state} ({temp:.2f} °C), YF-S201 flow is {flow_state} "
        f"({flow:.2f} L/min), total water is {water_state} ({total:.3f} L), "
        f"and Testo 872 Tmax is {thermal_for_text}."
    )

st.markdown('<div class="section-title">🔎 FAULT ANALYSIS — THERMAL IMAGE + SENSOR FUSION</div>', unsafe_allow_html=True)
a1, a2 = st.columns([1.15, 1.0])

with a1:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">WHAT PROBLEM IS DETECTED?</div>
<div style="font-size:25px;font-weight:800;margin:8px 0 12px;">{status}</div>
<div style="color:#b8cbd5;font-size:14px;line-height:1.65;">{analysis_text}</div>
</div>
""", unsafe_allow_html=True)

with a2:
    st.markdown(f"""
<div class="panel">
<div class="panel-head">FUSION EVIDENCE</div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>PT100</span><b>{temp:.2f} °C</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>YF-S201 Flow</span><b>{flow:.2f} L/min</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Total Water</span><b>{total:.3f} L</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Testo 872 Tmax</span><b>{thermal_text}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Temperature State</span><b>{temp_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Flow State</span><b>{flow_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Total Water State</span><b>{water_state}</b></div>
<div class="fusion-item" style="display:flex;justify-content:space-between;padding:8px 0;"><span>Fusion Decision</span><b>{severity}</b></div>
</div>
""", unsafe_allow_html=True)



if severity == "CRITICAL":
    st.error(f"🚨 CRITICAL FAULT: {status}")
    st.markdown(warning_beep_html(), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-weight:700;font-size:15px;margin-top:-8px;">'
        '🔊 WARNING SOUND: CRITICAL ALARM BEEP'
        '</div>',
        unsafe_allow_html=True
    )
elif severity == "WARNING":
    st.warning(f"⚠️ WARNING: {status}")
    st.markdown(warning_beep_html(), unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-weight:700;font-size:15px;margin-top:-8px;">'
        f'🔊 WARNING SOUND: {status}'
        f'</div>',
        unsafe_allow_html=True
    )
else:
    st.success("✅ SYSTEM STATUS: NORMAL OPERATION")

st.info(
    "Testo 872 BMT is the thermal input. The BMT contains the radiometric temperature data; "
    "the dashboard uses its IR matrix to calculate Tmax, Tmin, average temperature and hotspot position."
)

# ============================================================
# DATA LOG
# ============================================================
st.session_state.history.append({
    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Flow (L/min)": flow,
    "PT100 (°C)": temp,
    "Total Water (L)": total,
    "Testo Tmax (°C)": thermal_tmax,
    "Status": status,
    "Severity": severity
})
st.session_state.history = st.session_state.history[-1000:]

df = pd.DataFrame(st.session_state.history)

# ============================================================
# TREND CHARTS
# ============================================================
st.markdown('<div class="section-title">📈 REAL-TIME PROCESS TRENDS</div>', unsafe_allow_html=True)

if len(df) >= 2:
    x = pd.to_datetime(df["Time"])
    g1, g2 = st.columns(2)

    with g1:
        fig, ax = plt.subplots()
        ax.plot(x, df["PT100 (°C)"], label="PT100")
        ax.axhline(TEMP_NORMAL_MAX, linestyle="--", label="Normal upper limit")
        ax.axhline(TEMP_HIGH, linestyle="--", label="Fault limit")
        ax.set_title("Boiler Temperature")
        ax.set_ylabel("°C")
        ax.grid(True)
        ax.legend()
        plt.xticks(rotation=30)
        st.pyplot(fig)

    with g2:
        fig, ax = plt.subplots()
        ax.plot(x, df["Flow (L/min)"], label="YF-S201")
        ax.axhline(FLOW_LOW, linestyle="--", label="Low-flow limit")
        ax.set_title("Water Flow")
        ax.set_ylabel("L/min")
        ax.grid(True)
        ax.legend()
        plt.xticks(rotation=30)
        st.pyplot(fig)
else:
    st.info("Collecting live sensor history...")

# ============================================================
# ENGINEERING DATA
# ============================================================
with st.expander("📋 Engineering Data / CSV Report"):
    st.dataframe(df.tail(30), use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Sensor Log",
        data=csv_data,
        file_name="boiler_sensor_fusion_log.csv",
        mime="text/csv"
    )

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
AI-BASED BOILER PREDICTIVE FAULT DETECTION<br>
SENSOR FUSION • PT100 • YF-S201 • TESTO 872 THERMAL IMAGING<br><br>
MENTOR: N INDHU &nbsp; | &nbsp; RUJITH RS • SANJUSRINITHA T • RHOGETHRAM S T
</div>
""", unsafe_allow_html=True)

# ============================================================
# REFRESH
# ============================================================
if auto_refresh:
    time.sleep(2)
    st.rerun()
