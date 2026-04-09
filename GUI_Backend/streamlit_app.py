import streamlit as st
import paho.mqtt.client as mqtt
import ssl
import json
import time
import queue
import pandas as pd

# -----------------------------
# TTN MQTT CONFIG
# -----------------------------
APP_ID    = "ssr-baton-test"
MQTT_USER = "ssr-baton-test@ttn"
MQTT_PASS = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER    = "nam1.cloud.thethings.network"
PORT      = 8883

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# MQTT CALLBACKS
# -----------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(f"v3/{APP_ID}/devices/+/up")
    else:
        print(f"MQTT connect failed: {reason_code}")

def on_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
    except Exception:
        return
    dp  = raw.get("uplink_message", {}).get("decoded_payload", {})
    rx  = raw.get("uplink_message", {}).get("rx_metadata", [{}])[0]
    row = {
        "time":     raw.get("received_at", ""),
        "baton_id": dp.get("batonID"),
        "lat":      dp.get("latitude"),
        "lon":      dp.get("longitude"),
        "battery":  dp.get("battery"),
        "rssi":     rx.get("rssi"),
    }
    userdata["queue"].put(row)

# -----------------------------
# START MQTT ONCE
# -----------------------------
def start_mqtt(q):
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        protocol=mqtt.MQTTv311
    )
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.user_data_set({"queue": q})
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

if "mqtt_started" not in st.session_state:
    start_mqtt(st.session_state.msg_queue)
    st.session_state.mqtt_started = True

# -----------------------------
# DRAIN QUEUE → SESSION STATE
# -----------------------------
q = st.session_state.msg_queue
while not q.empty():
    st.session_state.messages.append(q.get_nowait())

st.session_state.messages = st.session_state.messages[-200:]

# -----------------------------
# UI
# -----------------------------
st.title("🏃 Newt Racing — Live Baton Tracker")
st.caption(f"Packets received: {len(st.session_state.messages)}")

msgs = st.session_state.messages

if msgs:
    df = pd.DataFrame(msgs)
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%H:%M:%S")

    st.dataframe(df[::-1], use_container_width=True)

    gps = df[(df["lat"] != 0) & (df["lon"] != 0)].copy()
    if not gps.empty:
        gps = gps.rename(columns={"lat": "latitude", "lon": "longitude"})
        st.map(gps[["latitude", "longitude"]])
    else:
        st.info("GPS coordinates are all zero — device may not have a fix yet.")
else:
    st.info("Waiting for MQTT messages…")

time.sleep(2)
st.rerun()