function decodeUplink(input) {
  var b = input.bytes;
  var view = new DataView(new Uint8Array(b).buffer);
  return {
    data: {
      batonID:       b[0],
      buttonPressed: view.getInt32(1, true),
      latitude:      view.getFloat32(5, true),
      longitude:     view.getFloat32(9, true),
    }
  };
}