import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime

dfGGA = pd.DataFrame()
dfRssi = pd.DataFrame()
dfTXT = pd.DataFrame()
dfUavMode = pd.DataFrame()
dfEventLog = pd.DataFrame()

flagTXT = 0

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']

uav_mode_labels = {
    0: 'ROOT',
    1: 'DISARMED', 
    2: 'IDLE',              # Неактивное состояние
    3: 'TEST_ACTUATION',    # Состояние для проверки работоспособности рулевых поверхностей   
    4: 'TEST_PARACHUTE',    # Состояние для проверки парашюта
    5: 'TEST_ENGINE',       # Состояние для проверки двигателя
    6: 'PARACHUTE',         # Состояние, в котором выбрасывается парашют и ожидается его раскрытие
    7: 'WAIT_FOR_LANDING',  # Состояние снижения на парашюте
    8: 'LANDED',            # Состояние, индицирующее успешную посадку
    9: 'CATAPULT',          # Состояние готовности к запуску для самолета
    10: 'PREFLIGHT',        # Проверка готовности двигателей
    11: 'ARMED',            #                
    12: 'TAKEOFF',          # Набор минимальной необходимой высоты
    13: 'WAIT_FOR_GNSS',    # Состояние ожидания появления сигнала со спутникового приемника
    14: 'WIND_MEASURE',     # Измерение скорости ветра
    15: 'MISSION',          # Режим автоматического полета по ранее загруженной миссии
    16: 'MISSION_ASCEND',   # Набор в соответствии с заданием
    17: 'MISSION_DESCEND',  # Снижение в соответствии с заданием
    18: 'MISSION_RTL',      # Возврат домой
    19: 'UNCONDITIONAL_RTL',# Безусловный возврат домой. Ручное управление и возврат на маршрут недоступны
    20: 'MANUAL_HEADING',   # Ручное управление курсом, высотой и скоростью
    21: 'MANUAL_ROLL',      # Ручное управление ориентацией, высотой и скоростью
    22: 'MANUAL_SPEED',     # Ручное управление скоростями, направлением и высотой
    23: 'LANDING',          # Подготовка к посадке
    24: 'ON_DEMAND'         # Режим полета по требованию
}

if not os.path.exists('Result_Picture_Rssi'):
    os.makedirs('Result_Picture_Rssi')

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
            if '_Rssi.csv' in i:
                dfRssi = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfRssi['GPS_Time'] = pd.to_datetime(dfRssi['GPS_Time']) 
                dfRssi['GPS_Time'] = dfRssi['GPS_Time'].apply(parse_multiple_formats)
            if '_TXT.csv' in i:
                flagTXT = 1
                dfTXT = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfTXT['GPS_Time'] = pd.to_datetime(dfTXT['GPS_Time'])  
                dfTXT['GPS_Time'] = dfTXT['GPS_Time'].apply(parse_multiple_formats)                
            if '_UavMode.csv' in i:
                dfUavMode = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfUavMode['GPS_Time'] = pd.to_datetime(dfUavMode['GPS_Time'])
                dfUavMode['GPS_Time'] = dfUavMode['GPS_Time'].apply(parse_multiple_formats) 
            if '_EventLog.csv' in i:
                dfEventLog = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfEventLog['GPS_Time'] = pd.to_datetime(dfEventLog['GPS_Time'])
                dfEventLog['GPS_Time'] = dfEventLog['GPS_Time'].apply(parse_multiple_formats)

        dataframes = [dfGGA, dfRssi]
        time_format = mdates.DateFormatter('%H:%M:%S')
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:,0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:,0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time.strftime("%H:%M:%S"), max_time.strftime("%H:%M:%S"))
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')
        
        # event log
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('Event log', fontsize=9)
        ax1.set_xlim(min_time, max_time)
        ax1.scatter(dfEventLog['GPS_Time'], dfEventLog['EventLog'], label='EventLog', s=2)
        ax1.plot(dfEventLog['GPS_Time'], dfEventLog['EventLog'], linewidth=0.2)
        ax1.set_ylabel('Status')
        ax1.xaxis.set_major_formatter(time_format)
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")

        # GGA_Status
        textlable = ' 0=Invalid \n 1=fixGNSS \n 2=DGPS \n 3=fixPPS \n 4=FixRTK \n 5=FloatRTK'
        ax2 = fig.add_subplot(3, 2, 2)
        ax2.set_title('Status, NMEA GGA', fontsize=9)
        ax2.set_xlim(min_time, max_time)
        ax2.plot(dfGGA['GPS_Time'], dfGGA['Status'], label=textlable)
        ax2.set_ylabel('Status', fontsize=9)
        ax2.xaxis.set_major_formatter(time_format)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(1, 0.5), loc="lower left")

        # RSSI
        ax6 = fig.add_subplot(3, 2, 6)
        ax6.set_title('RSSI', fontsize=9)
        ax6.plot(dfRssi['GPS_Time'], dfRssi['Rssi'], label='Rssi', linewidth=0.2)
        ax6.scatter(dfRssi['GPS_Time'], dfRssi['Rssi'], s=2)
        ax6.set_xlim(min_time, max_time)
        ax6.set_ylabel('Rssi, dB')
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.legend(bbox_to_anchor=(1, 1), loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax6.xaxis.set_major_formatter(time_format)

        # UAV mode
        ax3 = fig.add_subplot(3, 2, 3)
        ax3.set_title('UAV mode', fontsize=9)
        ax3.set_xlim(min_time, max_time)
        ax3.scatter(dfUavMode['GPS_Time'], dfUavMode['UavMode'], label='UavMode', s=2)
        ax3.plot(dfUavMode['GPS_Time'], dfUavMode['UavMode'], linewidth=0.2)
        ax3.set_ylabel('Mode', fontsize=9)
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        for i in range(len(dfUavMode)):
            mode_value = dfUavMode['UavMode'][i]
            mode_label = uav_mode_labels.get(mode_value, str(mode_value))  # Получаем текстовую метку или значение по умолчанию
            ax3.text(dfUavMode['GPS_Time'][i], dfUavMode['UavMode'][i], mode_label, fontsize=6)


        # TXT
        ax5 = fig.add_subplot(3, 2, 5)
        ax5.set_title('NMEA TXT', fontsize=9)
        ax5.set_xlim(min_time, max_time)
        if flagTXT == 1:
            dfTXT.columns = ['GPS_Time'] + list(dfTXT.iloc[:, 1:].columns)
            ax5.plot(dfTXT['GPS_Time'], dfTXT['0'], label='0')
            ax5.plot(dfTXT['GPS_Time'], dfTXT['1'], label='1')
            ax5.plot(dfTXT['GPS_Time'], dfTXT['2'], label='2')
            #ax5.plot(dfTXT['GPS_Time'], dfTXT['3'], label='3')
            ax5.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        ax5.set_ylabel('Message')
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        

        # RTK_age_NMEA
        ax4 = fig.add_subplot(3, 2, 4)
        ax4.set_xlim(min_time, max_time)
        ax4.set_title('RTK age, NMEA GGA', fontsize=9)
        ax4.plot(dfGGA['GPS_Time'], dfGGA['rtkAGE'], label='RTK age', linewidth=0.2)
        ax4.scatter(dfGGA['GPS_Time'], dfGGA['rtkAGE'], label='RTK age', s=2)
        ax4.set_ylabel('Rtk age, sec')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(bbox_to_anchor=(1, 1), loc="upper left")
        plt.savefig('Result_Picture_Rssi/' + binfile[:-4], dpi=500)
        #plt.show()




