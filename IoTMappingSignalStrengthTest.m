clc;
clear;
clearvars;

%% Importing Data

folder_general = '/Users/andrewj.donofrio/Desktop/NEW_DEBUT_TEST';
Test_One = fullfile(folder_general, 'Test_Lat_Long_Data.CSV');
data = readtable(Test_One);

%% Formatting
% Extract data
lat  = data.Lattitude;
lon  = data.Longitude;
rssi = data.RSSI;

% Create geographic figure
figure
gx = geoaxes;
geobasemap(gx, 'satellite')
hold on

% Plot heatmap-like dots
geoscatter(gx, lat, lon, ...
    30, ...                % marker size
    rssi, ...         % color by RSSI
    'filled')

% Colorbar
cb = colorbar;
cb.Label.String = 'Normalized RSSI';

% Title
title('Satellite Signal Strength Density Map')

% Improve visibility
set(gx, 'FontSize', 12)
geolimits([42.4425 42.44625],[-76.48375 -76.48125])
title("Signal Strenght Upson Hall Test #1")
