import json
import ssl
import time
import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mqtt_started" not in st.session_state:
    st.session_state.mqtt_started = False

# MQTT Callback
def on_message(client, userdata, msg):
    """Callback for when a message is received from TTN."""
    try:
        payload = json.loads(msg.payload.decode())
        st.session_state.messages.append(payload)
        print("MQTT message received:", payload)
    except Exception as e:
        print("Error parsing MQTT message:", e)

# MQTT Startup
def start_mqtt():
    """Connect to TTN MQTT and begin listening."""
    MQTT_USERNAME = st.secrets["MQTT_USERNAME"]
    MQTT_PASSWORD = st.secrets["MQTT_PASSWORD"]
    MQTT_SERVER   = st.secrets["MQTT_SERVER"]
    APP_ID        = st.secrets["APP_ID"]

    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_message = on_message

    client.connect(MQTT_SERVER, 8883)
    client.subscribe(f"v3/{APP_ID}/devices/+/up")
    client.loop_start()

    return client

# DataFrame Builder (Robust)
def build_dataframe():
    """Safely convert stored MQTT messages into a DataFrame."""
    messages = st.session_state.get("messages", [])
    rows = []

    for msg in messages:
        uplink = msg.get("uplink_message", {})
        decoded = uplink.get("decoded_payload", {})

        rows.append({
            "timestamp": uplink.get("received_at"),
            "lat": decoded.get("lat"),
            "lon": decoded.get("lon"),
            "battery": decoded.get("battery"),
            "raw": msg
        })

    return pd.DataFrame(rows)


# Streamlit UI
st.title("📡 TTN Live Telemetry Dashboard")

# Start MQTT only once
if not st.session_state.mqtt_started:
    start_mqtt()
    st.session_state.mqtt_started = True
    st.success("MQTT listener started")

# Build dataframe
df = build_dataframe()

# Display UI
if df.empty:
    st.info("Waiting for MQTT messages…")
else:
    st.subheader("Latest Telemetry")
    st.dataframe(df)

    # Optional: show last message
    st.subheader("Most Recent Packet")
    st.json(df.iloc[-1]["raw"])