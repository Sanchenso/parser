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
