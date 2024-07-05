import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime

dfGGA = pd.DataFrame()
dfGPSL1 = pd.DataFrame()
dfBeiDouL1 = pd.DataFrame()
dfAltitude = pd.DataFrame()
dfNavVelocity = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']
flagRMC = 0

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
        for i in files_with_prefix:
            if '_GGA.csv' in i:
                dfGGA = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfGGA['GPS_Time'] = pd.to_datetime(dfGGA['GPS_Time'])
                dfGGA['GPS_Time'] = dfGGA['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfGGA['Altitude'].iloc[0]
                dfGGA['Altitude'] = dfGGA['Altitude'].apply(lambda x: x - first_altitude)
            if '_GPS_L1_SNR.csv' in i:
                dfGPSL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfGPSL1['Unnamed: 0'] = pd.to_datetime(dfGPSL1['Unnamed: 0'])
                dfGPSL1['Unnamed: 0'] = dfGPSL1['Unnamed: 0'].apply(parse_multiple_formats)
            if '_BeiDou_L1_SNR.csv' in i:
                dfBeiDouL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfBeiDouL1['Unnamed: 0'] = pd.to_datetime(dfBeiDouL1['Unnamed: 0'])
                dfBeiDouL1['Unnamed: 0'] = dfBeiDouL1['Unnamed: 0'].apply(parse_multiple_formats)
            if '_BarAltitude.csv' in i:
                dfAltitude = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfAltitude['GPS_Time'] = pd.to_datetime(dfAltitude['GPS_Time'])
                dfAltitude['GPS_Time'] = dfAltitude['GPS_Time'].apply(parse_multiple_formats)
                first_altitude = dfAltitude['BarAltitude'].iloc[0]
                dfAltitude['BarAltitude'] = dfAltitude['BarAltitude'].apply(lambda x: x - first_altitude)
            if '_RMC.csv' in i:
                flagRMC = 1
                dfRMC = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                #dfRMC['GPS_Time'] = pd.to_datetime(dfRMC['GPS_Time'])
                dfRMC['GPS_Time'] = dfRMC['GPS_Time'].apply(parse_multiple_formats)
                dfRMC['mode_indicator'] = dfRMC['mode_indicator'].fillna('')
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
                
            
        dataframes = [dfGGA, dfGPSL1, dfBeiDouL1, dfAltitude]
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:, 0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:, 0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time.strftime("%H:%M:%S"), max_time.strftime("%H:%M:%S"))
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')

        # SNR
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('SNR GPS L1 and BeiDou L1, NMEA GSV', fontsize=9)

        for column in dfGPSL1.columns[1:]:
            ax1.scatter(dfGPSL1['Unnamed: 0'], dfGPSL1[column], s=2)
            ax1.plot(dfGPSL1['Unnamed: 0'], dfGPSL1[column], linewidth=0.2)
        for column in dfBeiDouL1.columns[1:]:
            ax1.scatter(dfBeiDouL1['Unnamed: 0'], dfBeiDouL1[column], s=2)
            ax1.plot(dfBeiDouL1['Unnamed: 0'], dfBeiDouL1[column], linewidth=0.2)
            
        sumSNR_gps = dfGPSL1.iloc[:, 1:].sum().sum()
        countSNR_gps = dfGPSL1.iloc[:, 1:].count().sum()
        avgSNR_gps = round(float(sumSNR_gps) / float(countSNR_gps), 1)
        
        sumSNR_beidou = dfBeiDouL1.iloc[:, 1:].sum().sum()
        countSNR_beidou = dfBeiDouL1.iloc[:, 1:].count().sum() 
        avgSNR_beidou = round(float(sumSNR_beidou) / float(countSNR_beidou), 1)

        ax1.text(0.01, 0.98, f'     GPS L1: {avgSNR_gps} dBHz', fontsize=10, transform=ax1.transAxes, verticalalignment='top')
        ax1.text(0.01, 0.92, f'BeiDou L1: {avgSNR_beidou} dBHz', fontsize=10, transform=ax1.transAxes, verticalalignment='top')
        ax1.set_ylim(10, 60)
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

        # Nav Status
        textlable1 = ' 0=Autonomous \n 1=Float RTK \n 2=Fix RTK'
        textlable2 = ' 0=invalid \n 1=initialisation \n 2=search GNSS \n 3=GNSS \n 4=RTK'
        ax4 = fig.add_subplot(3, 2, 2)
        ax4.set_title('Status, Nav', fontsize=9)
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
        ax2.set_xlim(min_time, max_time)
        ax2.plot(dfGGA['GPS_Time'], dfGGA['Altitude'], label='GGA Altitude')
        ax2.plot(dfAltitude['GPS_Time'], dfAltitude['BarAltitude'], label='Bar Altitude')
        ax2.set_ylabel('Altitude, m')
        ax2.xaxis.set_major_formatter(time_format)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")

        # GGA_Status
        textlable = ' 0=Invalid \n 1=fixGNSS \n 2=DGPS \n 3=fixPPS \n 4=FixRTK \n 5=FloatRTK'
        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_title('Status, NMEA GGA', fontsize=9)
        ax3.set_xlim(min_time, max_time)
        ax3.plot(dfGGA['GPS_Time'], dfGGA['Status'], label=textlable)
        ax3.set_ylabel('Status', fontsize=9)
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(1, 0.5), loc="lower left")


        # Precision
        ax5 = fig.add_subplot(3, 2, 6)
        ax5.set_title('Precision, NavAUTO', fontsize=9)
        ax5.set_xlim(min_time, max_time)
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['vAccuracy'], label='vAccuracy')
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['hAccuracy'], label='hAccuracy')
        ax5.set_ylabel('Precision, m')
        #ax5.set_ylim(0, 8)
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(bbox_to_anchor=(1, 0.75), loc="lower left")
        ax5.set_xlabel('Time')


        # Velocity
        ax6 = fig.add_subplot(3, 2, 5)
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
        plt.savefig('Result_Picture/' + binfile[:-4], dpi=500)
        #plt.show()




