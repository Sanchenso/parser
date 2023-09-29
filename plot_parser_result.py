import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

dfGGA = pd.DataFrame()
dfGPSL1 = pd.DataFrame()
dfAltitude = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']



for binfile in os.listdir():
    if binfile[-4:] == '.bin':
        print(binfile)
        prefix = binfile[:-4]
        files_with_prefix = [file for file in files_in_path if file.startswith(prefix)]
        for i in files_with_prefix:
            if '_GGA.csv' in i:
                dfGGA = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfGGA['GPS_Time'] = pd.to_datetime(dfGGA['GPS_Time'])
                first_altitude = dfGGA['Altitude'].iloc[0]
                dfGGA['Altitude'] = dfGGA['Altitude'].apply(lambda x: x - first_altitude)
            if '_GPS_L1_SNR.csv' in i:
                dfGPSL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfGPSL1['Unnamed: 0'] = pd.to_datetime(dfGPSL1['Unnamed: 0'])
                # dfGPSL1['Unnamed: 0'] = mdates.date2num(pd.to_datetime(dfGPSL1['Unnamed: 0']))
            if '_BarAltitude.csv' in i:
                dfAltitude = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfAltitude['GPS_Time'] = pd.to_datetime(dfAltitude['GPS_Time'])
                first_altitude = dfAltitude['BarAltitude'].iloc[0]
                dfAltitude['BarAltitude'] = dfAltitude['BarAltitude'].apply(lambda x: x - first_altitude)
            if '_RMC.csv' in i:
                dfRMC = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfRMC['GPS_Time'] = pd.to_datetime(dfRMC['GPS_Time'])
                dfRMC['mode_indicator'] = dfRMC['mode_indicator'].fillna('')
            if '_NavPrecision.csv' in i:
                dfPrecision = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfPrecision['GPS_Time'] = pd.to_datetime(dfPrecision['GPS_Time'])
        dataframes = [dfGGA, dfGPSL1, dfAltitude]
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:,0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:,0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time, max_time)
        fig = plt.figure(figsize=(18, 20))

        # SNR
        ax1 = fig.add_subplot(3, 2, 1)
        for column in dfGPSL1.columns[1:]:
            ax1.plot(dfGPSL1['Unnamed: 0'], dfGPSL1[column], label=column)
        ax1.set_ylim(10, 60)
        ax1.set_xlim(min_time, max_time)
        ax1.set_ylabel('SNR, dBHz')
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.set_title(binfile)
        ax1.legend(loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax1.xaxis.set_major_formatter(time_format)

        # RMC Status
        textlable1 = ' A=Active \n V=Void'
        textlable2 = ' A=Autonomous \n D=Differential \n R=RTK \n N=No fix \n F=Float RTK'
        ax4 = fig.add_subplot(3, 2, 2)
        ax4.set_xlim(min_time, max_time)
        ax4.plot(dfRMC['GPS_Time'], dfRMC['status'], label=textlable1)
        ax4.plot(dfRMC['GPS_Time'], dfRMC['mode_indicator'], label=textlable2)
        ax4.set_ylabel('Status NMEA GGA')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(loc="upper left")

        # Altitude
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_xlim(min_time, max_time)
        ax2.plot(dfGGA['GPS_Time'], dfGGA['Altitude'], label='Navigation')
        ax2.plot(dfAltitude['GPS_Time'], dfAltitude['BarAltitude'], label='Barometer')
        ax2.set_ylabel('Altitude, m')
        ax2.xaxis.set_major_formatter(time_format)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(loc="upper left")

        # GGA_Status
        textlable = ' 0=Invalid \n 1=fixGNSS \n 2=DGPS \n 3=fixPPS \n 4=FixRTK \n 5=FloatRTK'
        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_xlim(min_time, max_time)
        ax3.plot(dfGGA['GPS_Time'], dfGGA['Status'], label=textlable)
        ax3.set_ylabel('Status GGA')
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.set_xlabel('Time')
        ax3.legend(loc="lower left")


        # Precision
        ax5 = fig.add_subplot(3, 2, 6)
        ax5.set_xlim(min_time, max_time)
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['vAccuracy'], label='vAccuracy')
        ax5.plot(dfPrecision['GPS_Time'], dfPrecision['hAccuracy'], label='hAccuracy')
        ax5.set_ylabel('Precision, mm')
        ax5.set_ylim(0, 10000)
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(loc="upper left")


        # Velocity
        ax6 = fig.add_subplot(3, 2, 5)
        ax6.set_xlim(min_time, max_time)
        ax6.plot(dfRMC['GPS_Time'], dfRMC['Speed'], label='RMC Velocity')
        ax6.set_ylabel('Precision, mps')
        ax6.xaxis.set_major_formatter(time_format)
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.legend(loc="upper left")
        #plt.savefig('New', dpi=500)
        plt.show()




