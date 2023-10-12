import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

dfGGA = pd.DataFrame()
dfGPSL1 = pd.DataFrame()
dfAltitude = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']

if not os.path.exists('Result_Picture_Rssi_led'):
    os.makedirs('Result_Picture_Rssi_led')



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
                dfPrecision['hAccuracy'] = dfPrecision['hAccuracy'] / 1000
                dfPrecision['vAccuracy'] = dfPrecision['vAccuracy'] / 1000
            if '_NavSatInfo.csv' in i:
                dfNavSatInfo = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfNavSatInfo['GPS_Time'] = pd.to_datetime(dfNavSatInfo['GPS_Time'])
            if '_Rssi.csv' in i:
                dfRssi = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfRssi['GPS_Time'] = pd.to_datetime(dfRssi['GPS_Time'])
            if '_LedBoardData' in i:
                dfLedBoardData = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfLedBoardData['GPS_Time'] = pd.to_datetime(dfLedBoardData['GPS_Time'])
            if '_IntPowerStatus' in i:
                dfIntPowerStatus = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfIntPowerStatus['GPS_Time'] = pd.to_datetime(dfIntPowerStatus['GPS_Time'])            
        dataframes = [dfGGA, dfGPSL1, dfAltitude]
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:,0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:,0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time, max_time)
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4],  x=0.5, y=0.95, verticalalignment='top')

        # RSSI
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('RSSI', fontsize=9)
        ax1.plot(dfRssi['GPS_Time'], dfRssi['Rssi'], label='Rssi')
        ax1.set_xlim(min_time, max_time)
        ax1.set_ylabel('Rssi, dB')
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.legend(bbox_to_anchor=(-0.1, 1), loc="upper right")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax1.xaxis.set_major_formatter(time_format)

        # RTK_age
        ax4 = fig.add_subplot(3, 2, 2)
        ax4.set_title('RTK age NAV', fontsize=9)
        ax4.set_xlim(min_time, max_time)
        ax4.plot(dfPrecision['GPS_Time'], dfPrecision['rtk_age'], label='RTK age')
        ax4.set_ylabel('RTK age, sec')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(bbox_to_anchor=(1, 0.4), loc="lower left")

        # Driver_Temp
        ax2 = fig.add_subplot(3, 2, 3)
        ax2.set_title('Temperature Led Board', fontsize=9)
        ax2.set_xlim(min_time, max_time)
        ax2.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Driver'], label='Temp_Driver')
        ax2.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Temp_Led'], label='Temp_LED')
        ax2.set_ylabel('Temperature, C')
        ax2.xaxis.set_major_formatter(time_format)
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")

        # Vbat
        ax3 = fig.add_subplot(3, 2, 4)
        ax3.set_title('Power_Battery', fontsize=9)
        ax3.set_xlim(min_time, max_time)
        ax3.plot(dfIntPowerStatus['GPS_Time'], dfIntPowerStatus['Vbat'], label='Vbat')
        ax3.set_ylabel('Vbat, V', fontsize=9)
        ax3.xaxis.set_major_formatter(time_format)
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(1, 0.5), loc="lower left")


        # Led_Current
        ax5 = fig.add_subplot(3, 2, 6)
        ax5.set_title('Led_Current', fontsize=9)
        ax5.set_xlim(min_time, max_time)
        ax5.plot(dfLedBoardData['GPS_Time'], dfLedBoardData['Current'], label='Current')
        ax5.set_ylabel('Current, mA')
        ax5.xaxis.set_major_formatter(time_format)
        ax5.grid(color='black', linestyle='--', linewidth=0.2)
        ax5.legend(bbox_to_anchor=(1, 0.75), loc="lower left")
        ax5.set_xlabel('Time')


        # RTK_age_NMEA
        ax6 = fig.add_subplot(3, 2, 5)
        ax6.set_xlim(min_time, max_time)
        ax6.set_title('RTK age, NMEA GGA', fontsize=9)
        ax6.plot(dfGGA['GPS_Time'], dfGGA['rtkAGE'], label='RTK age')
        ax6.set_ylabel('rtt age, sec')
        ax6.xaxis.set_major_formatter(time_format)
        ax6.grid(color='black', linestyle='--', linewidth=0.2)
        ax6.legend(bbox_to_anchor=(-0.05, 1), loc="upper right")
        ax6.set_xlabel('Time')
        plt.savefig('Result_Picture_Rssi_led/' + binfile[:-4], dpi=500)
        #plt.show()




