// Board_Tracker_Main.ino
// Baton Tracker — Newt Racing Seneca 7
// Cornell MAE 4220 IoT
// Author: Andrew D'Onofrio (ajd323)
//
// FIX SUMMARY (vs original):
//   1. GPS is NOT wired up — latitude/longitude are hardcoded to 1.0f as
//      placeholders.  Added clear TODO markers and a commented example of
//      how to integrate a GPS module (TinyGPSPlus + Serial2).
//   2. Added software button debounce (50 ms) to prevent false racer-number
//      increments from contact bounce.
//   3. Serial wait loop was potentially infinite on boards without USB CDC
//      auto-detect; added a 5-second total timeout.
//   4. Corrected: lastTime initialized after LoRaWAN begin (not before),
//      so the first 60-second window is accurate.

// ── Pre-Initialization ────────────────────────────────────────────────────
#ifdef COMPILE_REGRESSION_TEST
  #define FILLMEIN 0
#else
  #define FILLMEIN 0
  #warning "Fill in your TTN keys in keys.h"
#endif

#ifndef LMIC_DEBUG_LEVEL
  #define LMIC_DEBUG_LEVEL 2
#endif
#define LMIC_PRINTF_TO Serial

// ── Includes ─────────────────────────────────────────────────────────────
#include <Arduino_LoRaWAN_ttn.h>
#include <lmic.h>
#include <hal/hal.h>
#include "keys.h"

// TODO: Uncomment these two lines when a GPS module is wired to Serial1/Serial2
// #include <TinyGPSPlus.h>
// TinyGPSPlus gps;

// ── Constants ─────────────────────────────────────────────────────────────
const int    BUTTON_PIN       = 10;
const int    MAX_RACER        = 7;
const unsigned long TX_INTERVAL_MS  = 60000UL;   // 1 minute
const unsigned long DEBOUNCE_MS     =    50UL;   // button debounce window

// ── Packet structure ──────────────────────────────────────────────────────
// IMPORTANT: the TTN uplink decoder (uplink_decoder.js) assumes ARM Cortex-M
// struct padding.  The layout is:
//   [0]    batonID      (uint8)
//   [1]    racerNumber  (uint8)
//   [2-3]  padding      (2 bytes, added by ARM compiler for float alignment)
//   [4-7]  latitude     (float, little-endian)
//   [8-11] longitude    (float, little-endian)
//   [12-15] battery     (float, little-endian)
// Total transmitted: 16 bytes
struct BatonPacket {
    uint8_t batonID;
    uint8_t racerNumber;
    float   latitude;
    float   longitude;
    float   battery;
} myPkt;

// ── State ─────────────────────────────────────────────────────────────────
const uint8_t BATON_ID   = 1;   // hard-code per device
uint8_t       racerNumber = 1;

bool          lastButtonState   = HIGH;
unsigned long lastDebounceTime  = 0;
bool          pendingButtonRead = HIGH;

unsigned long lastTxTime = 0;

// ── LoRaWAN class ────────────────────────────────────────────────────────
class cMyLoRaWAN : public Arduino_LoRaWAN_ttn {
public:
    cMyLoRaWAN() {}
protected:
    virtual bool GetOtaaProvisioningInfo(Arduino_LoRaWAN::OtaaProvisioningInfo*) override;
    virtual void NetSaveSessionInfo(const SessionInfo&, const uint8_t*, size_t) override;
    virtual void NetSaveSessionState(const SessionState&) override;
    virtual bool NetGetSessionState(SessionState&) override;
    virtual bool GetAbpProvisioningInfo(Arduino_LoRaWAN::AbpProvisioningInfo*) override;
};
cMyLoRaWAN myLoRaWAN {};

// ── Pin map (Adafruit Feather M0 LoRa) ───────────────────────────────────
const cMyLoRaWAN::lmic_pinmap myPinMap = {
    .nss            = 8,
    .rxtx           = cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN,
    .rst            = 4,
    .dio            = { 3, 6, cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN },
    .rxtx_rx_active = 0,
    .rssi_cal       = 0,
    .spi_freq       = 8000000,
};

// ── Uplink callback ──────────────────────────────────────────────────────
#ifdef __cplusplus
extern "C" {
#endif
void myStatusCallback(void* data, bool success) {
    Serial.println(success ? "Uplink OK" : "Uplink FAILED");
}
#ifdef __cplusplus
}
#endif

