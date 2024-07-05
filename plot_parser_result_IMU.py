import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime
from filterpy.kalman import KalmanFilter
import numpy as np

dfRawAccelGyroData = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)

columns_to_filter = ['accel_X', 'accel_Y', 'accel_Z', 'gyro_X', 'gyro_Y', 'gyro_Z']

if not os.path.exists('Result_Picture_IMU'):
    os.makedirs('Result_Picture_IMU')

# Определение функции для парсинга нескольких форматов даты и времени
def parse_multiple_formats(date_str):
    formats = ["%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S.%f"] 
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    print(f"Не удалось преобразовать: {date_str}")  # Вывод строки, которая не подошла ни под один формат
    return pd.NaT  # Если ни один формат не подошел, возвращаем NaT

def apply_kalman_filter(data, R=5, Q=1):
    """
    R (float): Ковариация измерений.
    Q (float): Ковариация процесса
    """
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

for binfile in os.listdir():
    if binfile[-4:] == '.bin':
        print(binfile)
        prefix = binfile[:-4]
        files_with_prefix = [file for file in files_in_path if file.startswith(prefix)]
        for i in files_with_prefix:
            if '_RawAccelGyroData.csv' in i:
                dfRawAccelGyroData = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfRawAccelGyroData['GPS_Time'] = dfRawAccelGyroData['GPS_Time'].apply(parse_multiple_formats)                
                for column in columns_to_filter:
                    #dfRawAccelGyroData[f'{column}_filtered'] = apply_kalman_filter(dfRawAccelGyroData[column].values)  #применение Фильтра Калмана
                     # Выполнение преобразования Фурье
                    fft_values = np.fft.fft(dfRawAccelGyroData[column].values)
                    frequencies = np.fft.fftfreq(len(fft_values), 0.002)

        


                    # Построение графиков исходного сигнала и спектра
                    fig, (ax_time, ax_freq) = plt.subplots(2, 1, figsize=(12, 8))
                            
                    # График исходного сигнала во временной области
                    ax_time.plot(dfRawAccelGyroData[column].values)
                    ax_time.set_title(f'Time - {column}')
                    ax_time.set_xlabel('Sample')
                    ax_time.set_ylabel('Amplitude')

                    # График спектра в частотной области
                    ax_freq.plot(frequencies, np.abs(fft_values))
                    ax_freq.set_title(f'Frequency - {column}')
                    ax_freq.set_xlabel('Frequency')
                    ax_freq.set_ylabel('Magnitude')

                    plt.tight_layout()
                    plt.show()
                            
        
        
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
        
        
