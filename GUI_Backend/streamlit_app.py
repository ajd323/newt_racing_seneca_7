import streamlit as st
from mqtt_backend import start_mqtt_background, latest_messages
import time
import json

st.title("TTN Live Telemetry Dashboard")

# Start MQTT only once
if "mqtt_started" not in st.session_state:
    start_mqtt_background()
    st.session_state.mqtt_started = True

output = st.empty()

while True:
    if latest_messages:
        msg = latest_messages.pop(0)
        pretty = json.dumps(msg, indent=2)
        output.text(pretty)
    time.sleep(0.2)