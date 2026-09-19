"""
relay_server.py  -  ESP32 to ThingSpeak bridge
=================================================
Run this on your local PC (same network as the ESP32).

Requirements:
  py -m pip install flask flask-cors requests

Usage:
  py relay_server.py

Set your ThingSpeak WRITE_API_KEY and CHANNEL_ID below.
The script will poll the ESP32 and push to ThingSpeak every 15s.
(Free ThingSpeak has 15-second minimum update interval.)

ThingSpeak field mapping:
  field1 = flow (L/min)
  field2 = temperature (degC)
  field3 = totalLiters (L)
"""

import time
import threading
import requests
from flask import Flask, jsonify
from flask_cors import CORS

# ----------------------------------------------------------------
# CONFIG  -- EDIT THESE VALUES
# ----------------------------------------------------------------
ESP32_URL        = "http://192.168.137.128/data"
THINGSPEAK_WRITE = "4MBMDDLPU78NBNF4"   # <-- paste Write API Key
THINGSPEAK_CH    = "3500246"      # <-- paste Channel ID (digits only)

RELAY_PORT       = 5050
FETCH_INTERVAL   = 1.0    # how often to poll ESP32 (seconds)
PUSH_INTERVAL    = 15.0   # how often to push ThingSpeak (min 15s on free plan)
# ----------------------------------------------------------------

app = Flask(__name__)
CORS(app)

_cache_lock = threading.Lock()
_cached = {
    "flow":        0.0,
    "temperature": 0.0,
    "totalLiters": 0.0,
    "status":      "fetching",
    "ts":          0,
}


# ---------------------------------------------------------------
# Poll ESP32 continuously at 1s intervals
# ---------------------------------------------------------------
def _poll_esp32():
    print("[relay] Polling ESP32 at " + ESP32_URL + " ...")
    while True:
        try:
            r = requests.get(ESP32_URL, timeout=3)
            r.raise_for_status()
            data = r.json()
            with _cache_lock:
                _cached.update({
                    "flow":        float(data.get("flow",        0)),
                    "temperature": float(data.get("temperature", 0)),
                    "totalLiters": float(data.get("totalLiters", 0)),
                    "status":      "ok",
                    "ts":          int(time.time()),
                })
            print("[relay] ESP32 OK  flow=" + str(round(_cached["flow"], 2)) +
                  "  temp=" + str(round(_cached["temperature"], 2)) +
                  "  total=" + str(round(_cached["totalLiters"], 4)))
        except Exception as e:
            with _cache_lock:
                _cached["status"] = "error: " + str(e)
            print("[relay] ESP32 error: " + str(e))
        time.sleep(FETCH_INTERVAL)


# ---------------------------------------------------------------
# Push to ThingSpeak every 15 seconds (free plan minimum)
# ---------------------------------------------------------------
def _push_thingspeak():
    if THINGSPEAK_WRITE == "YOUR_WRITE_API_KEY":
        print("[relay] WARNING: ThingSpeak Write API Key not configured!")
        print("        Open relay_server.py and set THINGSPEAK_WRITE and THINGSPEAK_CH")
        return

    ts_url = "https://api.thingspeak.com/update"
    print("[relay] ThingSpeak push thread started (every " + str(PUSH_INTERVAL) + "s)")

    while True:
        time.sleep(PUSH_INTERVAL)
        with _cache_lock:
            f  = _cached["flow"]
            t  = _cached["temperature"]
            tl = _cached["totalLiters"]
            ok = _cached["status"] == "ok"

        if not ok:
            print("[relay] Skipping ThingSpeak push - no ESP32 data yet")
            continue

        try:
            params = {
                "api_key": THINGSPEAK_WRITE,
                "field1":  round(f,  4),
                "field2":  round(t,  4),
                "field3":  round(tl, 4),
            }
            r = requests.get(ts_url, params=params, timeout=10)
            if r.text.strip() == "0":
                print("[relay] ThingSpeak push FAILED (rate limit or bad key)")
            else:
                print("[relay] ThingSpeak push OK  entry=" + r.text.strip() +
                      "  flow=" + str(round(f, 2)) +
                      "  temp=" + str(round(t, 2)))
        except Exception as e:
            print("[relay] ThingSpeak push error: " + str(e))


# ---------------------------------------------------------------
# Flask routes (optional - for local debugging)
# ---------------------------------------------------------------
@app.route("/data")
def data():
    with _cache_lock:
        return jsonify(dict(_cached))

@app.route("/health")
def health():
    with _cache_lock:
        return jsonify({"relay": "up", "esp32_status": _cached["status"]})


# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  ESP32  ->  ThingSpeak  Relay")
    print("  ESP32 URL  : " + ESP32_URL)
    print("  Channel ID : " + THINGSPEAK_CH)
    print("  Push every : " + str(PUSH_INTERVAL) + "s")
    print("=" * 60)
    print()

    # ESP32 polling thread
    t1 = threading.Thread(target=_poll_esp32, daemon=True)
    t1.start()

    # ThingSpeak push thread
    t2 = threading.Thread(target=_push_thingspeak, daemon=True)
    t2.start()

    print("[relay] Local debug endpoint: http://localhost:" + str(RELAY_PORT) + "/data")
    app.run(host="0.0.0.0", port=RELAY_PORT, threaded=True)
