import streamlit as st
import paho.mqtt.client as mqtt
import ssl
import json
import time
import threading

APP_ID = "ssr-baton-test"
MQTT_USERNAME = "ssr-baton-test@ttn"
MQTT_PASSWORD = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER = "nam1.cloud.thethings.network"
PORT = 8883

if "latest_messages" not in st.session_state:
    st.session_state.latest_messages = []

def on_connect(client, userdata, flags, rc):
    print("on_connect fired with rc =", rc)
    if rc == 0:
        client.subscribe(f"v3/{APP_ID}/devices/+/up")
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    print("MQTT message received:", msg.payload)
    try:
        payload = json.loads(msg.payload.decode())
    except:
        payload = {"raw": msg.payload.decode()}
    st.session_state.latest_messages.append(payload)

def start_mqtt():
    print("Starting MQTT thread...")
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    threading.Thread(target=client.loop_forever, daemon=True).start()

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("TTN Live Telemetry Dashboard")

# FIRST RUN: render UI only
if "first_run_done" not in st.session_state:
    st.session_state.first_run_done = True
    st.write("Initializing MQTT…")
    st.rerun()

# SECOND RUN: start MQTT thread
if "mqtt_thread_started" not in st.session_state:
    start_mqtt()
    st.session_state.mqtt_thread_started = True
    st.write("MQTT thread started")
    st.rerun()

# SUBSEQUENT RUNS: show messages
log = st.empty()

if st.session_state.latest_messages:
    text = "\n\n".join(json.dumps(m, indent=2) for m in st.session_state.latest_messages[-50:])
    log.text(text)
else:
    log.text("Waiting for MQTT messages...")

time.sleep(1)
st.rerun()