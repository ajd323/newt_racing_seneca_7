import streamlit as st
from mqtt_backend import start_mqtt_background, latest_messages
import pandas as pd
import time

st.title("TTN Live Telemetry Dashboard")

# Start MQTT only once
if "mqtt_started" not in st.session_state:
    start_mqtt_background()
    st.session_state.mqtt_started = True

placeholder = st.empty()

while True:
    if latest_messages:
        df = pd.DataFrame(latest_messages)
        placeholder.dataframe(df)
    time.sleep(0.5)