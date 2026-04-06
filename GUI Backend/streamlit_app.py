import streamlit as st
import pandas as pd
import pydeck as pdk
from mqtt_listener import start_mqtt

st.set_page_config(page_title="Baton Tracker Dashboard", layout="wide")

# Start MQTT listener
start_mqtt()

st.title("🏃 Baton Tracker — Live Race Dashboard")

# Extract decoded data into a DataFrame
def build_dataframe():
    rows = []
    for msg in st.session_state.messages:
        try:
            d = msg["uplink_message"]["decoded_payload"]
            rows.append({
                "batonID": d["batonID"],
                "lat": d["latitude"],
                "lon": d["longitude"],
                "battery": d["battery"],
                "timestamp": msg["received_at"]
            })
        except KeyError:
            continue
    return pd.DataFrame(rows)

df = build_dataframe()

# If no data yet
if df.empty:
    st.info("Waiting for live data from TTN…")
    st.stop()

# Sidebar: Baton selector
batons = sorted(df["batonID"].unique())
selected_baton = st.sidebar.selectbox("Select Baton", batons)

df_baton = df[df["batonID"] == selected_baton]

# Battery indicator
latest = df_baton.tail(1).iloc[0]
st.metric(
    label=f"Baton {selected_baton} Battery",
    value=f"{latest.battery:.2f} V"
)

# Map
st.subheader("Live GPS Map")
layer = pdk.Layer(
    "ScatterplotLayer",
    df_baton,
    get_position='[lon, lat]',
    get_color='[255, 0, 0]',
    get_radius=40,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=latest.lat,
            longitude=latest.lon,
            zoom=12,
            pitch=0,
        )
    )
)

# Recent uplinks
st.subheader("Recent Uplinks")
st.dataframe(df_baton.sort_values("timestamp", ascending=False).head(20))