# LoRaWAN Tracker for Newt Racing Seneca 7
This is a post-processing graphical user interface (GUI) for Newt Racing's Seneca7 marathon trackers, provided by Cornell University's MAE 4220: Internet of Things Class

## From Device
*Loaded onto the "Baton_Tracker_Code"*
 1. Packaging is Button Logic (1/0) and Baton ID, includes GPS and Time
 2. Sampling Every Minute (1/60 Hz)
 3. Hard-Code each Microcontroller with Baton ID (Integer)

## From Backend
*JSON File from TTN Network -> Local, Dynamic Lists*
 1. time_var (Undefined-length List) - 2-decimal (~0.5 seconds) places time from TTN
 2. baton_ID (Undefined-length List) - Single integer from pre-saved ID
 3. latt_var (Undefined-length List) - 5-decimal (~30-feet) places from TTN
 4. long_var (Undefined-length List) - 5-decimal (~30-feet) places from TTN

*Preset Variables -> Hard-Coded Lists*
 1. run_ID (5-int List) - ID for Specific Devices and Groups
 2. pass_GPS_ranges (2x12 Matrix) - 6 Pass Zones Provided as Rectangular Limits (2x2)
 3. init_range (2x2 Matrix) - Scope of the the TTN Map 

*State Variables -> Continously Calculated Conditions*
 1. run_team_pace (2xX Matrix, Time-Dependent) - Instantaneous Total Distance / Total Time, inclduing the timestamp and the mile time (minutes)
 2. run_runner_pace (2xX Matrix, Time-Dependent) - Instantaneous Runner Distance / Runenr Time, inclduing the timestamp and the mile time (minutes)
