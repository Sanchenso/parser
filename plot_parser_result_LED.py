import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime

dfGGA = pd.DataFrame()
dfGPSL1 = pd.DataFrame()
dfAltitude = pd.DataFrame()

flagIntPowerStatus = 0
flagExtPowerStatus = 0

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']

if not os.path.exists('Result_Picture_led'):
    os.makedirs('Result_Picture_led')

# Определение функции для парсинга нескольких форматов даты и времени
def parse_multiple_formats(date_str):
    formats = ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%H:%M:%S.%f", "%H:%M:%S"] 
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    print(f"Не удалось преобразовать: {date_str}")  # Вывод строки, которая не подошла ни под один формат
    return pd.NaT  # Если ни один формат не подошел, возвращаем NaT


for binfile in os.listdir():
    if binfile[-4:] == '.bin':
        print(binfile)
        prefix = binfile[:-4]
        files_with_prefix = [file for file in files_in_path if file.startswith(prefix)]
        for i in files_with_prefix:
            if '_GGA.csv' in i:
                dfGGA = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfGGA['GPS_Time'] = pd.to_datetime(dfGGA['GPS_Time'])
                dfGGA['GPS_Time'] = dfGGA['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfGGA['Altitude'].iloc[0]
                dfGGA['Altitude'] = dfGGA['Altitude'].apply(lambda x: x - first_altitude)
            if '_LedBoardData' in i:
                dfLedBoardData = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfLedBoardData['GPS_Time'] = pd.to_datetime(dfLedBoardData['GPS_Time'])
                dfLedBoardData['GPS_Time'] = dfLedBoardData['GPS_Time'].apply(parse_multiple_formats)
            if '_IntPowerStatus' in i:
                flagIntPowerStatus = 1 
                dfIntPowerStatus = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfIntPowerStatus['GPS_Time'] = pd.to_datetime(dfIntPowerStatus['GPS_Time'])
                dfIntPowerStatus['GPS_Time'] = dfIntPowerStatus['GPS_Time'].apply(parse_multiple_formats)                
            if '_ExtPowerStatus' in i:
                flagExtPowerStatus = 1
                dfExtPowerStatus = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfExtPowerStatus['GPS_Time'] = pd.to_datetime(dfExtPowerStatus['GPS_Time']) 
                dfExtPowerStatus['GPS_Time'] = dfExtPowerStatus['GPS_Time'].apply(parse_multiple_formats)
        dataframes = [dfGGA]
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:,0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:,0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time, max_time)
        fig = plt.figure(figsize=(10, 14))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')
        time_format = mdates.DateFormatter('%H:%M:%S')
        
        # Driver_Temp
        ax2 = fig.add_subplot(3, 1, 1)
        ax2.set_title('Temperature Led Board', fontsize=9)
        ax2.set_xlim(min_time, max_time)
        ax2.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Driver'], label='Temp_Driver')
        ax2.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Led'], label='Temp_LED')
        ax2.set_ylabel('Temperature, C')
        ax2.xaxis.set_major_formatter(time_format)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(1, 1), loc="lower right")

        # Vbat
        ax3 = fig.add_subplot(3, 1, 2)
        ax3.set_title('Power_Battery', fontsize=9)
        ax3.set_xlim(min_time, max_time)
        if flagIntPowerStatus == 1:
            ax3.plot(dfIntPowerStatus['GPS_Time'], dfIntPowerStatus['Vbat'], label='Vbat')
        elif flagExtPowerStatus == 1:
            ax3.plot(dfExtPowerStatus['GPS_Time'], dfExtPowerStatus['Vbat'], label='Vbat')
        ax3.set_ylabel('Vbat, V', fontsize=9)
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(1, 1), loc="lower right")


        # Led_Current
        ax5 = fig.add_subplot(3, 1, 3)
        ax5.set_title('Led_Current', fontsize=9)
        ax5.set_xlim(min_time, max_time)
        ax5.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Current'], label='Current')
        ax5.set_ylabel('Current, mA')
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(bbox_to_anchor=(1, 1), loc="lower right")
        ax5.set_xlabel('Time')

        plt.savefig('Result_Picture_led/' + binfile[:-4], dpi=500)
        #plt.show()




