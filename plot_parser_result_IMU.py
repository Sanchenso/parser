import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime
from filterpy.kalman import KalmanFilter
from scipy.fft import fft
from scipy.signal import stft
import numpy as np

# Создаем директорию для результатов, если её нет
if not os.path.exists('Result_CSV'):
    os.makedirs('Result_CSV')
if not os.path.exists('Result_Picture_IMU'):
    os.makedirs('Result_Picture_IMU')

dfMotor = pd.DataFrame()
dfRawAccelGyroData = pd.DataFrame()
dfRawAccelGyroDataAll = pd.DataFrame()

#columns_to_filter = ['accel_X', 'accel_Y', 'accel_Z']
columns_to_filter = ['gyro_X', 'gyro_Y', 'gyro_Z']

# Функция парсинга нескольких форматов даты и времени
def parse_multiple_formats(date_str):
    formats = ["%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S.%f"] 
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    print(f"Не удалось преобразовать: {date_str}")
    return pd.NaT

# Функция применения фильтра Калмана
def apply_kalman_filter(data, R=5, Q=1):
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.F = np.array([[1, 1], [0, 1]])  # Матрица перехода состояния
    kf.H = np.array([[1, 0]])          # Матрица измерений
    kf.P *= 1000.                      # Начальная ковариационная матрица ошибки
    kf.R = R                           # Ковариационная матрица измерений
    kf.Q = np.eye(2) * Q               # Ковариационная матрица процесса
    kf.x = np.array([0, 0])            # Начальное состояние

    filtered_data = []
    for z in data:
        kf.predict()
        kf.update([z])
        filtered_data.append(kf.x[0])
    return filtered_data

# Рекурсивная функция для работы с файлами в директориях
def process_directory(directory):
    for root, _, files in os.walk(directory):
        for binfile in files:
            if binfile.endswith('.bin'):
                print("Processing:", binfile)
                process_file(os.path.join(root, binfile))

