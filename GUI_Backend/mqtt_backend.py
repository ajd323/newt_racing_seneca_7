"""
mqtt_backend.py — standalone MQTT helper (optional, for testing outside Streamlit)
-----------------------------------------------------------------------------------
FIX SUMMARY (vs original):
  1. MQTT topic was missing @ttn tenant:  v3/{APP_ID}/devices/+/up  →
                                          v3/{APP_ID}@ttn/devices/+/up
  2. latest_messages is now a proper thread-safe structure.
  3. on_connect now matches MQTTv311 4-arg signature.
  4. Removed any Streamlit imports — this module is pure Python and can be
     imported by streamlit_app.py without side-effects.

To test standalone:
    python mqtt_backend.py
"""

import json
import ssl
import threading
import time
import paho.mqtt.client as mqtt

APP_ID        = "ssr-baton-test"
MQTT_USERNAME = "ssr-baton-test@ttn"
MQTT_PASSWORD = "NNSXS.Q2TYZ6MNINBWG4MDDC7KOCWU3NRWIBKTU5QDGYA.ILKJTCXVLQ3BWHWYM2WTNMCJRMO4B7IJYQERVX5HOIQTAGRQOFQQ"
BROKER        = "nam1.cloud.thethings.network"
PORT          = 8883

# Correct topic: APP_ID@ttn is required by TTN v3
TOPIC = f"v3/{APP_ID}@ttn/devices/+/up"

_lock            = threading.Lock()
latest_messages  = []   # protected by _lock
connected        = False


def on_connect(client, userdata, flags, rc):
    """MQTTv311 on_connect — 4 positional args (no properties)."""
    global connected
    if rc == 0:
        print(f"[mqtt_backend] Connected. Subscribing to {TOPIC}")
        connected = True
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"[mqtt_backend] Connection failed, rc={rc}")


def on_message(client, userdata, message):
    print(f"[mqtt_backend] Message on {message.topic}: {message.payload[:120]}")
    try:
        payload = json.loads(message.payload.decode())
    except Exception:
        payload = {"raw": message.payload.decode()}

    with _lock:
        latest_messages.append(payload)
        if len(latest_messages) > 500:
            latest_messages.pop(0)


def get_messages():
    """Thread-safe snapshot of all received messages."""
    with _lock:
        return list(latest_messages)


def start_mqtt_background():
    """Connect and start the paho loop in a daemon thread. Returns the client."""
    client = mqtt.Client(
        client_id=f"newt-backend-{int(time.time())}",
        protocol=mqtt.MQTTv311,
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


# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Connecting to {BROKER}:{PORT} …")
    c = start_mqtt_background()
    try:
        while True:
            time.sleep(5)
            msgs = get_messages()
            print(f"Total messages received: {len(msgs)}")
            if msgs:
                print("Latest:", json.dumps(msgs[-1], indent=2)[:300])
    except KeyboardInterrupt:
        print("Stopping.")
        c.disconnect()