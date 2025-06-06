import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft
import subprocess
import argparse
import os


class SecondOrderFilter:
    MAX_N = 16
    MASK = MAX_N - 1
    D = 7

    def __init__(self):
        self.counter = 0
        self.n0 = 1
        self.n1 = 1
        self.sum0 = np.zeros(self.D, dtype=int)
        self.sum1 = np.zeros(self.D, dtype=int)
        self.buffer0 = np.zeros((self.MAX_N, self.D), dtype=int)
        self.buffer1 = np.zeros((self.MAX_N, self.D), dtype=int)

    def config(self, n0, n1):
        """Configure the filter with specific n0 and n1 parameters."""
        self.n0 = max(1, min(n0, self.MAX_N))
        self.n1 = max(1, min(n1, self.MAX_N))

    def scale(self):
        """Return the scaling factor of the filter."""
        return self.n0 * self.n1

    def update(self, mpu_data):
        """Update the filter with new data from MPU and return filtered output."""
        current = self.counter & self.MASK
        prev0 = (self.counter - self.n0) & self.MASK
        prev1 = (self.counter - self.n1) & self.MASK
        den = self.scale()
        out = np.zeros(self.D, dtype=int)

        for i in range(self.D):
            self.sum0[i] += mpu_data[i]
            y = self.sum0[i] - self.buffer0[prev0][i]
            self.buffer0[current][i] = self.sum0[i]
            self.sum1[i] += y
            out[i] = (self.sum1[i] - self.buffer1[prev1][i]) // den
            self.buffer1[current][i] = self.sum1[i]

        self.counter += 1
        return out


def parse_log(file_path):
    data = {'accel_x': [], 'accel_y': [], 'accel_z': [], 'gyro_x': [], 'gyro_y': [], 'gyro_z': []}
    nameFile_int, nameFile_ext = os.path.splitext(file_path)
    csv_file_RawAccelGyroData = nameFile_int + "_RawAccelGyroData.txt"
    is_windows = os.name == 'nt'
    parser_command = "./parser.exe" if is_windows else "./parser"
    command = f"{parser_command} --print_entries {file_path} | rg RawAccelGyroData > {csv_file_RawAccelGyroData}"
    #command = f"{parser_command} --print_entries {file_path} | grep RawAccelGyroData > {csv_file_RawAccelGyroData}"
    #command = f"powershell -Command \"{parser_command} --print_entries {file_path} | Select-String RawAccelGyroData > {csv_file_RawAccelGyroData}\""
    subprocess.run(command, shell=True)

    with open(csv_file_RawAccelGyroData, 'r') as file:
        line_counter = 0
        for line in file:
            match = re.search(r'RawAccelGyroData\s([\d-]+)\s([\d-]+)\s([\d-]+)\s([\d-]+)\s([\d-]+)\s([\d-]+)\s([\d-]+)',
                              line)
            if match:
                #line_counter += 1
                #if line_counter <= 10000:
                #    continue
                accel_x, accel_y, accel_z, _, gyro_x, gyro_y, gyro_z = match.groups()
                # gyro_x, gyro_y, gyro_z, _, _, _, _ = match.groups()
                data['accel_x'].append(int(accel_x))
                data['accel_y'].append(int(accel_y))
                data['accel_z'].append(int(accel_z))
                data['gyro_x'].append(int(gyro_x))
                data['gyro_y'].append(int(gyro_y))
                data['gyro_z'].append(int(gyro_z))
    return data


def apply_filter(data):
    filter_obj = SecondOrderFilter()
    filter_obj.config(4, 4)  # Example: setting n0 and n1 both to 4
    filtered_data = {'accel_x': [], 'accel_y': [], 'accel_z': [], 'gyro_x': [], 'gyro_y': [], 'gyro_z': []}

    for i in range(len(data['gyro_x'])):
        input_data = [data['gyro_x'][i], data['gyro_y'][i], data['gyro_z'][i], 0, data['accel_x'][i], data['accel_y'][i], data['accel_z'][i]]
        filtered_output = filter_obj.update(input_data)
        filtered_data['accel_x'].append(filtered_output[4])
        filtered_data['accel_y'].append(filtered_output[5])
        filtered_data['accel_z'].append(filtered_output[6])
        filtered_data['gyro_x'].append(filtered_output[0])
        filtered_data['gyro_y'].append(filtered_output[1])
        filtered_data['gyro_z'].append(filtered_output[2])

    return filtered_data


def perform_fft_analysis(data_raw, data_filtered, logfile_name):
    output_path = os.path.join(output_dir, logfile_name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, axs = plt.subplots(2, 3, figsize=(15, 10))  
    axes = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    for i, axis in enumerate(axes):
        # Raw data
        signal_raw = data_raw[axis]
        N_raw = len(signal_raw)
        T = 1.0 / 500.0  # Assuming a sample rate of 500 Hz (adjust according to your actual data)
        x_raw = np.linspace(0.0, N_raw * T, N_raw, endpoint=False)
        y_raw = np.array(signal_raw)
        yf_raw = fft(y_raw)

        xf_raw = np.fft.fftfreq(N_raw, T)[:N_raw // 2]

        # Filtered data
        signal_filtered = data_filtered[axis]
        N_filtered = len(signal_filtered)
        y_filtered = np.array(signal_filtered)
        yf_filtered = fft(y_filtered)
        xf_filtered = np.fft.fftfreq(N_filtered, T)[:N_filtered // 2]

        # Plot the results
        row, col = divmod(i, 3)
        axs[row, col].plot(xf_raw, 2.0 / N_raw * np.abs(yf_raw[:N_raw // 2]), label='Raw Data')
        axs[row, col].plot(xf_filtered, 2.0 / N_filtered * np.abs(yf_filtered[:N_filtered // 2]), label='Filtered Data')
        axs[row, col].set_title(f'{logfile_name} - {axis}')
        axs[row, col].set_xlabel('Frequency (Hz)')
        axs[row, col].set_ylabel('Amplitude')
        axs[row, col].legend()
        axs[row, col].grid()
        if i < 3:
            axs[row, col].set_ylim(0, 80)
        else:
            axs[row, col].set_ylim(0, 15)
        
    plt.tight_layout()  # Для улучшения расположения подграфиков
    #plt.savefig('Result_Picture_IMU/' + logfile_name + '_accel_new.jpeg',dpi=200)
    plt.savefig(output_path + '_accel_new.jpeg', dpi=200)
    #plt.show()
    plt.close()
    try:
        os.remove(args.logfile[:-4] + "_flight_0.gscl")
        os.remove(args.logfile[:-4] + "_flight_0.params")
        os.remove(args.logfile[:-4] + "_RawAccelGyroData.txt")
    except FileNotFoundError as e:
        print(f"Error while trying to remove or rename a file: {e}")
       
if __name__ == '__main__':
    output_dir = 'Result_Picture_IMU'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    parser = argparse.ArgumentParser(description="Analyze IMU data from log file.")
    parser.add_argument('logfile', metavar='logfile', type=str, help='Path to the .bin log file')
    args = parser.parse_args()
    #logfile_name = args.logfile[:-4]
    logfile_name = os.path.splitext(args.logfile)[0]
    print(logfile_name)
    data = parse_log(args.logfile)
    filtered_data = apply_filter(data)
    perform_fft_analysis(data, filtered_data, args.logfile)
