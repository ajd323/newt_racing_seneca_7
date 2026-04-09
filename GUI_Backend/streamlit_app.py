import streamlit as st
from mqtt_backend import start_mqtt_background, latest_messages
import json
import time

st.title("TTN Live Telemetry Dashboard")

# Start MQTT only once
if "mqtt_started" not in st.session_state:
    start_mqtt_background()
    st.session_state.mqtt_started = True

# Auto-refresh every second
st_autorefresh = st.experimental_rerun

# Display area
log = st.empty()

# Render messages
if latest_messages:
    text = "\n\n".join(json.dumps(m, indent=2) for m in latest_messages[-50:])
    log.text(text)
else:
    log.text("Waiting for MQTT messages...")

# Trigger rerun in 1 second
time.sleep(1)
st.experimental_rerun()
