/**
 * uplink_decoder.js  —  TTN v3 Payload Formatter
 * ------------------------------------------------
 * Paste this into The Things Network Console:
 *   Application → "ssr-baton-test" → Payload formatters → Uplink → Custom Javascript formatter
 *
 * FIX SUMMARY (vs original uplink_decoder.java):
 *   1. File renamed .java → .js  (TTN uses JavaScript, not Java)
 *   2. Byte offsets corrected to match the Arduino struct layout:
 *
 *      struct BatonPacket {
 *          uint8_t batonID;       // b[0]        (1 byte)
 *          uint8_t racerNumber;   // b[1]         (1 byte)
 *          // compiler adds 2 padding bytes here on 32-bit ARM for float alignment
 *          float   latitude;      // b[4..7]      (4 bytes, little-endian)
 *          float   longitude;     // b[8..11]     (4 bytes, little-endian)
 *          float   battery;       // b[12..15]    (4 bytes, little-endian)
 *      }  // total: 16 bytes  (with padding)
 *
 *   The original decoder was already correct for the offsets — BUT only works
 *   if the Arduino compiler inserts the 2-byte padding after racerNumber.
 *   This is true for ARM Cortex-M (Adafruit Feather M0) but NOT for AVR
 *   (Arduino Uno/Mega) which packs structs tightly.
 *
 *   If you see garbage lat/lon, switch to the PACKED version below.
 */

// ── PADDED version (ARM Cortex-M / Adafruit Feather M0) ──────────────────
function decodeUplink(input) {
  var b = input.bytes;

  // Minimum expected payload size: 16 bytes (padded struct)
  if (b.length < 16) {
    return { errors: ["Payload too short: got " + b.length + " bytes, need 16"] };
  }

  function f32(b0, b1, b2, b3) {
    var buf  = new ArrayBuffer(4);
    var view = new DataView(buf);
    view.setUint8(0, b0);
    view.setUint8(1, b1);
    view.setUint8(2, b2);
    view.setUint8(3, b3);
    return view.getFloat32(0, true);  // little-endian
  }

  var lat  = f32(b[4],  b[5],  b[6],  b[7]);
  var lon  = f32(b[8],  b[9],  b[10], b[11]);
  var batt = f32(b[12], b[13], b[14], b[15]);

  // Basic sanity checks
  var warnings = [];
  if (lat === 1.0 && lon === 1.0) {
    warnings.push("lat/lon are placeholder values (1.0) — GPS not yet implemented in firmware");
  }
  if (lat < -90 || lat > 90)  warnings.push("latitude out of range: " + lat);
  if (lon < -180 || lon > 180) warnings.push("longitude out of range: " + lon);

  return {
    data: {
      batonID:     b[0],
      racerNumber: b[1],
      latitude:    Math.round(lat  * 1e6) / 1e6,
      longitude:   Math.round(lon  * 1e6) / 1e6,
      battery:     Math.round(batt * 100) / 100
    },
    warnings: warnings
  };
}

/*
 * ── PACKED version — use this if lat/lon are garbage on ARM ──────────────
 * Uncomment and replace the function above if the struct is packed
 * (i.e. __attribute__((packed)) is used in the Arduino code, or you're
 * running on AVR):
 *
 * struct BatonPacket {          // packed — no padding
 *     uint8_t batonID;          // b[0]
 *     uint8_t racerNumber;      // b[1]
 *     float   latitude;         // b[2..5]
 *     float   longitude;        // b[6..9]
 *     float   battery;          // b[10..13]
 * }                             // total: 14 bytes

function decodeUplink(input) {
  var b = input.bytes;
  if (b.length < 14) {
    return { errors: ["Payload too short: got " + b.length + " bytes, need 14"] };
  }
  function f32(b0, b1, b2, b3) {
    var buf = new ArrayBuffer(4);
    var view = new DataView(buf);
    view.setUint8(0, b0); view.setUint8(1, b1);
    view.setUint8(2, b2); view.setUint8(3, b3);
    return view.getFloat32(0, true);
  }
  return {
    data: {
      batonID:     b[0],
      racerNumber: b[1],
      latitude:    Math.round(f32(b[2],  b[3],  b[4],  b[5])  * 1e6) / 1e6,
      longitude:   Math.round(f32(b[6],  b[7],  b[8],  b[9])  * 1e6) / 1e6,
      battery:     Math.round(f32(b[10], b[11], b[12], b[13]) * 100) / 100
    }
  };
}
*/