// Baton Tracker Main IoT Project
// For Red Newt's Seneca7 Marathon
// Created by Andrew D'Onofrio (ajd323)

// -- Pre-Initialization -- //
// Definition Statements
#ifdef COMPILE_REGRESSION_TEST
#define FILLMEIN 0
#else
#define FILLMEIN 0
#warning "You must fill in your keys with the right values from the TTN control panel"
#endif
#ifndef LMIC_DEBUG_LEVEL
#define LMIC_DEBUG_LEVEL 2
#endif
#define LMIC_PRINTF_TO Serial
// Include Statements
#include <Arduino_LoRaWAN_ttn.h>
#include <lmic.h>
#include <hal/hal.h>
#include "keys.h"
// Variables and Structs
uint8_t batonID = 1;
uint64_t lastTime = 0;
uint32_t bufferLength = 8;
static uint8_t messageBuffer[8] = {0, 1, 2, 3, 4, 5, 6, 7};

// -- Callback Testing -- //
#ifdef __cplusplus
extern "C"{
#endif
void myStatusCallback(void * data, bool success){
  if(success){
    Serial.println("Uplink Succeeded");
  } else {
    Serial.prinln("Uplink Failed")
  }
}
#ifdef __cplusplus 
}
#endif


// -- Class Definitions -- //
class cMyLoRaWAN : public Arduino_LoRaWAN_ttn {
public:
    cMyLoRaWAN() {};
protected:
    virtual bool GetOtaaProvisioningInfo(Arduino_LoRaWAN::OtaaProvisioningInfo*) override;
    virtual void NetSaveSessionInfo(const SessionInfo &Info, const uint8_t *pExtraInfo, size_t nExtraInfo) override;
    virtual void NetSaveSessionState(const SessionState &State) override;
    virtual bool NetGetSessionState(SessionState &State) override;
    virtual bool GetAbpProvisioningInfo(Arduino_LoRaWAN::AbpProvisioningInfo*) override;
};
cMyLoRaWAN myLoRaWAN {};

// -- Pin Map -- //
const cMyLoRaWAN::lmic_pinmap myPinMap = {
     .nss = 8,
     .rxtx = cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN,
     .rst = 4,
     .dio = { 3, 6, cMyLoRaWAN::lmic_pinmap::LMIC_UNUSED_PIN },
     .rxtx_rx_active = 0,
     .rssi_cal = 0,
     .spi_freq = 8000000,
};

// -- Functions -- //
void setup() {
  Serial.begin(115200);
  while(!Serial);
  {
    uint64_t lt = millis();
    while(!Serial && millis() - lt < 5000);
  }
  myLoRaWAN.begin(myPinMap);
  Serial.print("LMIC radio init status: ");
  Serial.println(os_getTime());
  lastTime = millis();
  if(myLoRaWAN.IsProvisioned())
    Serial.println("Provisioned for something");
  else
    Serial.println("Not provisioned.");
    myLoRaWAN.SendBuffer((uint8_t *) &myPkt, sizeof(myPkt), myStatusCallback, NULL, false, 1);
}

void loop() {
  myLoRaWAN.loop();
  if (millis() - lastTime > 60000){
    Serial.println("Pass");
    messageBuffer[0]++;
    myPkt.batonID = batonID;
    myLoRaWAN.SendBuffer((uint8_t *) &myPkt, sizeof(myPkt), myStatusCallback, NULL, false, 1);
    lastTime = millis();
  }
}

bool
cMyLoRaWAN::GetOtaaProvisioningInfo(
    OtaaProvisioningInfo *pInfo
    ) {
      if (pInfo){
        memcpy_P(pInfo->AppEUI, APPEUI, 8);
        memcpy_P(pInfo->DevEUI, DEVEUI, 8);
        memcpy_P(pInfo->AppKey, APPKEY, 16);
      }
    return true;
}

void
cMyLoRaWAN::NetSaveSessionInfo(
    const SessionInfo &Info,
    const uint8_t *pExtraInfo,
    size_t nExtraInfo
    ) {
    (void)Info;
    (void)pExtraInfo;
    (void)nExtraInfo;
}

void
cMyLoRaWAN::NetSaveSessionState(const SessionState &State) {
    (void)State;
}

bool
cMyLoRaWAN::NetGetSessionState(SessionState &State) {
    (void)State;
    return false;
}

bool
cMyLoRaWAN::GetAbpProvisioningInfo(Arduino_LoRaWAN::AbpProvisioningInfo* Info){
  (void)Info;
  return false;
}