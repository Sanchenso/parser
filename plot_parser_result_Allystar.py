import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime
import matplotlib.ticker as ticker
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


expansion = (sys.argv[1]) if len(sys.argv) > 1 else '.bin'

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
    if binfile[-4:] == expansion:
        print(binfile)
        prefix = binfile[:-4]
        files_with_prefix = [file for file in files_in_path if file.startswith(prefix)]
        dataframes = []
        dfGGA = pd.DataFrame()
        dfGPSL1 = pd.DataFrame()
        dfBeiDouL1 = pd.DataFrame()
        dfAltitude = pd.DataFrame()
        dfNavVelocity = pd.DataFrame()
        dfPrecision = pd.DataFrame()
        dfPyroBoardState = pd.DataFrame()
        dfLedBoardData = pd.DataFrame()
        dfTXT = pd.DataFrame() 


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
            if '_GPS_L1CA_L1_SNR.csv' in i:
                dfGPSL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfGPSL1['Unnamed: 0'] = pd.to_datetime(dfGPSL1['Unnamed: 0'])
                dfGPSL1['GPS_Time'] = dfGPSL1['GPS_Time'].apply(parse_multiple_formats)
                if not dfGPSL1.empty:
                    dataframes.append(dfGPSL1)
            if 'BeiDou_B1I_L1_SNR.csv' in i:
                dfBeiDouL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfBeiDouL1['Unnamed: 0'] = pd.to_datetime(dfBeiDouL1['Unnamed: 0'])
                dfBeiDouL1['GPS_Time'] = dfBeiDouL1['GPS_Time'].apply(parse_multiple_formats)
                if not dfBeiDouL1.empty:
                    dataframes.append(dfBeiDouL1)
            if '_TXT.csv' in i:
                flagTXT = 1
                dfTXT = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfTXT['GPS_Time'] = pd.to_datetime(dfTXT['GPS_Time'])  
                dfTXT['GPS_Time'] = dfTXT['GPS_Time'].apply(parse_multiple_formats)    
            if '_BarAltitude.csv' in i and os.path.getsize(os.path.join(path, i)) > 100:
                dfAltitude = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfAltitude['GPS_Time'] = pd.to_datetime(dfAltitude['GPS_Time'])
                dfAltitude['GPS_Time'] = dfAltitude['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfAltitude['BarAltitude'].iloc[0]
                dfAltitude['BarAltitude'] = dfAltitude['BarAltitude'].apply(lambda x: x - first_altitude)
                if not dfAltitude.empty:
                    dataframes.append(dfAltitude)
            if '_RMC.csv' in i:
                flagRMC = 1
                dfRMC = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfRMC['GPS_Time'] = pd.to_datetime(dfRMC['GPS_Time'])
                dfRMC['GPS_Time'] = dfRMC['GPS_Time'].apply(parse_multiple_formats)
                dfRMC['mode_indicator'] = dfRMC['mode_indicator'].fillna('')
            if '_LedBoardData' in i:
                dfLedBoardData = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfLedBoardData['GPS_Time'] = pd.to_datetime(dfLedBoardData['GPS_Time'])
                dfLedBoardData['GPS_Time'] = dfLedBoardData['GPS_Time'].apply(parse_multiple_formats)           
            if '_PyroBoardState' in i:
                dfPyroBoardState = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfLedBoardData['GPS_Time'] = pd.to_datetime(dfLedBoardData['GPS_Time'])
                dfPyroBoardState['GPS_Time'] = dfPyroBoardState['GPS_Time'].apply(parse_multiple_formats)
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

            takeoff_time = None     
            if '_UavMode.csv' in i:
                dfUavMode = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfUavMode['GPS_Time'] = pd.to_datetime(dfUavMode['GPS_Time'])
                dfUavMode['GPS_Time'] = dfUavMode['GPS_Time'].apply(parse_multiple_formats)
                takeoff_rows = dfUavMode[dfUavMode['UavMode'] == 24] 
                takeoff_time = takeoff_rows.iloc[0]['GPS_Time']

        if dataframes:
            for df in dataframes:
                if not df.empty:
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
                    min_time = min(df.iloc[:, 0].min() for df in dataframes) - timedelta(seconds=5)
                    max_time = max(df.iloc[:, 0].max() for df in dataframes) + timedelta(seconds=5)
            print(min_time.strftime("%H:%M:%S"), max_time.strftime("%H:%M:%S"))
        else:
            print('no dfAltitude')
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')

        if takeoff_time is not None:
            min_time = takeoff_time - pd.Timedelta(seconds=30)

        

        # SNR
        ax1 = fig.add_subplot(3, 2, 1)
        # ax1.set_title('SNR GPS L1 and BeiDou L1, NMEA GSV', fontsize=9)
        ax1.set_title('SNR GPS L1, NMEA GSV', fontsize=9)

        for column in dfGPSL1.columns[1:]:
            ax1.scatter(dfGPSL1['GPS_Time'], dfGPSL1[column], s=2)
            ax1.plot(dfGPSL1['GPS_Time'], dfGPSL1[column], linewidth=0.2)
        # for column in dfBeiDouL1.columns[1:]:
            # ax1.scatter(dfBeiDouL1['GPS_Time'], dfBeiDouL1[column], s=2)
            # ax1.plot(dfBeiDouL1['GPS_Time'], dfBeiDouL1[column], linewidth=0.2)
        if not dfGPSL1.empty:
            sumSNR_gps = dfGPSL1.iloc[:, 1:].sum().sum()
            countSNR_gps = dfGPSL1.iloc[:, 1:].count().sum()
            avgSNR_gps = round(float(sumSNR_gps) / float(countSNR_gps), 1)

            #sumSNR_beidou = dfBeiDouL1.iloc[:, 1:].sum().sum()
            #countSNR_beidou = dfBeiDouL1.iloc[:, 1:].count().sum()
            #avgSNR_beidou = round(float(sumSNR_beidou) / float(countSNR_beidou), 1)

            ax1.text(0.01, 0.98, f'     GPS L1: {avgSNR_gps} dBHz', fontsize=10, transform=ax1.transAxes, verticalalignment='top')
            #ax1.text(0.01, 0.92, f'BeiDou L1: {avgSNR_beidou} dBHz', fontsize=10, transform=ax1.transAxes, verticalalignment='top')
        ax1.set_ylim(10, 60)
        ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
        if not dfAltitude.empty:
            ax1.set_xlim(min_time, max_time)
        ax1.set_ylabel('SNR, dBHz')
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        #ax1.legend(bbox_to_anchor=(-0.1, 1), loc="upper right")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax1.xaxis.set_major_formatter(time_format)

        # # RMC Status
        # textlable1 = ' A=Active \n V=Void'
        # textlable2 = ' A=Autonomous \n D=Differential \n R=RTK \n N=No fix \n F=Float RTK'
        # ax4 = fig.add_subplot(3, 2, 2)
        # ax4.set_title('Status, NMEA RMC', fontsize=9)
        # ax4.set_xlim(min_time, max_time)
        # ax4.plot(dfRMC['GPS_Time'], dfRMC['status'], label=textlable1)
        # ax4.plot(dfRMC['GPS_Time'], dfRMC['mode_indicator'], label=textlable2)
        # ax4.set_ylabel('Status')
        # ax4.xaxis.set_major_formatter(time_format)
        # ax4.grid(color='black', linestyle='--', linewidth=0.2)
        # ax4.legend(bbox_to_anchor=(1, 0.4), loc="lower left")

        # Driver_Temp
        if not dfLedBoardData.empty:
            ax4 = fig.add_subplot(3, 2, 2)
            ax4.set_title('Temperature Led Board', fontsize=9)
            ax4.set_xlim(min_time, max_time)
            ax4.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Driver'], label='Temp_Driver')
            ax4.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Led'], label='Temp_LED')
            ax4.set_ylabel('Temperature, C')
            ax4.xaxis.set_major_formatter(time_format)
            ax4.grid(color='black', linestyle='--', linewidth=0.2)
            ax4.legend(bbox_to_anchor=(1, 1), loc="lower right")
 


        # # Nav Status
        # textlable1 = ' 0=Autonomous \n 1=Float RTK \n 2=Fix RTK'
        # textlable2 = ' 0=invalid \n 1=initialisation \n 2=search GNSS \n 3=GNSS \n 4=RTK'
        # ax4 = fig.add_subplot(3, 2, 2)
        # ax4.set_title('Status, Nav', fontsize=9)
        # if not dfAltitude.empty:
            # ax4.set_xlim(min_time, max_time)
        # ax4.plot(dfNavSatInfo['GPS_Time'], dfNavSatInfo['NSI_Status'], label=textlable2)
        # ax4.plot(dfNavSatInfo['GPS_Time'], dfNavSatInfo['NavSatInfo'], label=textlable1)
        # ax4.set_ylabel('Status')
        # ax4.xaxis.set_major_formatter(time_format)
        # ax4.grid(color='black', linestyle='--', linewidth=0.2)
        # ax4.legend(bbox_to_anchor=(1, 0.4), loc="lower left")

        # Altitude
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_title('Altitude, NMEA GGA vs Pressure Sensor', fontsize=9)
        if not dfAltitude.empty:
            ax2.set_xlim(min_time, max_time)
            ax2.plot(dfAltitude['GPS_Time'], dfAltitude['BarAltitude'], label='Bar Altitude')
        if not dfGGA.empty:
            ax2.scatter(dfGGA['GPS_Time'], dfGGA['Altitude'], s=2)
            ax2.plot(dfGGA['GPS_Time'], dfGGA['Altitude'], linewidth=0.2, label='GGA Altitude')
            ax2.set_ylabel('Altitude, m')
            ax2.xaxis.set_major_formatter(time_format)
            ax2.grid(color='black', linestyle='--', linewidth=0.2)
            ax2.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")

        # Добавляем вертикальные линии для режимов полёта
        if not dfUavMode.empty:
            y_min, y_max = ax2.get_ylim()
            label_y_start = y_max * 0.95  # Начальная позиция первой метки
            
            for i in range(len(dfUavMode)):
                mode_time = dfUavMode['GPS_Time'][i]
                mode_value = dfUavMode['UavMode'][i]
                mode_label = uav_mode_labels.get(mode_value, str(mode_value))
                
                # Вертикальная линия
                ax2.axvline(x=mode_time, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
                
                # Позиция метки (смещаем каждую следующую метку ниже)
                label_y_pos = label_y_start - (i % 3) * (y_max * 0.05)  # 3 уровня
                
                # Горизонтальная метка
                ax2.text(mode_time, label_y_pos, mode_label,
                        fontsize=6, rotation=0,
                        va='top', ha='right',
                        color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))

        # GGA Status
        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_title('Status, NMEA GGA', fontsize=9)
        textlable = ' 0=Invalid \n 1=fixGNSS \n 2=DGPS \n 3=fixPPS \n 4=FixRTK \n 5=FloatRTK'
        if not dfAltitude.empty:
            ax3.set_xlim(min_time, max_time)
        if not dfGGA.empty:
            ax3.scatter(dfGGA['GPS_Time'], dfGGA['Status'], s=2)
            ax3.plot(dfGGA['GPS_Time'], dfGGA['Status'], label=textlable, linewidth=0.2)
            ax3.set_ylabel('Status', fontsize=9)
            ax3.xaxis.set_major_formatter(time_format)
            ax3.grid(color='black', linestyle='--', linewidth=0.2)
            ax3.legend(bbox_to_anchor=(1, 0.5), loc="lower left")

        
        # TXT
        ax5 = fig.add_subplot(3, 2, 5)
        ax5.set_title('NMEA TXT', fontsize=9)
        ax5.set_xlim(min_time, max_time)
        if flagTXT == 1:
            dfTXT.columns = ['GPS_Time'] + list(dfTXT.iloc[:, 1:].columns)
            ax5.plot(dfTXT['GPS_Time'], dfTXT['1'], label='$TXT,x')
            ax5.plot(dfTXT['GPS_Time'], dfTXT['2'], label='$TXT,,x')
            ax5.plot(dfTXT['GPS_Time'], dfTXT['3'], label='$TXT,,,x')
            ax5.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        ax5.set_ylabel('Message')
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)

        problem_file_path = os.path.join('problemAlly', f"{binfile[:-4]}_problems.txt")
        if os.path.exists(problem_file_path):
            with open(problem_file_path, 'r') as file:
                lines = file.readlines()
            
            event_times = {
                'ALLYSTAR': [],
                'HD9311': []
            }
            
            for line in lines:
                if line.startswith('[ALLYSTAR]') or line.startswith('[HD9311]'):
                    event_type = line[1:line.find(']')]  # Извлекаем ALLYSTAR или HD9311
                    time_str = line.split()[1].strip()
                    
                    try:
                        event_time = datetime.strptime(time_str, "%H:%M:%S.%f").time()
                        event_datetime = datetime.combine(min_time.date(), event_time)
                        event_times[event_type].append(event_datetime)
                    except ValueError:
                        continue
            
            # Markers
            y_min, y_max = ax5.get_ylim()
            label_y_pos = {
                'ALLYSTAR': y_max * 0.95,  # Метки ALLYSTAR вверху
                'HD9311': y_max * 0.90      # Метки HD9311 чуть ниже
            }
            colors = {
                'ALLYSTAR': 'purple',
                'HD9311': 'blue'
            }
            
            for event_type, times in event_times.items():
                if not times:
                    continue
                    
                for time in times:
                    ax5.axvline(x=time, color=colors[event_type], linestyle=':', linewidth=0.8, alpha=0.7)
                    ax5.text(time, label_y_pos[event_type], f' {event_type}',
                            fontsize=6, rotation=0,
                            va='top', ha='right',
                            color=colors[event_type],
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.1'))



        # PyroBoardState
        ax6 = fig.add_subplot(3, 2, 6)
        if not dfPyroBoardState.empty:
            ax6.set_xlim(min_time, max_time)
        ax6.set_title('PyroBoardState', fontsize=9)
        if not dfPyroBoardState.empty:
            ax6.plot(dfPyroBoardState['GPS_Time'], dfPyroBoardState['channel_1'], label='channel_1')
            ax6.plot(dfPyroBoardState['GPS_Time'], dfPyroBoardState['channel_2'], label='channel_2')
            ax6.plot(dfPyroBoardState['GPS_Time'], dfPyroBoardState['channel_3'], label='channel_3')
            ax6.plot(dfPyroBoardState['GPS_Time'], dfPyroBoardState['channel_4'], label='channel_4')
            ax6.legend(bbox_to_anchor=(1, 1), loc="upper left")
        ax6.set_ylabel('State')
        ax6.xaxis.set_major_formatter(time_format)
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.set_xlabel('Time')


        plt.savefig('Result_Picture/' + binfile[:-4] + '.jpeg', dpi=200)
        #plt.show()
        plt.close(fig)




