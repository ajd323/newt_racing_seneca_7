# mqtt_backend.py

import json
import ssl
import threading
import time
import paho.mqtt.client as mqtt

APP_ID = "ssr-baton-test"
MQTT_USERNAME = "ssr-baton-test@ttn"
MQTT_PASSWORD = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER = "nam1.cloud.thethings.network"
PORT = 8883

latest_messages = []
Connected = False

def on_connect(client, userdata, flags, rc):
    global Connected
    if rc == 0:
        print("Connected to broker")
        Connected = True
        client.subscribe(f"v3/{APP_ID}/devices/+/up")
    else:
        print("Connection failed with rc =", rc)

def on_message(client, userdata, message):
    print("MQTT message received:", message.payload)

    try:
        payload = json.loads(message.payload.decode())
    except:
        payload = {"raw": message.payload.decode()}

    # Push to Streamlit
    latest_messages.append(payload)

def start_mqtt_background():
    client = mqtt.Client(
        client_id="StreamlitListener",
        protocol=mqtt.MQTTv311
    )

    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, keepalive=60)

    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()

    return client