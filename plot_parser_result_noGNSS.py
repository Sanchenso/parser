import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime

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


if not os.path.exists('Result_Picture'):
    os.makedirs('Result_Picture')


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
        dataframes = []
        dfGGA = pd.DataFrame()
        dfGPSL1 = pd.DataFrame()
        dfBeiDouL1 = pd.DataFrame()
        dfAltitude = pd.DataFrame()
        dfNavVelocity = pd.DataFrame()
        flagRMC = 0
        for i in files_with_prefix:
            if '_GGA.csv' in i:
                dfGGA = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfGGA['GPS_Time'] = pd.to_datetime(dfGGA['GPS_Time'])
                dfGGA['GPS_Time'] = dfGGA['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfGGA['Altitude'].iloc[0]
                dfGGA['Altitude'] = dfGGA['Altitude'].apply(lambda x: x - first_altitude)
                if not dfGGA.empty:
                    dataframes.append(dfGGA)
            if '_BarAltitude.csv' in i and os.path.getsize(os.path.join(path, i)) > 100:
                dfAltitude = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfAltitude['GPS_Time'] = pd.to_datetime(dfAltitude['GPS_Time'])
                dfAltitude['GPS_Time'] = dfAltitude['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfAltitude['BarAltitude'].iloc[0]
                dfAltitude['BarAltitude'] = dfAltitude['BarAltitude'].apply(lambda x: x - first_altitude)
                if not dfAltitude.empty:
                    dataframes.append(dfAltitude)
            if '_NavPrecision.csv' in i:
                dfPrecision = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfPrecision['GPS_Time'] = pd.to_datetime(dfPrecision['GPS_Time'])
                dfPrecision['GPS_Time'] = dfPrecision['GPS_Time'].apply(parse_multiple_formats)
                dfPrecision['hAccuracy'] = dfPrecision['hAccuracy'] / 1000
                dfPrecision['vAccuracy'] = dfPrecision['vAccuracy'] / 1000
            if '_NavSatInfo.csv' in i:
                dfNavSatInfo = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfNavSatInfo['GPS_Time'] = pd.to_datetime(dfNavSatInfo['GPS_Time'])
                dfNavSatInfo['GPS_Time'] = dfNavSatInfo['GPS_Time'].apply(parse_multiple_formats)
            if '_NavVelocity.csv' in i:
                dfNavVelocity = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfNavVelocity['GPS_Time'] = pd.to_datetime(dfNavVelocity['GPS_Time'])
                dfNavVelocity['GPS_Time'] = dfNavVelocity['GPS_Time'].apply(parse_multiple_formats)
            if '_UavMode.csv' in i:
                dfUavMode = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfUavMode['GPS_Time'] = pd.to_datetime(dfUavMode['GPS_Time'])
                dfUavMode['GPS_Time'] = dfUavMode['GPS_Time'].apply(parse_multiple_formats) 
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
        time_format = mdates.DateFormatter('%H:%M:%S')
        if dataframes:
            for df in dataframes:
                if not df.empty:
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
                    min_time = min(df.iloc[:, 0].min() for df in dataframes) - timedelta(seconds=5)
                    max_time = max(df.iloc[:, 0].max() for df in dataframes) + timedelta(seconds=5)
            print(min_time.strftime("%H:%M:%S"), max_time.strftime("%H:%M:%S"))
        else:
            print('no dfAltitude')

        min_time = datetime.strptime('15:10:30', '%H:%M:%S')
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')

        # UAV mode
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('UAV mode', fontsize=9)
        ax1.set_xlim(min_time, max_time)
        ax1.scatter(dfUavMode['GPS_Time'], dfUavMode['UavMode'], label='UavMode', s=2)
        ax1.plot(dfUavMode['GPS_Time'], dfUavMode['UavMode'], linewidth=0.2)
        ax1.set_ylabel('Mode', fontsize=9)
        ax1.xaxis.set_major_formatter(time_format)
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        for i in range(len(dfUavMode)):
            mode_value = dfUavMode['UavMode'][i]
            mode_label = uav_mode_labels.get(mode_value, str(mode_value))  # Получаем текстовую метку или значение по умолчанию
            ax1.text(dfUavMode['GPS_Time'][i], dfUavMode['UavMode'][i], mode_label, fontsize=6)
        if not dfAltitude.empty:
            ax1.set_xlim(min_time, max_time)


        # Nav Status
        textlable1 = ' 0=Autonomous \n 1=Float RTK \n 2=Fix RTK'
        textlable2 = ' 0=invalid \n 1=initialisation \n 2=search GNSS \n 3=GNSS \n 4=RTK'
        ax4 = fig.add_subplot(3, 2, 2)
        ax4.set_title('Status, Nav', fontsize=9)
        if not dfAltitude.empty:
            ax4.set_xlim(min_time, max_time)
        ax4.plot(dfNavSatInfo['GPS_Time'], dfNavSatInfo['NSI_Status'], label=textlable2)
        ax4.plot(dfNavSatInfo['GPS_Time'], dfNavSatInfo['NavSatInfo'], label=textlable1)
        ax4.set_ylabel('Status')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(bbox_to_anchor=(1, 0.4), loc="lower left")

        # Altitude
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_title('Altitude, NMEA GGA vs Pressure Sensor', fontsize=9)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        if not dfAltitude.empty:
            ax2.set_xlim(min_time, max_time)
            ax2.plot(dfAltitude['GPS_Time'], dfAltitude['BarAltitude'], label='Bar Altitude')
        if not dfGGA.empty:
            ax2.plot(dfGGA['GPS_Time'], dfGGA['Altitude'], label='GGA Altitude')
            ax2.set_ylabel('Altitude, m')
            ax2.xaxis.set_major_formatter(time_format)
            ax2.grid(color='black', linestyle='--', linewidth=0.2)
            ax2.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
            # GGA_Status
            textlable = ' 0=Invalid \n 1=fixGNSS \n 2=DGPS \n 3=fixPPS \n 4=FixRTK \n 5=FloatRTK'

        # Vbat
        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_title('Power_Battery', fontsize=9)
        ax3.set_xlim(min_time, max_time)
        if flagIntPowerStatus == 1:
            ax3.plot(dfIntPowerStatus['GPS_Time'], dfIntPowerStatus['Vbat'], label='Vbat')
        elif flagExtPowerStatus == 1:
            ax3.plot(dfExtPowerStatus['GPS_Time'], dfExtPowerStatus['Vbat'], label='Vbat')
        ax3.set_ylabel('Vbat, V', fontsize=9)
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(1, 0.5),  loc="lower left")


        # Precision
        ax5 = fig.add_subplot(3, 2, 6)
        ax5.set_title('Precision, NavAUTO', fontsize=9)
        if not dfAltitude.empty:
            ax5.set_xlim(min_time, max_time)
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['vAccuracy'], label='vAccuracy')
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['hAccuracy'], label='hAccuracy')
        ax5.set_ylabel('Precision, m')
        ax5.set_ylim(0, 8)
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(bbox_to_anchor=(1, 0.75), loc="lower left")
        ax5.set_xlabel('Time')


        # Velocity
        ax6 = fig.add_subplot(3, 2, 5)
        if not dfAltitude.empty:
            ax6.set_xlim(min_time, max_time)
        ax6.set_title('Velocity, NMEA RMC', fontsize=9)
        if flagRMC == 1:
            ax6.plot(dfRMC['GPS_Time'], dfRMC['Speed'], label='RMC Velocity')
        ax6.plot(dfNavVelocity['GPS_Time'], dfNavVelocity['Velocity'], label='NAV Velocity')
        ax6.set_ylabel('Velocity, mps')
        ax6.xaxis.set_major_formatter(time_format)
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        ax6.set_xlabel('Time')
        plt.savefig('Result_Picture/' + binfile[:-4] + '.jpeg', dpi=200)
        plt.show()
        plt.close(fig)