def process_file(binfile):
    nameFile_int, nameFile_ext = os.path.splitext(os.path.basename(binfile))
    csv_file_RawAccelGyroData = nameFile_int + "_RawAccelGyroData.csv"
    command = f"./parser --print_entries {binfile} | rg RawAccelGyroData > {csv_file_RawAccelGyroData}"
    subprocess.run(command, shell=True)

    # Убираем временные файлы
    temp_files = [
        f"{nameFile_int}_flight_0.gscl",
        f"{nameFile_int}_flight_0.params",
        f"{nameFile_int}_channel_lua_125.dat",
        f"{nameFile_int}_channel_passports_124.dat",
        f"{nameFile_int}_channel_telemetry_123.dat"
    ]
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass  # Если файл не найден, ничего не делаем
    
    os.rename(csv_file_RawAccelGyroData, os.path.join('Result_CSV', csv_file_RawAccelGyroData))
    
    dfRawAccelGyroData = pd.read_csv(os.path.join('Result_CSV', csv_file_RawAccelGyroData), header=None, sep=' ', skiprows=1)
    dfRawAccelGyroData = dfRawAccelGyroData.rename(columns={0: 'Time', 2: 'accel_X', 3: 'accel_Y', 4: 'accel_Z', 6: 'gyro_X', 7: 'gyro_Y', 8: 'gyro_Z'})
    
    # Построение графиков
    fig, (ax_time, ax_freq, ax_spectr) = plt.subplots(3, 1, figsize=(12, 8))
    
    for column in columns_to_filter:
        print(column)
        output_dir = 'Result_Picture_IMU'
        output_path = os.path.join(output_dir, binfile)
        #dfRawAccelGyroData[f'{column}_filtered'] = apply_kalman_filter(dfRawAccelGyroData[column].values)  #применение Фильтра Калмана
        # Выполнение преобразования Фурье
        fft_values = np.fft.fft(dfRawAccelGyroData[column].values)
        N = len(fft_values)
        frequencies = np.fft.fftfreq(N, 0.002)
        positive_frequencies = frequencies[:N // 2]
        positive_fft_values = np.abs(fft_values[:N // 2])
        fs = 1 / np.mean(np.diff(dfRawAccelGyroData['Time'].values))  # Вычисляем частоту дискретизации
        f, t, Zxx = stft(dfRawAccelGyroData[column].values, fs=fs, nperseg=256, noverlap=128)
        
        Sxx = np.abs(Zxx) ** 2  # Вычисляем квадрат амплитуды для получения мощности
        #f, t, Sxx = signal.spectrogram(dfRawAccelGyroData[column].values, fs, nperseg=256, noverlap=128)

                        
        # График исходного сигнала во временной области
        ax_time.plot(dfRawAccelGyroData['Time'], dfRawAccelGyroData[column].values)
        #ax_time.set_title(f'{nameFile_int} - {column}')
        ax_time.set_title(f'{nameFile_int}')
        ax_time.set_xlabel('Sample')
        ax_time.set_ylabel('Amplitude')
        #ax_time.set_ylim(-3000, 3000)
        
        # График спектра в частотной области
        ax_freq.plot(positive_frequencies, positive_fft_values)
        #ax_freq.set_title(f'Frequency - {column}')
        ax_freq.set_title(f'Frequency')
        ax_freq.set_xlabel('Frequency')
        ax_freq.set_ylabel('Magnitude')
        #ax_freq.set_ylim(0, 300000)
        ax_freq.set_xlim(-1, 250)
        plt.tight_layout()
        
        # Построение спектрограммы
        #f, t, Sxx = signal.spectrogram(data, fs)
        pcm = ax_spectr.pcolormesh(t, f, Sxx, shading='gouraud')
        ax_spectr.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
        ax_spectr.set_title('Спектрограмма сигнала')
        ax_spectr.set_xlabel('Время [sec]')
        ax_spectr.set_ylabel('Частота [Hz]')
        #cbar = fig.colorbar(pcm, ax=ax_spectr)
        #cbar.set_label('Мощность/Частота (dB/Hz)')

        plt.tight_layout()
        # plt.savefig('Result_Picture_IMU/' + nameFile_int + '_accel_new.jpeg',dpi=100)
    plt.savefig(output_path + '_gyro_new.jpeg', dpi=200)
    #plt.show()
    plt.close()  
        
        
        #ax_spectr.pcolormesh(t, f, np.abs(Zxx), shading='gouraud', cmap='viridis')
        #ax_spectr.set_colorbars(label='Amplitude')
        #ax_spectr.ylim([20, fs/2])
        
process_directory(".")
     
            
           
        
        
'''
        time_format = mdates.DateFormatter('%H:%M:%S')
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')
        
        # accel_X
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('accel_X', fontsize=9)
        ax1.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_X'], label='accel_X', s=2)
        ax1.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_X'], linewidth=0.2)
        #ax1.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_X_filtered'], linewidth=0.4)
        ax1.set_ylabel('accel_X')
        ax1.xaxis.set_major_formatter(time_format)
        ax1.set_ylim(-10000, 10000)
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")

        # accel_Y
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_title('accel_Y', fontsize=9)
        ax2.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Y'], label='accel_Y', s=2)
        ax2.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Y'], linewidth=0.2)
        #ax2.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Y_filtered'], linewidth=0.2)
        ax2.set_ylabel('accel_Y')
        ax2.xaxis.set_major_formatter(time_format)
        ax2.set_ylim(-10000, 10000)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        
        # accel_Z
        ax3 = fig.add_subplot(3, 2, 5)
        ax3.set_title('accel_Z', fontsize=9)
        ax3.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Z'], label='accel_Z', s=2)
        ax3.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Z'], linewidth=0.2)
        #ax3.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['accel_Z_filtered'], linewidth=0.2)
        ax3.set_ylabel('accel_Z')
        ax3.xaxis.set_major_formatter(time_format)
        ax3.set_ylim(-10000, 10000)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")   
        
        # gyro_X
        ax4 = fig.add_subplot(3, 2, 2)
        ax4.set_title('gyro_X', fontsize=9)
        ax4.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_X'], label='gyro_X', s=2)
        ax4.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_X'], linewidth=0.2)
        #ax4.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_X_filtered'], linewidth=0.2)
        ax4.set_ylabel('gyro_X')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.set_ylim(-3000, 2000)
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(bbox_to_anchor=(1, 1), loc="upper left")

        # gyro_Y
        ax5 = fig.add_subplot(3, 2, 4)
        ax5.set_title('gyro_Y', fontsize=9)
        ax5.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Y'], label='gyro_Y', s=2)
        ax5.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Y'], linewidth=0.2)
        #ax5.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Y_filtered'], linewidth=0.2)
        ax5.set_ylabel('gyro_Y')
        ax5.xaxis.set_major_formatter(time_format)
        ax5.set_ylim(-3000, 2000)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(bbox_to_anchor=(1, 1), loc="upper left")
        
        # gyro_Z
        ax6 = fig.add_subplot(3, 2, 6)
        ax6.set_title('gyro_Z', fontsize=9)
        ax6.scatter(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Z'], label='gyro_Z', s=2)
        ax6.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Z'], linewidth=0.2)
        #ax6.plot(dfRawAccelGyroData['GPS_Time'], dfRawAccelGyroData['gyro_Z_filtered'], linewidth=0.2)
        ax6.set_ylabel('gyro_Z')
        ax6.xaxis.set_major_formatter(time_format)
        ax6.set_ylim(-3000, 2000)
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.legend(bbox_to_anchor=(1, 1), loc="upper left")          
        
        plt.savefig('Result_Picture_IMU/' + binfile[:-4], dpi=300)
        #plt.show()
'''
        
        
