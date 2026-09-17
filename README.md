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

### Deploying to Streamlit Community Cloud (Recommended & Free)
Streamlit apps rely on persistent WebSockets and long-running Python execution. The recommended platform to host this application is **Streamlit Community Cloud**:
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `Rujith-45/Boiler-7`.
4. Set the main file path to: `dashboard.py`.
5. Click **"Deploy!"**. Your application will be live in minutes with full WebSocket and live re-rendering support.

### Note on Vercel
Vercel is designed for serverless, stateless architectures (Node.js/Next.js/stateless REST APIs) with short execution timeouts and does not support the persistent WebSockets required by standard Streamlit server sessions. For hosting Streamlit online, Streamlit Community Cloud, Render, Railway, or Hugging Face Spaces are recommended.

---

## 👥 Authors
- **Mentor**: N INDHU
- **Team**: RUJITH RS • SANJUSRINITHA T • RHOGETHRAM S T
