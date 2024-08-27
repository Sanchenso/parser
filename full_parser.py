import os
import subprocess

subprocess.call("python3 " + 'test_parser.py', shell=True)
subprocess.call("python3 " + 'NMEA_all.py', shell=True)

commands = [
    "python3 plot_parser_result.py",
    "python3 plot_parser_result_LED.py",
    "python3 plot_parser_result_Rssi.py",
]

# Start all processes simultaneously
processes = [subprocess.Popen(command, shell=True) for command in commands]

# Optionally, wait for all processes to complete
for process in processes:
    process.wait()

print("All scripts have completed.")


