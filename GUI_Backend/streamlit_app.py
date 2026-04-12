"""
streamlit_app.py — Newt Racing Seneca 7 Live Baton Tracker
------------------------------------------------------------
FIX SUMMARY (vs original):
  1. st.session_state cannot be written from a background thread — all
     cross-thread communication now goes through a thread-safe queue.Queue.
  2. MQTT client is only ever started ONCE per browser session via a flag
     in session_state; the original had a race condition that could spawn
     multiple clients.
  3. on_connect now matches the MQTTv311 signature (4 args, not 5).
  4. MQTT topic corrected to include @ttn tenant:
         v3/{APP_ID}@ttn/devices/+/up
  5. Draining the queue and calling st.rerun() every 2 s gives live updates
     without the blank-screen problem caused by writing session_state from
     a thread.
"""

import json
import queue
import ssl
import time

import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────
APP_ID    = "ssr-baton-test"
MQTT_USER = "ssr-baton-test@ttn"
MQTT_PASS = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER    = "nam1.cloud.thethings.network"
PORT      = 8883
# Correct topic: must include @ttn (tenant) after the app-id
TOPIC     = f"v3/{APP_ID}@ttn/devices/+/up"

# ── Session-state initialisation ────────────────────────────────────────────
# These run on every rerun but are only assigned the first time.
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()   # thread-safe; MQTT writes here

if "messages" not in st.session_state:
    st.session_state.messages = []               # main-thread accumulator

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Not connected"

# ── MQTT callbacks ──────────────────────────────────────────────────────────
# IMPORTANT: callbacks must never touch st.session_state directly —
# they run in paho's background thread and Streamlit will silently drop
# the writes (or crash).  Use a Queue instead.

def on_connect(client, userdata, flags, rc):
    """Called by paho in its own thread when the TCP handshake completes."""
    if rc == 0:
        client.subscribe(TOPIC, qos=1)
        # Signal the main thread via the queue
        userdata.put({"_status": "connected"})
    else:
        userdata.put({"_status": f"connect failed rc={rc}"})

def on_disconnect(client, userdata, rc):
    userdata.put({"_status": f"disconnected rc={rc}"})

def on_message(client, userdata, msg):
    """Parse a TTN uplink and push a flat dict onto the queue."""
    try:
        raw = json.loads(msg.payload.decode())
    except Exception:
        return

    uplink = raw.get("uplink_message", {})
    dp     = uplink.get("decoded_payload") or {}
    rx     = (uplink.get("rx_metadata") or [{}])[0]

    row = {
        "time"       : raw.get("received_at", ""),
        "device_id"  : raw.get("end_device_ids", {}).get("device_id", ""),
        "baton_id"   : dp.get("batonID"),
        "racer_num"  : dp.get("racerNumber"),
        "lat"        : dp.get("latitude"),
        "lon"        : dp.get("longitude"),
        "battery"    : dp.get("battery"),
        "rssi"       : rx.get("rssi"),
        "snr"        : rx.get("snr"),
    }
    userdata.put(row)   # ← safe cross-thread handoff

# ── Start MQTT exactly once per session ─────────────────────────────────────
if "mqtt_started" not in st.session_state:
    q = st.session_state.msg_queue
    client = mqtt.Client(
        client_id=f"newt-racing-{int(time.time())}",
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.tls_insecure_set(False)
    client.user_data_set(q)          # queue is the userdata — safe from any thread
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()              # starts paho's background thread
    st.session_state.mqtt_started = True

# ── Drain queue → session state (main thread only) ──────────────────────────
q = st.session_state.msg_queue
drained = 0
while not q.empty():
    item = q.get_nowait()
    if "_status" in item:
        st.session_state.mqtt_status = item["_status"]
    else:
        st.session_state.messages.append(item)
        drained += 1

# Keep only the most recent 500 records
st.session_state.messages = st.session_state.messages[-500:]

# ── UI ───────────────────────────────────────────────────────────────────────
st.title("🏃 Newt Racing — Seneca 7 Live Baton Tracker")

status_color = "🟢" if st.session_state.mqtt_status == "connected" else "🔴"
st.caption(
    f"{status_color} MQTT: {st.session_state.mqtt_status}  |  "
    f"Packets received: {len(st.session_state.messages)}"
)

msgs = st.session_state.messages

if msgs:
    df = pd.DataFrame(msgs)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")

    # ── Latest status per baton ──────────────────────────────────────────
    st.subheader("Latest Baton Status")
    latest = (
        df.sort_values("time")
          .groupby("baton_id")
          .last()
          .reset_index()[["baton_id", "racer_num", "lat", "lon", "battery", "rssi", "time"]]
    )
    st.dataframe(latest, use_container_width=True)

    # ── Map ──────────────────────────────────────────────────────────────
    gps = df.dropna(subset=["lat", "lon"])
    gps = gps[(gps["lat"] != 0) & (gps["lon"] != 0)].copy()
    if not gps.empty:
        st.subheader("GPS Track")
        gps = gps.rename(columns={"lat": "latitude", "lon": "longitude"})
        st.map(gps[["latitude", "longitude"]])
    else:
        st.info("No valid GPS fixes yet — device may still be acquiring satellites.")

    # ── Raw message log ──────────────────────────────────────────────────
    with st.expander("Raw message log (newest first)"):
        display = df.copy()
        display["time"] = display["time"].dt.strftime("%H:%M:%S")
        st.dataframe(display.iloc[::-1], use_container_width=True)

else:
    st.info("⏳ Waiting for MQTT messages from TTN…")
    st.markdown(
        f"**Broker:** `{BROKER}:{PORT}`  \n"
        f"**Topic:** `{TOPIC}`  \n"
        "Check that your device is powered on and within LoRaWAN coverage."
    )

# ── Auto-refresh every 2 s ───────────────────────────────────────────────────
time.sleep(2)
st.rerun()