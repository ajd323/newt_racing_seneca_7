# mqtt_backend.py

import json
import ssl
import threading
import paho.mqtt.client as mqtt

APP_ID = "ssr-baton-test"
MQTT_USERNAME = "ssr-baton-test@ttn"
MQTT_PASSWORD = "YOUR_API_KEY"
MQTT_SERVER = "nam1.cloud.thethings.network"
PORT = 8883

latest_messages = []

def on_connect(client, userdata, flags, rc, properties=None):
    print("MQTT connected with rc =", rc)
    if rc == 0:
        client.subscribe(f"v3/{APP_ID}/devices/+/up")
    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        latest_messages.append(payload)
    except Exception as e:
        print("Decode error:", e)

def start_mqtt_background():
    client = mqtt.Client(
        client_id="StreamlitListener",
        protocol=mqtt.MQTTv5,
        transport="tcp",
        callback_api_version=5
    )

    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.tls_insecure_set(False)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_SERVER, PORT, keepalive=60)

    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()

    return client