import json
import ssl
import time
import paho.mqtt.client as mqtt

# Load secrets from secrets.toml (Python 3.9+ compatible)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import os

# Auto-detect secrets file
if os.path.exists(".secrets.toml"):
    secrets_file = ".secrets.toml"
elif os.path.exists("secrets.toml"):
    secrets_file = "secrets.toml"
else:
    raise FileNotFoundError("No secrets.toml or .secrets.toml found in this folder.")

with open(secrets_file, "rb") as f:
    secrets = tomllib.load(f)

MQTT_USERNAME = secrets["MQTT_USERNAME"]
MQTT_PASSWORD = secrets["MQTT_PASSWORD"]
MQTT_SERVER   = secrets["MQTT_SERVER"]
APP_ID        = secrets["APP_ID"]


def on_message(client, userdata, msg):
    print("\n--- MQTT MESSAGE RECEIVED ---")
    try:
        payload = json.loads(msg.payload.decode())
        print(json.dumps(payload, indent=2))
    except Exception as e:
        print("Error decoding message:", e)


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # Use default TLS context, disable verification if needed
    client.tls_set()
    client.tls_insecure_set(True)

    print("Connecting to TTN MQTT...")
    client.connect(MQTT_SERVER, 8883)
    client.subscribe(f"v3/{APP_ID}/devices/+/up")
    client.loop_start()

    print("Connected. Listening for uplinks...")
    return client


if __name__ == "__main__":
    client = start_mqtt()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping MQTT listener...")
        client.loop_stop()
        client.disconnect()