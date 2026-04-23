"""
streamlit_app.py — Newt Racing Seneca 7 Live Baton Tracker
"""

import json
import queue
import ssl
import time
import uuid

import folium
import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st
from streamlit_folium import st_folium

# ── Config ─────────────────────────────────────────────────────────────────
APP_ID    = "ssr-baton-test"
MQTT_USER = "ssr-baton-test@ttn"
MQTT_PASS = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER    = "nam1.cloud.thethings.network"
PORT      = 8883
TOPIC     = f"v3/{APP_ID}@ttn/devices/+/up"

# ── Session-state initialisation ────────────────────────────────────────────
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "button_events" not in st.session_state:
    st.session_state.button_events = []  # list of {lat, lon, time, baton_id}

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Not connected"

if "prev_button_counts" not in st.session_state:
    st.session_state.prev_button_counts = {}  # device_id -> last buttonPressed value

if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None

# ── MQTT callbacks ──────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    error_messages = {
        0: "connected",
        1: "incorrect protocol version",
        2: "invalid client identifier", 
        3: "server unavailable",
        4: "bad username or password",
        5: "not authorized",
        7: "no supported authentication method"
    }
    
    if rc == 0:
        client.subscribe(TOPIC, qos=1)
        userdata.put({"_status": "connected"})
        print(f"✅ Connected successfully to {BROKER}")
    else:
        msg = error_messages.get(rc, f"unknown error {rc}")
        userdata.put({"_status": f"❌ {msg}"})
        print(f"❌ Connection failed: {msg} (rc={rc})")

def on_disconnect(client, userdata, rc):
    error_messages = {
        0: "disconnected (normal)",
        5: "disconnected (not authorized)",
        7: "disconnected (no auth method)"
    }
    msg = error_messages.get(rc, f"disconnected rc={rc}")
    userdata.put({"_status": msg})
    print(f"🔌 Disconnected: {msg}")

def on_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
    except Exception as e:
        print(f"⚠️  Failed to parse message: {e}")
        return

    uplink = raw.get("uplink_message", {})
    dp     = uplink.get("decoded_payload") or {}
    rx     = (uplink.get("rx_metadata") or [{}])[0]

    row = {
        "time"          : raw.get("received_at", ""),
        "device_id"     : raw.get("end_device_ids", {}).get("device_id", ""),
        "baton_id"      : dp.get("batonID"),
        "buttonPressed" : dp.get("buttonPressed", 0),
        "lat"           : dp.get("latitude"),
        "lon"           : dp.get("longitude"),
        "rssi"          : rx.get("rssi"),
        "snr"           : rx.get("snr"),
    }
    userdata.put(row)
    print(f"📨 Message received from baton {row.get('baton_id')}")

# ── Start MQTT exactly once per session ─────────────────────────────────────
if st.session_state.mqtt_client is None:
    q = st.session_state.msg_queue
    
    client = mqtt.Client(
        client_id=f"newt-racing-{uuid.uuid4().hex[:12]}",
        protocol=mqtt.MQTTv311,
    )
    
    # Set credentials
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    
    # TLS setup with explicit TLS 1.2
    client.tls_set(
        ca_certs=None,  # Use system CA bundle
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )
    
    # Set callbacks
    client.user_data_set(q)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    
    # Connect
    try:
        print(f"🔌 Attempting connection to {BROKER}:{PORT}")
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        st.session_state.mqtt_client = client
        print("✅ MQTT client started")
    except Exception as e:
        st.session_state.mqtt_status = f"Connection failed: {e}"
        print(f"❌ Connection exception: {e}")

# ── Drain queue → session state (main thread only) ──────────────────────────
q = st.session_state.msg_queue
while not q.empty():
    item = q.get_nowait()
    if "_status" in item:
        st.session_state.mqtt_status = item["_status"]
    else:
        st.session_state.messages.append(item)

        # ── Button press detection ──
        device_id = item.get("device_id", "")
        current_count = item.get("buttonPressed", 0) or 0
        prev_count = st.session_state.prev_button_counts.get(device_id, 0)

        # If buttonPressed count increased, record a button event at this location
        if current_count > prev_count and item.get("lat") and item.get("lon"):
            for _ in range(current_count - prev_count):
                st.session_state.button_events.append({
                    "lat"      : item["lat"],
                    "lon"      : item["lon"],
                    "time"     : item["time"],
                    "baton_id" : item.get("baton_id"),
                    "device_id": device_id,
                })

        st.session_state.prev_button_counts[device_id] = current_count

# Keep last 500 messages
st.session_state.messages = st.session_state.messages[-500:]

# ── UI ───────────────────────────────────────────────────────────────────────
st.title("🏃 Newt Racing — Seneca 7 Live Baton Tracker")

status_color = "🟢" if st.session_state.mqtt_status == "connected" else "🔴"
st.caption(
    f"{status_color} MQTT: {st.session_state.mqtt_status}  |  "
    f"Packets received: {len(st.session_state.messages)}  |  "
    f"Button events: {len(st.session_state.button_events)}"
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
          .reset_index()[["baton_id", "buttonPressed", "lat", "lon", "rssi", "time"]]
    )
    st.dataframe(latest, use_container_width=True)

    # ── Folium Map with blue button-press pins ───────────────────────────
    gps = df.dropna(subset=["lat", "lon"])
    gps = gps[(gps["lat"] != 0) & (gps["lon"] != 0)].copy()

    st.subheader("GPS Track & Button Press Locations")

    # Default center: Seneca Lake area
    center_lat = gps["lat"].mean() if not gps.empty else 42.444
    center_lon = gps["lon"].mean() if not gps.empty else -76.502

    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Draw GPS track as polyline per device
    if not gps.empty:
        for device_id, group in gps.groupby("device_id"):
            group = group.sort_values("time")
            coords = list(zip(group["lat"], group["lon"]))
            if len(coords) > 1:
                folium.PolyLine(
                    coords,
                    color="red",
                    weight=3,
                    opacity=0.7,
                    tooltip=f"Track: {device_id}"
                ).add_to(m)

            # Latest position marker (red)
            last = group.iloc[-1]
            folium.Marker(
                location=[last["lat"], last["lon"]],
                tooltip=f"Baton {last.get('baton_id')} — Latest position",
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(m)

    # Blue pins for button press events
    for event in st.session_state.button_events:
        if event.get("lat") and event.get("lon"):
            t = event.get("time", "")
            if hasattr(t, "strftime"):
                t_str = t
            else:
                try:
                    t_str = pd.to_datetime(t, utc=True).strftime("%H:%M:%S")
                except Exception:
                    t_str = str(t)

            folium.Marker(
                location=[event["lat"], event["lon"]],
                tooltip=f"🔵 Button pressed — Baton {event.get('baton_id')} at {t_str}",
                icon=folium.Icon(color="blue", icon="hand-up", prefix="glyphicon")
            ).add_to(m)

    st_folium(m, width=700, height=500)

    if st.session_state.button_events:
        st.subheader("Button Press Log")
        btn_df = pd.DataFrame(st.session_state.button_events)
        btn_df["time"] = pd.to_datetime(btn_df["time"], utc=True, errors="coerce")
        btn_df["time"] = btn_df["time"].dt.strftime("%H:%M:%S")
        st.dataframe(btn_df.iloc[::-1], use_container_width=True)
    else:
        st.info("No button presses recorded yet.")

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