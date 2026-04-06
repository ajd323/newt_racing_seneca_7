import json
import ssl
import paho.mqtt.client as mqtt
import streamlit as st

# Initialize message store
if "messages" not in st.session_state:
    st.session_state.messages = []

def on_message(client, userdata, msg):
    """Callback for when a message is received from TTN."""
    print("MQTT message received!")
    print(msg.payload.decode())  # raw JSON from TTN
    payload = json.loads(msg.payload.decode())
    st.session_state.messages.append(payload)

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