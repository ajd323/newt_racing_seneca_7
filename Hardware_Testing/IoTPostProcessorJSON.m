clear;
clc;

% Opening File
folder_general = "/Users/andrewj.donofrio/Desktop/IoT Labs/IoT_Lab_5";
fileName = "myData_Main.txt";
fullFilePath = fullfile(folder_general, fileName);
fid = fopen(fullFilePath, "r");

% Creating the Storage Methods
times = [];
digitalTemps = [];
thermTemps = [];
lineErrors = 0;
line = fgets(fid);

% Extracting Information
while ischar(line)
    try
        if contains(line, "b'{")
            % Reformatting the JSON File
            jsonString = extractBetween(line, "b'", "'");
            jsonString = char(jsonString);
            js = jsondecode(jsonString);
            nt = datetime(js.received_at, ...
                "InputFormat",'yyyy-MM-dd''T''HH:mm:ss.SSSSSSSSSZ', ...
                "TimeZone",'America/New_York');
            % Reading the Temperature Values
            digitalTemp = js.uplink_message.decoded_payload.digitalTempC;
            thermTemp = js.uplink_message.decoded_payload.thermistorTempC;
            % Appending Process
            times = [times; nt];
            digitalTemps = [digitalTemps; digitalTemp];
            thermTemps = [thermTemps; thermTemp];
        end
    catch
        lineErrors = lineErrors + 1;
    end
    line = fgets(fid);
end

fclose(fid);
disp("Line errors: " + lineErrors);

% Plotting
figure;
plot(times, digitalTemps);
hold on;
title("Digital and Thermistor Temperature Reading (C) vs. Time (s) from JSON")
plot(times, thermTemps);
legend("Digital Temp (C)", "Thermistor Temp (C)");
xlabel("Time");
ylabel("Temperature (°C)");
ylim([0 50]);
grid on;