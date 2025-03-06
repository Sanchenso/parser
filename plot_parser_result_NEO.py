import os
import subprocess
import pandas as pd
import georinex as gr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']


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


for arg in os.listdir():
    if arg[-4:] in ('.dat', '.ubx', '.log') or arg[-5:] == '.cyno':
        ubxFile = arg[:-4] + ".dat"
        obsFile = arg[:-4] + ".obs"
        print(ubxFile)
        subprocess.call("convbin " + ubxFile + " -o " + obsFile + " -os -r ubx", shell=True)

for binfile in os.listdir():
    if binfile[-4:] == '.bin' and (binfile[:-4] + ".obs" ) in os.listdir():
        print(binfile)
        obsFile = binfile[:-4] + ".obs"
        prefix = binfile[:-4]
        files_with_prefix = [file for file in files_in_path if file.startswith(prefix)]
        dataframes = []
        dfGGA = pd.DataFrame()
        dfGPSL1 = pd.DataFrame()
        dfBeiDouL1 = pd.DataFrame()
        dfAltitude = pd.DataFrame()
        dfNavVelocity = pd.DataFrame()
        dfPrecision = pd.DataFrame()
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

        # OBS parse
        hdr = gr.rinexheader(obsFile)
        print(hdr.get('fields'))  # вывод типа данных нав. систем

        obsG = gr.load(obsFile, use=['G'])
        spisok_name_satG = list((obsG['S1C'].sv.values))                # формируем список всех спутников GPS
        default_date = pd.Timestamp('1900-01-01')
        times = pd.Series(obsG.time.values)
        time_only = times.dt.time
        times = pd.Series([pd.Timestamp.combine(default_date, t) for t in time_only])
        #min_time = datetime.strptime('23:53:04', '%H:%M:%S')
        #max_time = datetime.strptime('00:02:06', '%H:%M:%S')

        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')

        # SNR GPS L1
        ax1 = fig.add_subplot(3, 2, 1)
        for sv in obsG['sv'].values:
            sat_data = obsG['S1C'].sel(sv=sv)
            df = pd.DataFrame({'time': times, 's1c': sat_data.values})
            df.set_index('time', inplace=True)
            downsampled_df = df.resample('1S').first()
            ax1.scatter(downsampled_df.index, downsampled_df['s1c'], label=str(sv), s=2)
            ax1.plot(downsampled_df.index, downsampled_df['s1c'], linewidth=0.2)
        ax1.set_title('SNR GPS L1, NMEA GSV', fontsize=9)
        ax1.set_ylim(10, 60)
        ax1.set_ylabel('SNR, dBHz')
        ax1.xaxis.set_major_formatter(time_format)
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        print(min_time, max_time)
        if not dfAltitude.empty:
            ax1.set_xlim(min_time, max_time)

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


        
        if not dfGGA.empty:
            ax4 = fig.add_subplot(3, 2, 2)
            ax4.set_xlim(min_time, max_time)
            ax4.set_title('RTK age, NMEA GGA', fontsize=9)
            ax4.plot(dfGGA['GPS_Time'], dfGGA['rtkAGE'], label='RTK age', linewidth=0.2)
            ax4.scatter(dfGGA['GPS_Time'], dfGGA['rtkAGE'], label='RTK age', s=2)
            ax4.set_ylabel('Rtk age, sec')
            ax4.xaxis.set_major_formatter(time_format)
            ax4.grid(color='black', linestyle='--', linewidth=0.2)
            ax4.legend(bbox_to_anchor=(1, 1), loc="upper left")
        

        '''
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
        '''
        # Altitude
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_title('Altitude, NMEA GGA vs Pressure Sensor', fontsize=9)
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

        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_title('Status, NMEA GGA', fontsize=9)
        if not dfAltitude.empty:
            ax3.set_xlim(min_time, max_time)
        if not dfGGA.empty:
            ax3.plot(dfGGA['GPS_Time'], dfGGA['Status'], label=textlable)
            ax3.set_ylabel('Status', fontsize=9)
            ax3.xaxis.set_major_formatter(time_format)
            ax3.grid(color='black', linestyle='--', linewidth=0.2)
            ax3.legend(bbox_to_anchor=(1, 0.5), loc="lower left")


        # Precision
        ax5 = fig.add_subplot(3, 2, 6)
        ax5.set_title('Precision, NavAUTO', fontsize=9)
        if not dfAltitude.empty:
            ax5.set_xlim(min_time, max_time)
        if not dfPrecision.empty:
            ax5.plot(dfPrecision['GPS_Time'], dfPrecision['vAccuracy'], label='vAccuracy')
            ax5.plot(dfPrecision['GPS_Time'], dfPrecision['hAccuracy'], label='hAccuracy')
            ax5.set_ylabel('Precision, m')
            ax5.set_ylim(0, 2)
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
        if not dfNavVelocity.empty:
            ax6.plot(dfNavVelocity['GPS_Time'], dfNavVelocity['Velocity'], label='NAV Velocity')
            ax6.set_ylabel('Velocity, mps')
            ax6.xaxis.set_major_formatter(time_format)
            ax6.grid(color='black', linestyle='--', linewidth=0.2)
            ax6.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
            ax6.set_xlabel('Time')
        plt.savefig('Result_Picture/' + binfile[:-4] + '.jpeg', dpi=200)
        #plt.show()
        plt.close(fig)




