## LoRaWAN Tracker for Newt Racing Seneca 7
This is a post-processing graphical user interface (GUI) for Newt Racing's Seneca7 marathon trackers, provided by Cornell University's MAE 4220: Internet of Things Class

# From Device
 1. Packaging is Button Logic (1/0) and Baton ID, includes GPS and Time
 2. Sampling Every Minute (1/60 Hz)
 3. Hard-Code each Microcontroller with Baton ID (

# From Backend
JSON File from TTN Network -> Local, Dynamic Lists
 1. time_var (Undefined-length List) - 3-decimal places time from TTN
 2. baton_ID (Undefined-length List) - Single integer from pre-saved ID
 3. latt_var (Undefined-length List)
 4. Long_var (Undefined-length List)

Preset Variables -> Hard-Coded Lists
 1. run_ID (5-int List) - ID for Specific Devices and Groups
 2. pass_GPS_ranges (2x12 Matrix) - 6 Pass Zones Provided as Rectangular Limits (2x2)
 3. init_range (2x2 Matrix)




Sampling rate is everyminute
