import streamlit as st
from mqtt_backend import start_mqtt_background, latest_messages
import json
import time

st.title("TTN Live Telemetry Dashboard")

if "mqtt_started" not in st.session_state:
    start_mqtt_background()
    st.session_state.mqtt_started = True

log = st.empty()

if latest_messages:
    text = "\n\n".join(json.dumps(m, indent=2) for m in latest_messages[-50:])
    log.text(text)
else:
    log.text("Waiting for MQTT messages...")

time.sleep(1)
st.rerun()