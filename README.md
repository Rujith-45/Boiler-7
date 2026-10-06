# AI-Based Boiler Predictive Fault Detection

A Cyber-Physical SCADA / HMI Dashboard built with Streamlit for industrial boiler monitoring and predictive fault diagnosis using multi-sensor fusion and radiometric thermography.

---

## 📌 Project Overview

- **Process Telemetry**: Real-time data acquisition from STM32 microcontroller (PT100 temperature sensor, YF-S201 water flow sensor, and cumulative water volume).
- **Radiometric Thermography**: Integrated binary parser for Testo 872 `.BMT` files to extract raw radiometric temperature matrices, compute hotspot pixel locations, and generate thermal heatmaps.
- **Thermography Video**: Video playback for visual thermal inspection.
- **Rule-Based Sensor Fusion Engine**: Multi-priority fault classification (inlet/pump failures, dry-run risk, heater element degradation, localized hotspots).
- **SCADA Digital Twin**: Interactive CSS-animated boiler model and synthesized audio alarm generation.

---

## 🚀 Installation & Local Execution

### Prerequisites
- Python 3.9+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Rujith-45/Boiler-7.git
cd Boiler-7
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the dashboard
```bash
streamlit run dashboard.py
```

The application will be accessible at `http://localhost:8501`.

---

## ☁️ Deployment Guide

### Live on GitHub Pages (Serverless & Free)
This application runs natively in web browsers on GitHub Pages using **stlite** (Streamlit compiled with WebAssembly/Pyodide). No backend server is required!

1. Go to your repository on GitHub: `https://github.com/Rujith-45/Boiler-7`
2. Navigate to **Settings** ➔ **Pages**
3. Under **Build and deployment**:
   - **Source**: Select **GitHub Actions** (recommended) or **Deploy from a branch** (`main` / `/root`)
4. Once deployed, your live application will be available at:
   `https://rujith-45.github.io/Boiler-7/`

---

## 👥 Authors
- **Mentor**: N INDHU
- **Team**: RUJITH RS • SANJUSRINITHA T • RHOGETHRAM S T
