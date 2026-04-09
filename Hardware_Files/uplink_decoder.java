function decodeUplink(input) {
  var b = input.bytes;

  function f32(b0,b1,b2,b3){
    var buf = new ArrayBuffer(4);
    var view = new DataView(buf);
    view.setUint8(0,b0);
    view.setUint8(1,b1);
    view.setUint8(2,b2);
    view.setUint8(3,b3);
    return view.getFloat32(0,true); // little-endian
  }

  return {
    data: {
      batonID: b[0],
      latitude:  f32(b[1], b[2], b[3], b[4]),
      longitude: f32(b[5], b[6], b[7], b[8]),
      battery:   f32(b[9], b[10], b[11], b[12])
    }
  };
}
