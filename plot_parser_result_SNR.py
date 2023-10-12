import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

dfGGA = pd.DataFrame()
dfGPSL1 = pd.DataFrame()
dfGPSL2 = pd.DataFrame()
dfBeiDouL1 = pd.DataFrame()
dfBeiDouL2 = pd.DataFrame()
dfAltitude = pd.DataFrame()

path = "Result_CSV"
files_in_path = os.listdir(path)
suffix = ['_GGA.csv', '_channel_gnss_126_GPS_L1_SNR.csv', '_BarAltitude.csv']


if not os.path.exists('Result_SNR_4'):
    os.makedirs('Result_SNR_4')

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
            if '_GPS_L2_SNR.csv' in i:
                dfGPSL2 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfGPSL2['Unnamed: 0'] = pd.to_datetime(dfGPSL2['Unnamed: 0'])
            if '_BeiDou_L1_SNR.csv' in i:
                dfBeiDouL1 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfBeiDouL1['Unnamed: 0'] = pd.to_datetime(dfBeiDouL1['Unnamed: 0'])
            if '_BeiDou_L2_SNR.csv' in i:
                dfBeiDouL2 = pd.read_csv(os.path.join(path, i), header=0, sep=',', skiprows=0)
                dfBeiDouL2['Unnamed: 0'] = pd.to_datetime(dfBeiDouL2['Unnamed: 0'])
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
        dataframes = [dfGGA, dfGPSL1, dfAltitude, dfGPSL2, dfBeiDouL1, dfBeiDouL2]
        for df in dataframes:
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        min_time = min(df.iloc[:, 0].min() for df in dataframes) - timedelta(seconds=5)
        max_time = max(df.iloc[:, 0].max() for df in dataframes) + timedelta(seconds=5)
        print(min_time, max_time)
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4], x=0.5, y=0.95, verticalalignment='top')

        # SNR
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.set_title('SNR GPS L1, NMEA GSV', fontsize=9)
        for column in dfGPSL1.columns[1:]:
            ax1.plot(dfGPSL1['Unnamed: 0'], dfGPSL1[column], label=column)
        sumSNR = dfGPSL1.iloc[:, 1:].sum().sum()
        countSNR = dfGPSL1.iloc[:, 1:].count().sum()
        print(round(sumSNR/countSNR, 1))
        ax1.text(0.1, 0.9, 'average SNR:', fontsize=12, transform=ax1.transAxes)
        ax1.text(0.27, 0.9, '        dBHz', fontsize=12, transform=ax1.transAxes)
        ax1.text(0.266, 0.9, str(round(sumSNR/countSNR, 1)), fontsize=12, transform=ax1.transAxes)
        ax1.set_ylim(10, 60)
        ax1.set_xlim(min_time, max_time)
        ax1.set_ylabel('SNR, dBHz')
        ax1.grid(color='black', linestyle='--', linewidth=0.2)

        ax1.legend(bbox_to_anchor=(1, 1), loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax1.xaxis.set_major_formatter(time_format)

        ax2 = fig.add_subplot(2, 2, 2)
        ax2.set_title('SNR GPS L2, NMEA GSV', fontsize=9)
        average_snr = 0
        column_snr = 0
        for column in dfGPSL2.columns[1:]:
            ax2.plot(dfGPSL2['Unnamed: 0'], dfGPSL2[column], label=column)
        sumSNR = dfGPSL2.iloc[:, 1:].sum().sum()
        countSNR = dfGPSL2.iloc[:, 1:].count().sum()
        print(round(sumSNR/countSNR, 1))
        ax2.text(0.1, 0.9, 'average SNR:', fontsize=12, transform=ax2.transAxes)
        ax2.text(0.27, 0.9, '        dBHz', fontsize=12, transform=ax2.transAxes)
        ax2.text(0.266, 0.9, str(round(sumSNR/countSNR, 1)), fontsize=12, transform=ax2.transAxes)
        ax2.set_ylim(10, 60)
        ax2.set_xlim(min_time, max_time)
        ax2.set_ylabel('SNR, dBHz')
        ax2.grid(color='black', linestyle='--', linewidth=0.2)
        ax2.legend(bbox_to_anchor=(1, 1), loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax2.xaxis.set_major_formatter(time_format)

        ax3 = fig.add_subplot(2, 2, 3)
        ax3.set_title('SNR BeiDou L1, NMEA GSV', fontsize=9)
        average_snr = 0
        column_snr = 0
        for column in dfBeiDouL1.columns[1:]:
            ax3.plot(dfBeiDouL1['Unnamed: 0'], dfBeiDouL1[column], label=column)
        sumSNR = dfBeiDouL1.iloc[:, 1:].sum().sum()
        countSNR = dfBeiDouL1.iloc[:, 1:].count().sum()
        print(round(sumSNR/countSNR, 1))
        ax3.text(0.1, 0.9, 'average SNR:', fontsize=12, transform=ax3.transAxes)
        ax3.text(0.27, 0.9, '        dBHz', fontsize=12, transform=ax3.transAxes)
        ax3.text(0.266, 0.9, str(round(sumSNR/countSNR, 1)), fontsize=12, transform=ax3.transAxes)
        ax3.set_ylim(10, 60)
        ax3.set_xlim(min_time, max_time)
        ax3.set_ylabel('SNR, dBHz')
        ax3.grid(color='black', linestyle='--', linewidth=0.2)
        ax3.legend(bbox_to_anchor=(1, 1), loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax3.xaxis.set_major_formatter(time_format)

        ax4 = fig.add_subplot(2, 2, 4)
        ax4.set_title('SNR BeiDou L2, NMEA GSV', fontsize=9)
        average_snr = 0
        column_snr = 0
        for column in dfBeiDouL2.columns[1:]:
            ax4.plot(dfBeiDouL2['Unnamed: 0'], dfBeiDouL2[column], label=column)
        sumSNR = dfBeiDouL2.iloc[:, 1:].sum().sum()
        countSNR = dfBeiDouL2.iloc[:, 1:].count().sum()
        print(round(sumSNR/countSNR, 1))
        ax4.text(0.1, 0.9, 'average SNR:', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.27, 0.9, '        dBHz', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.266, 0.9, str(round(sumSNR/countSNR, 1)), fontsize=12, transform=ax4.transAxes)
        ax4.set_ylim(10, 60)
        ax4.set_xlim(min_time, max_time)
        ax4.set_ylabel('SNR, dBHz')
        ax4.grid(color='black', linestyle='--', linewidth=0.2)
        ax4.legend(bbox_to_anchor=(1, 1), loc="upper left")
        time_format = mdates.DateFormatter('%H:%M:%S')
        ax4.xaxis.set_major_formatter(time_format)
        ax4.set_xlabel('Time')

        plt.savefig('Result_SNR_4/' + binfile[:-4], dpi=500)
        plt.show()
