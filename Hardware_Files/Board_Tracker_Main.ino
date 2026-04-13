// Board_Tracker_Main.ino
// Baton Tracker — Newt Racing Seneca 7
// Cornell MAE 4220 IoT
// Author: Andrew D'Onofrio (ajd323)
// NOTE BUTTON LOGIC (PRESSED = 0, NOT PRESSED = 1)

// ── Pre-Initialization ──
#define LMIC_DEBUG_LEVEL 2
#define LMIC_PRINTF_TO Serial
#ifdef COMPILE_REGRESSION_TEST
#define FILLMEIN 0
#else
#define FILLMEIN (#Don't edit this stuff. Fill in the appropriate FILLMEIN values.)
#warning "You must fill in your keys with the right values from the TTN control panel"
#endif

// ── Includes ──
#include <Arduino_LoRaWAN_ttn.h>
#include <lmic.h>
#include <hal/hal.h>
#include "keys.h"

// ── Baton Constants ──
const uint8_t BATON_ID = 1;

// ── Button Constants ──
const int OUTPUT_PIN = 12;
const int BUTTON_PIN = 10;
bool buttonState = true;
int buttonPressed = 0;

// ── Buffer Constants ──
uint64_t lastTime = 0;
uint32_t bufferLength = 8;
static uint8_t messageBuffer[8] = {0, 1, 2, 3, 4, 5, 6, 7};
const unsigned long buffer_interval = 30000;

#ifdef __cplusplus
extern "C" {
#endif

struct __attribute__((packed)) BatonPacket {
  uint8_t batonID;
  int buttonPressed;
  float latitude;
  float longitude;
} myPkt;

void myStatusCallback(void * data, bool success){
  if(success)
    Serial.println("Succeeded!");
  else
    Serial.println("Failed!");
}

#ifdef __cplusplus 
}
#endif

// ── LoRaWAN class ──
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

// ── Pin Map ──
const cMyLoRaWAN::lmic_pinmap myPinMap = {
  .nss = 8,
  .rxtx = cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN,
  .rst = 4,
  .dio = { 3, 6, cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN },
  .rxtx_rx_active = 0,
  .rssi_cal = 0,
  .spi_freq = 8000000,
};

// ── Setup ──
void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, HIGH);
  buttonState = true;
  {
    uint64_t lt = millis();
    while(!Serial && millis() - lt < 5000);
  }
  myLoRaWAN.begin(myPinMap);
  Serial.println("LMIC radio init status: ");
  Serial.println(os_getTime());
  lastTime = millis();
  Serial.println("Serial begin");
  
  if(myLoRaWAN.IsProvisioned()){
    Serial.println("Provisioned for something");
  }else{
    Serial.println("Not provisioned.");
    myLoRaWAN.SendBuffer((uint8_t *) &myPkt, sizeof(myPkt), myStatusCallback, NULL, false, 1);
  }
}

// ── Loop ──
void loop() {
  myLoRaWAN.loop();
  
  // Check if buffer interval has elapsed
  if (millis() - lastTime > buffer_interval){
    // If button was pressed during the interval, update the count
    if(buttonState == 0){  // FIXED: was = instead of ==
      buttonPressed++;
    }
    
    messageBuffer[0]++; 
    sendPacket();
    lastTime = millis();
    buttonState = true;  // Reset button state for next interval
  }
  
  // Monitor button press during interval
  if(buttonState){ // True = 1, Not Pressed
    buttonState = (digitalRead(BUTTON_PIN) == HIGH);
    if(!buttonState){
      Serial.println("Button Pressed Within Interval");
    }
  }
}

// ── LoRaWAN Provisioning Stubs ──
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

// ── Helpers ──
void sendPacket() {
  myPkt.batonID = BATON_ID;
  myPkt.buttonPressed = buttonPressed;
  myPkt.latitude = 42.4440f;
  myPkt.longitude = -76.5019f;

  Serial.print("Baton ID = ");
  Serial.print(myPkt.batonID);
  Serial.print(" Button Pressed = ");
  Serial.print(myPkt.buttonPressed);
  Serial.print(" Lat. = ");
  Serial.print(myPkt.latitude, 6);
  Serial.print(" Long. = ");
  Serial.println(myPkt.longitude, 6);

  myLoRaWAN.SendBuffer(
    (uint8_t*)&myPkt, sizeof(myPkt),
    myStatusCallback, nullptr, false, 1
  );
}