// ── Helpers ───────────────────────────────────────────────────────────────
float readBatteryVoltage() {
    // Feather M0: battery divider on A9 (pin 9)
    // Vbatt = analogRead(A9) * 2 * 3.3 / 1024
    float measured = analogRead(A9) * (2.0f * 3.3f / 1024.0f);
    return measured;
}

void sendPacket() {
    // TODO: replace 1.0f placeholders with real GPS data when module is wired:
    //
    //   while (Serial1.available()) gps.encode(Serial1.read());
    //   if (gps.location.isValid()) {
    //       myPkt.latitude  = (float)gps.location.lat();
    //       myPkt.longitude = (float)gps.location.lng();
    //   }

    myPkt.batonID     = BATON_ID;
    myPkt.racerNumber = racerNumber;
    myPkt.latitude    = 1.0f;    // TODO: replace with gps.location.lat()
    myPkt.longitude   = 1.0f;   // TODO: replace with gps.location.lng()
    myPkt.battery     = readBatteryVoltage();

    Serial.print("Sending packet — baton=");
    Serial.print(myPkt.batonID);
    Serial.print(" racer=");
    Serial.print(myPkt.racerNumber);
    Serial.print(" lat=");
    Serial.print(myPkt.latitude, 6);
    Serial.print(" lon=");
    Serial.print(myPkt.longitude, 6);
    Serial.print(" batt=");
    Serial.println(myPkt.battery, 2);

    myLoRaWAN.SendBuffer(
        (uint8_t*)&myPkt, sizeof(myPkt),
        myStatusCallback, nullptr, false, 1
    );
}

// ── Setup ─────────────────────────────────────────────────────────────────
void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    Serial.begin(115200);

    // Wait for Serial — timeout after 5 s so the board works without USB
    unsigned long t0 = millis();
    while (!Serial && millis() - t0 < 5000) {}

    // TODO: start GPS serial when module is wired
    // Serial1.begin(9600);

    myLoRaWAN.begin(myPinMap);
    Serial.print("LMIC time: "); Serial.println(os_getTime());
    Serial.println(myLoRaWAN.IsProvisioned() ? "Provisioned (OTAA)" : "Not provisioned.");

    lastTxTime = millis();
    sendPacket();   // send immediately on boot
}

// ── Loop ──────────────────────────────────────────────────────────────────
void loop() {
    myLoRaWAN.loop();

    // ── Debounced button read ───────────────────────────────────────────
    bool reading = digitalRead(BUTTON_PIN);
    if (reading != pendingButtonRead) {
        lastDebounceTime = millis();
        pendingButtonRead = reading;
    }
    if (millis() - lastDebounceTime > DEBOUNCE_MS) {
        // State has been stable for DEBOUNCE_MS
        if (lastButtonState == HIGH && pendingButtonRead == LOW) {
            // Rising edge (press)
            racerNumber = (racerNumber % MAX_RACER) + 1;
            Serial.print("Racer number → "); Serial.println(racerNumber);
        }
        lastButtonState = pendingButtonRead;
    }

    // ── Periodic uplink ────────────────────────────────────────────────
    if (millis() - lastTxTime >= TX_INTERVAL_MS) {
        sendPacket();
        lastTxTime = millis();
    }
}

// ── LoRaWAN provisioning stubs ───────────────────────────────────────────
bool cMyLoRaWAN::GetOtaaProvisioningInfo(OtaaProvisioningInfo* pInfo) {
    if (pInfo) {
        memcpy_P(pInfo->AppEUI, APPEUI, 8);
        memcpy_P(pInfo->DevEUI, DEVEUI, 8);
        memcpy_P(pInfo->AppKey, APPKEY, 16);
    }
    return true;
}
void cMyLoRaWAN::NetSaveSessionInfo(const SessionInfo&, const uint8_t*, size_t) {}
void cMyLoRaWAN::NetSaveSessionState(const SessionState&) {}
bool cMyLoRaWAN::NetGetSessionState(SessionState& State) { return false; }
bool cMyLoRaWAN::GetAbpProvisioningInfo(Arduino_LoRaWAN::AbpProvisioningInfo*) { return false; }