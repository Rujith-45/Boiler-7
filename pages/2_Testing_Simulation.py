import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import io
import struct
import xml.etree.ElementTree as ET

# ============================================================
# PAGE CONFIGURATION (MUST BE FIRST STREAMLIT CALL)
# ============================================================
st.set_page_config(
    page_title="Boiler AI - Testing / Simulation",
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


def boiler_status(value, minimum, maximum, low_label, high_label):
    """Return LOW, NORMAL, or HIGH status for a boiler parameter."""
    if value < minimum:
        return low_label
    if value > maximum:
        return high_label
    return "NORMAL"


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
    """
    Simulated sensor fusion runner returning (status, severity, diagnosis, action).
    """
    status, severity = sensor_fusion(f, t, thermal_tmax=thermal_tmax, hotspot=hotspot, total_water=total_water)
    states = get_parameter_states(f, t, total_water if total_water is not None else 0.0)
    temp_state = states["temperature"]
    flow_state = states["flow"]
    water_state = states["total_water"]
    
    thermal_text = f"{thermal_tmax:.1f} °C" if thermal_tmax is not None else "No radiometric BMT uploaded"

    # Detailed diagnosis description
    if severity == "CRITICAL":
        diagnosis = (
            f"Rule-based sensor fusion identified critical boiler hazard: {status}. "
            f"PT100 is {temp_state} ({t:.1f} °C), flow is {flow_state} ({f:.2f} L/min), "
            f"total water is {water_state} ({total_water:.2f} L), and Testo 872 Tmax is {thermal_text}."
        )
    elif severity == "WARNING":
        diagnosis = (
            f"Process anomaly detected: {status}. "
            f"PT100 is {temp_state} ({t:.1f} °C), flow is {flow_state} ({f:.2f} L/min), "
            f"total water is {water_state} ({total_water:.2f} L), and Testo 872 Tmax is {thermal_text}."
        )
    else:
        diagnosis = (
            f"All monitored parameters are within safe operating limits. "
            f"Temperature ({t:.1f} °C), flow ({f:.2f} L/min), and cumulative volume ({total_water:.2f} L) are normal."
        )

    # Specific actionable engineering recommendations
    if "INLET" in status or "PUMP" in status or "FLOW RESTRICTION" in status:
        action = "Check inlet solenoid valve, inspect pump electrical feed and relay, clear sediment from YF-S201 sensor, and confirm water feed pressure."
    elif "OVERHEATING" in status or "CRITICAL PT100" in status or "HEATER CONTROL" in status:
        action = "Immediately disengage boiler heating coils, activate emergency cooling/venting, verify thermocouple/PT100 calibration, and inspect solid-state relay (SSR)."
    elif "DRY-RUN" in status or "LOW WATER" in status:
        action = "Halt boiler heating immediately to prevent tube burnout. Verify feed tank water level and prime the inlet pump before restarting."
    elif "HOTSPOT" in status or "FOULING" in status:
        action = "Schedule boiler descaling and clean tube bundle. Inspect refractory insulation around the detected hotspot coordinates."
    elif "LOW BOILER TEMPERATURE" in status or "LOW HEATING" in status:
        action = "Inspect heating elements for continuity or phase loss. Check contactor and temperature setpoint configuration."
    elif "EXCESSIVE FLOW" in status or "HIGH FLOW" in status:
        action = "Throttle intake control valve and verify pressure regulator downstream of the feed pump."
    elif severity == "WARNING":
        action = "Perform routine diagnostic check on indicated sensor channel and monitor trends closely."
    else:
        action = "System operating optimally. Continue standard supervisory monitoring."

    return status, severity, diagnosis, action


# ============================================================
# STYLING & BRANDING
# ============================================================
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');
.stApp {background:radial-gradient(circle at 50% 0%,rgba(0,190,255,.10),transparent 30%),linear-gradient(135deg,#02060c 0%,#06111b 52%,#02050a 100%);color:#eaf8ff;}
header {visibility:hidden;} footer {visibility:hidden;} #MainMenu {visibility:hidden;}
.block-container {max-width:1700px;padding:14px 2rem 30px 2rem;} * {font-family:'Inter',sans-serif;}
h1,h2,h3,h4 {font-family:'Orbitron',sans-serif !important;}
.topbar {display:flex;align-items:center;justify-content:space-between;padding:13px 18px;margin-bottom:14px;border:1px solid rgba(75,220,255,.18);border-radius:12px;background:rgba(3,12,21,.92);}
.brand {font-family:'Orbitron',sans-serif;font-weight:700;letter-spacing:1.5px;color:#f0fbff;} .brand span {color:#46e7ff;}
.section-title {font-family:'Orbitron',sans-serif;font-weight:700;letter-spacing:1px;margin:18px 0 10px;color:#9eefff;}
.metric-card {padding:18px;border:1px solid rgba(75,220,255,.18);border-radius:14px;background:rgba(3,12,21,.88);text-align:center;}
.metric-label {font-size:12px;color:#89a8b8;letter-spacing:1px;text-transform:uppercase;} .metric-value {font-family:'Orbitron',sans-serif;font-size:30px;font-weight:700;margin-top:5px;color:#f4fdff;}
.status-normal {color:#63ffc0;font-weight:800;} .status-warning {color:#ffd166;font-weight:800;} .status-critical {color:#ff6868;font-weight:800;}
.info-box {padding:18px;border-radius:14px;border:1px solid rgba(75,220,255,.20);background:rgba(5,24,35,.55);}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="topbar"><div class="brand">BOILER <span>AI</span> • TESTING / SIMULATION</div><div>🧪 <b>OFFLINE TEST MODE</b></div></div>', unsafe_allow_html=True)

# ============================================================
# STATE INITIALIZATION
# ============================================================
if "test_history" not in st.session_state:
    st.session_state.test_history = []
if "test_bmt" not in st.session_state:
    st.session_state.test_bmt = None
if "test_bmt_name" not in st.session_state:
    st.session_state.test_bmt_name = ""

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.markdown("## 🧭 Navigation")
st.sidebar.page_link("dashboard.py", label="🏭 Live Monitoring", icon="🏭")
st.sidebar.page_link("pages/2_Testing_Simulation.py", label="🧪 Testing / Simulation", icon="🧪")
st.sidebar.markdown("---")
st.sidebar.caption("Change process values without connecting the physical boiler.")

# ============================================================
# MANUAL PROCESS SLIDERS
# ============================================================
st.markdown('<div class="section-title">🎛️ MANUAL SENSOR INPUTS</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    manual_temp = st.slider("PT100 Temperature (°C)", 0.0, 150.0, 60.0, 0.5)
with c2:
    manual_flow = st.slider("YF-S201 Flow (L/min)", 0.0, 20.0, 1.5, 0.05)
with c3:
    manual_total = st.slider("Total Water (L)", 0.0, 20.0, 2.0, 0.05)

# ============================================================
# TESTO 872 BMT UPLOAD
# ============================================================
st.markdown('<div class="section-title">🌡️ OPTIONAL TESTO 872 BMT</div>', unsafe_allow_html=True)
bmt_file = st.file_uploader("Upload Testo 872 .BMT for radiometric thermal analysis", type=["bmt"], key="testing_bmt")
if bmt_file is not None:
    try:
        parsed = parse_testo_bmt(bmt_file.getvalue())
        st.session_state.test_bmt = parsed
        st.session_state.test_bmt_name = bmt_file.name
        st.success(f"BMT loaded: {bmt_file.name}")
    except Exception as e:
        st.session_state.test_bmt = None
        st.error(f"BMT parsing failed: {e}")

thermal_tmax = None
hotspot = False
if st.session_state.test_bmt is not None:
    bmt_stats = bmt_summary(st.session_state.test_bmt)
    if bmt_stats:
        thermal_tmax = float(bmt_stats.get("tmax")) if bmt_stats.get("tmax") is not None else None
        hotspot = thermal_tmax is not None and thermal_tmax >= TEMP_NORMAL_MAX

# ============================================================
# SIMULATION TRIGGER
# ============================================================
run = st.button("▶ RUN TEST / SIMULATION", type="primary", use_container_width=True)
if run:
    status, severity, diagnosis, action = fusion(
        manual_flow,
        manual_temp,
        thermal_tmax=thermal_tmax,
        hotspot=hotspot,
        total_water=manual_total
    )
    result = {
        "flow": manual_flow,
        "temp": manual_temp,
        "total": manual_total,
        "thermal_tmax": thermal_tmax,
        "status": status,
        "severity": severity,
        "diagnosis": diagnosis,
        "action": action,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.test_result = result
    st.session_state.test_history.append(result.copy())
    st.session_state.test_history = st.session_state.test_history[-1000:]

# ============================================================
# TEST RESULTS DISPLAY
# ============================================================
result = st.session_state.get("test_result")
if result:
    st.markdown('<div class="section-title">📊 TEST RESULT</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    with a:
        st.markdown(f'<div class="metric-card"><div class="metric-label">PT100</div><div class="metric-value">{result["temp"]:.1f} °C</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="metric-card"><div class="metric-label">YF-S201 FLOW</div><div class="metric-value">{result["flow"]:.2f} L/min</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="metric-card"><div class="metric-label">TOTAL WATER</div><div class="metric-value">{result["total"]:.2f} L</div></div>', unsafe_allow_html=True)
    with d:
        t = 'N/A' if result["thermal_tmax"] is None else f'{result["thermal_tmax"]:.1f} °C'
        st.markdown(f'<div class="metric-card"><div class="metric-label">TESTO TMAX</div><div class="metric-value">{t}</div></div>', unsafe_allow_html=True)

    sev = result["severity"].upper()
    cls = "status-normal" if sev == "NORMAL" else ("status-warning" if sev in ("LOW", "HIGH", "WARNING") else "status-critical")
    st.markdown(f'<div class="info-box"><h3 class="{cls}">STATUS: {result["status"]} • SEVERITY: {result["severity"]}</h3><h3>🔎 {result["diagnosis"]}</h3><p><b>Recommended Action:</b> {result["action"]}</p></div>', unsafe_allow_html=True)
    
    if sev in ("HIGH", "CRITICAL"):
        st.error("⚠️ WARNING — Simulated abnormal condition detected. This is a software test only.")
    elif sev in ("LOW", "WARNING"):
        st.warning("⚠️ Simulated warning condition detected.")
    else:
        st.success("✅ Simulated process is within the configured normal range.")

# ============================================================
# SENSOR STATE BREAKDOWN
# ============================================================
st.markdown('<div class="section-title">🔬 SENSOR STATE BREAKDOWN</div>', unsafe_allow_html=True)
states = get_parameter_states(manual_flow, manual_temp, manual_total)
q1, q2, q3, q4 = st.columns(4)
with q1:
    st.metric("PT100 State", states["temperature"])
with q2:
    st.metric("Flow State", states["flow"])
with q3:
    st.metric("Total Water State", states["total_water"])
with q4:
    thermal_val = ("CRITICAL" if thermal_tmax >= TEMP_HIGH else ("HIGH" if thermal_tmax >= TEMP_NORMAL_MAX else "NORMAL")) if thermal_tmax is not None else "NO BMT DATA"
    st.metric("Testo 872 Tmax State", thermal_val)

# ============================================================
# RADIOMETRIC MATRIX & PLOT
# ============================================================
if st.session_state.test_bmt is not None:
    st.markdown('<div class="section-title">🌡️ TESTO 872 RADIOMETRIC RESULT</div>', unsafe_allow_html=True)
    stats = bmt_summary(st.session_state.test_bmt)
    if stats:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tmax", f"{stats['tmax']:.2f} °C")
        m2.metric("Tmin", f"{stats['tmin']:.2f} °C")
        m3.metric("Average", f"{stats['tavg']:.2f} °C")
        m4.metric("Hotspot", f"X={stats['hot_x']}, Y={stats['hot_y']}")

        arr = stats.get("matrix")
        if arr is not None:
            fig, ax = plt.subplots(figsize=(8, 4.5))
            fig.patch.set_facecolor('#040e18')
            ax.set_facecolor('#040e18')
            im = ax.imshow(arr, cmap="inferno", aspect="auto")
            hx = stats.get("hotspot_x", stats.get("hot_x"))
            hy = stats.get("hotspot_y", stats.get("hot_y"))
            if hx is not None and hy is not None:
                ax.scatter([hx], [hy], marker="x", color="#00ffff", s=120, linewidths=2.5, label=f"Hotspot ({stats['tmax']:.1f}°C)")
                ax.legend(facecolor='#030d17', edgecolor='#4bdcff', labelcolor='#ffffff')
            ax.set_title("Testo 872 Radiometric Thermal Matrix", color="#9eefff", fontsize=12, fontweight="bold")
            ax.set_xlabel("Pixel X", color="#89a8b8")
            ax.set_ylabel("Pixel Y", color="#89a8b8")
            ax.tick_params(colors="#89a8b8")
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label("Temperature (°C)", color="#89a8b8")
            cbar.ax.yaxis.set_tick_params(color="#89a8b8")
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color="#89a8b8")
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.download_button(
                "⬇️ Download Radiometric Matrix CSV",
                pd.DataFrame(arr).to_csv(index=False).encode("utf-8"),
                "testo_872_test_matrix.csv",
                "text/csv"
            )

# ============================================================
# QUICK TEST CASES
# ============================================================
st.markdown('<div class="section-title">🧰 QUICK TEST CASES</div>', unsafe_allow_html=True)
q1, q2, q3, q4 = st.columns(4)
with q1:
    st.caption("NORMAL")
    st.code("60 °C | 1.5 L/min | 2.0 L")
with q2:
    st.caption("LOW FLOW")
    st.code("60 °C | 0.1 L/min | 2.0 L")
with q3:
    st.caption("OVERHEATING")
    st.code("90 °C | 1.5 L/min | 2.0 L")
with q4:
    st.caption("COMBINED FAULT")
    st.code("90 °C | 0.1 L/min | 0.2 L")

# ============================================================
# SIMULATION HISTORY
# ============================================================
st.markdown('<div class="section-title">📈 SIMULATION HISTORY</div>', unsafe_allow_html=True)
hist = pd.DataFrame(st.session_state.test_history)
if not hist.empty:
    x = pd.to_datetime(hist["time"])
    g1, g2 = st.columns(2)
    with g1:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        fig.patch.set_facecolor('#040e18')
        ax.set_facecolor('#040e18')
        ax.plot(x, hist["temp"], color="#ff7b26", linewidth=2, label="PT100")
        ax.axhline(TEMP_NORMAL_MAX, color="#ffd166", linestyle="--", label=f"Normal max ({TEMP_NORMAL_MAX}°C)")
        ax.axhline(TEMP_HIGH, color="#ff6868", linestyle="--", label=f"Fault limit ({TEMP_HIGH}°C)")
        ax.set_ylabel("°C", color="#89a8b8")
        ax.set_title("Simulated Temperature", color="#9eefff")
        ax.tick_params(colors="#89a8b8")
        ax.grid(True, color="#122533", linestyle=":")
        ax.legend(facecolor='#030d17', edgecolor='#4bdcff', labelcolor='#ffffff', fontsize=8)
        plt.xticks(rotation=30)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with g2:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        fig.patch.set_facecolor('#040e18')
        ax.set_facecolor('#040e18')
        ax.plot(x, hist["flow"], color="#46e7ff", linewidth=2, label="YF-S201")
        ax.axhline(FLOW_LOW, color="#ff6868", linestyle="--", label=f"Low-flow limit ({FLOW_LOW} L/min)")
        ax.set_ylabel("L/min", color="#89a8b8")
        ax.set_title("Simulated Flow", color="#9eefff")
        ax.tick_params(colors="#89a8b8")
        ax.grid(True, color="#122533", linestyle=":")
        ax.legend(facecolor='#030d17', edgecolor='#4bdcff', labelcolor='#ffffff', fontsize=8)
        plt.xticks(rotation=30)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.dataframe(hist.tail(30), use_container_width=True)
    st.download_button(
        "⬇️ Download Testing Log",
        hist.to_csv(index=False).encode("utf-8"),
        "boiler_testing_simulation_log.csv",
        "text/csv"
    )
else:
    st.info("Run a test to create simulation history.")

st.markdown('<div style="text-align:center;color:#6f8997;padding:24px">AI-BASED BOILER PREDICTIVE FAULT DETECTION<br>SENSOR FUSION • PT100 • YF-S201 • TESTO 872<br><br>TESTING / SIMULATION MODE</div>', unsafe_allow_html=True)
