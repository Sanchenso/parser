# parser
parsing data for autopilot

Put in the logs folder and run. 
The folder should contain "parser"

## Update system (windows)
Open PowerShell as root in the folder with install-rg.ps1 and requirements.txt. Run install: 

`./install-rg.ps1`

## Analyse IMU (windows)
### 1. Building a signal spectrogram of the Giroscope Data
argument - none

The folder must contain maip.py , plot_parser_result_IMU.py , parser.exe, logs

example usage: 

`python plot_parser_result_IMU.py`

### 2. Visual evaluation of the autopilot filter for the accelerometer and gyroscope data 
argument - name of the log

example usage:

`python main.py test.bin`

## Analyse Navigation (linux):
### 1. Formatting data from the log:
argument - none 

example usage: 

`python3 test_parser.py`

### 2. Analyse Navigation data from NMEA: 
script - https://github.com/Sanchenso/NMEA
argument - none 

example usage: 

`python3 NMEA_all.py`

### 3. Analyse Navigation data from NMEA: 
Plotting six graphs, including SNR, altitude, speeds, rtkAGE, navigation status, and navigational accuracy
argument - none 

example usage: 

`python3 plot_parser_result.py`

if there is no raw navigation data (NMEA), then use this:

`python3 plot_parser_result_noGNSS.py`
