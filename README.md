# parser
parsing data for autopilot

Put in the logs folder and run. 
The folder should contain "parser"

## Analyse IMU:
### 1. Building a signal spectrogram of the Giroscope Data
argument - none

example usage: 
python3 plot_parser_result_IMU.py

### 2. Visual evaluation of the autopilot filter for the accelerometer and gyroscope data
argument - name of the log

example usage:
python3 main.py test.bin

## Analyse Navigation:
### 1. Formatting data from the log:
argument - none 

example usage: 
python3 test_parser.py

### 2. Analyse Navigation data from NMEA: 
argument - none 

example usage: 
python3 NMEA_all.py

### 3. Analyse Navigation data from NMEA: 
Plotting six graphs, including SNR, altitude, speeds, correction lifetime, navigation status, and navigational accuracy
argument - none 

example usage: 
python3 plot_parser_result.py
