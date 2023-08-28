import os
import subprocess
import glob
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pynmea2
import matplotlib.pyplot as plt


def parser(binFile):
    arg = binFile[:-4]
    csv_file_navaltitude = arg + "_NavAltitude.csv"
    csv_file_baraltitude = arg + "_BarAltitude.csv"
    csv_file_time = arg + "_TimeDelta.csv"
    csv_file_NavSatInfo = arg + "_NavSatInfo.csv"
    csv_file_NavPrecision = arg + "_NavPrecision.csv"
    ubxFile = arg + ".dat"

    try:
        result = subprocess.run("./parser --print_entries " + binFile + " |rg NavPosition > " + csv_file_navaltitude,
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run("./parser --print_entries " + binFile + " |rg TimeDelta > " + csv_file_time, shell=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run("./parser --print_entries " + binFile + " |rg Altitude > " + csv_file_baraltitude, shell=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run("./parser --print_entries " + binFile + " |rg NavSatInfo > " + csv_file_NavSatInfo, shell=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run("./parser --print_entries " + binFile + " |rg NavPrecision > " + csv_file_NavPrecision,
                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        subprocess.run("./parser --raw_data " + binFile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    except:
        print(binFile, " are not parsing!")
    # удаляем ненужное

    try:
        os.remove(arg + "_flight_0.gscl")
        os.remove(arg + "_flight_0.params")
        os.remove(arg + "_channel_lua_125.dat")
        os.remove(arg + "_channel_passports_124.dat")
        os.remove(arg + "_channel_telemetry_123.dat")
        os.rename(arg + "_channel_gnss_126.dat", ubxFile)
    except:
        print("not parser some files")

    # проверяем успешность выполнения скрипта
    if result.returncode == 0:
        # получаем строку с информацией о времени
        output_lines = result.stdout.decode().split('\n')
        for line in output_lines[-2]:
            if "Flight time:" in line:
                flight_time_start = datetime.strptime(line.strip()[34:55], '%Y-%m-%dT%H:%M:%S.%f')
                print('Start', flight_time_start)
                flight_time_end = datetime.strptime(line.strip()[67:-6], '%Y-%m-%dT%H:%M:%S.%f')
                print('End  ', flight_time_end)
    else:
        print("Ошибка выполнения скрипта!")


def parser_time(csv_file_time):
    # функция линейной аппроксимации TimeDelta
    df = pd.read_csv(csv_file_time, header=None, sep=' ', skiprows=1)
    x = df[0].astype(float)
    y = df[2].astype(float)
    coefficients = np.polyfit(x, y, 1)
    polynomial = np.poly1d(coefficients)
    try:
        os.remove(csv_file_time)
    except:
        print("not file TimeDelta")
    return coefficients, polynomial


def convert_time(value, coefficients, polynomial):
    # Функция конвертации времени из TimeDelta
    y_approx = polynomial(value) / 1000000 + value
    gps_start_date = datetime(1980, 1, 6, 0, 0, 0)
    utc_time = gps_start_date + timedelta(seconds=float(y_approx))
    formatted_output = utc_time.strftime('%H:%M:%S.%f')
    return formatted_output


def check_argument(arg):
    if arg is not None:
        try:
            return float(arg)
        except ValueError:
            print("arg isn't int,float,str")
            return None
    else:
        print("arg is None")
        return None


def NMEA_altitude(nameFile):
    altitude = {}
    timestamps = []
    dictRMC = {}
    dictSpeedTime = {}
    numsec = 0
    numsecEr = 0
    arg = nameFile[:-4]
    with open(nameFile, 'r', encoding="CP866") as file:
        print('Time_Error:', end='\n')
        nmeaMSG = ['$GNGGA', '$GNRMC']
        for line in file:
            for i in nmeaMSG:
                start_index = line.find(i)
                if start_index == -1:
                    continue
                elif line[start_index:].split(',')[1] == '':
                    numsecEr += 1
                    continue
                numsec += 1
                try:
                    message = line[start_index:].strip()
                    msg = pynmea2.parse(message)
                    if '$GNGGA' in message:
                        # Получаем время из сообщения
                        listMsgGGA = [msg.altitude, msg.age_gps_data, msg.gps_qual]
                        Time = str(message.split(',')[1].strip())
                        time = datetime.strptime(Time, '%H''%M''%S.%f') + timedelta(seconds=18)
                        formatted_output = time.strftime('%H:%M:%S.%f')
                        if map(check_argument, listMsgGGA):
                            altitude[formatted_output] = float(msg.altitude), float(msg.age_gps_data), int(msg.gps_qual)
                        else:
                            print(time, 'skipped messege')
                            numsecEr += 1
                    elif 'GNRMC' in message:
                        listMsgRMC = [msg.status, msg.mode_indicator, msg.nav_status]
                        if map(check_argument, listMsgRMC):
                            Time1 = str(message.split(',')[1].strip())
                            time1 = datetime.strptime(Time1, '%H''%M''%S.%f') + timedelta(seconds=18)
                            formatted_output1 = time1.strftime('%H:%M:%S.%f')
                            dictRMC[formatted_output1] = msg.status, msg.mode_indicator, msg.nav_status
                except pynmea2.ParseError:
                    continue
    print('Number of massage NMEA:', numsec)
    print('Number of error value NMEA:', numsecEr)
    return altitude, dictRMC


data = []
files = glob.glob('*.bin')
for binFile in files:
    arg = binFile[:-4]
    print(arg)
    parser(binFile)
    csv_file_time = arg + "_TimeDelta.csv"
    coefficients, polynomial = parser_time(csv_file_time)

    csv_file_navaltitude = arg + "_NavAltitude.csv"
    df = pd.read_csv(csv_file_navaltitude, header=None, sep=' ', skiprows=1)
    df = df.drop(df.columns[[1, 2, 3]], axis=1)
    df[1] = df[0].copy()
    df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
    df = df.rename(columns={0: 'GPS_Time', 4: 'NavAltitude', 1: 'Drone_Time'})
    df_NavAltitude = df
    df.to_csv(csv_file_navaltitude, index=False)

    csv_file_baraltitude = arg + "_BarAltitude.csv"
    df = pd.read_csv(csv_file_baraltitude, header=None, sep=' ', skiprows=2)
    df = df.drop(df.columns[[1]], axis=1)
    df[1] = df[0].copy()
    df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
    df = df.rename(columns={0: 'GPS_Time', 2: 'BarAltitude', 1: 'Drone_Time'})

    fig, ax = plt.subplots()
    df['BarAltitude'] = df['BarAltitude'].astype(float)
    ax.plot(df['Drone_Time'], df['BarAltitude'])
    df['BarAltitude'] = df['BarAltitude'].ewm(alpha=0.2).mean()
    ax.plot(df['Drone_Time'], df['BarAltitude'])
    plt.show()
    df_BarAltitude = df
    df.to_csv(csv_file_baraltitude, index=False)

    csv_file_NavSatInfo = arg + "_NavSatInfo.csv"
    df = pd.read_csv(csv_file_NavSatInfo, header=None, sep=' ', skiprows=1)
    df = df.drop(df.columns[[1, 3, 4, 5, 6, 7, 8, 9]], axis=1)
    df[1] = df[0].copy()
    df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
    df = df.rename(columns={0: 'GPS_Time', 2: 'NSI_Status', 10: 'NavSatInfo', 1: 'Drone_Time'})
    df_NavSatInfo = df
    df.to_csv(csv_file_NavSatInfo, index=False)

    csv_file_NavPrecision = arg + "_NavPrecision.csv"
    df = pd.read_csv(csv_file_NavPrecision, header=None, sep=' ', skiprows=1)
    df = df.drop(df.columns[[1, 5]], axis=1)
    df[1] = df[0].copy()
    df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
    df = df.rename(columns={0: 'GPS_Time', 2: 'PDOP', 3: 'vAccuracy', 4: 'hAccuracy', 1: 'Drone_Time'})
    df_NavPrecision = df
    df.to_csv(csv_file_NavPrecision, index=False)

    ubxFile = arg + ".dat"
    altitude, dictRMC = NMEA_altitude(ubxFile)
    df = pd.DataFrame(list(altitude.items()), columns=["GPS_Time", "Values"])
    df2 = pd.DataFrame(list(dictRMC.items()), columns=["GPS_Time", "Values"])
    # Разделить колонку "Values" на две колонки
    df[['Altitude', 'rtkAGE', 'Status']] = pd.DataFrame(df.Values.tolist(), index=df.index)
    df2[["status", "mode_indicator", "nav_status"]] = pd.DataFrame(df2.Values.tolist(), index=df2.index)
    # Удалить колонку "Values"
    df = df.drop(["Values"], axis=1)
    df2 = df2.drop(["Values"], axis=1)
    df_NMEA = df
    df_RMC_NMEA = df2
    df2.to_csv(arg + '_NMEA.csv', index=False)

    df_NMEA['GPS_Time'] = pd.to_datetime(df_NMEA['GPS_Time'], format='%H:%M:%S.%f')
    df_RMC_NMEA['GPS_Time'] = pd.to_datetime(df_RMC_NMEA['GPS_Time'], format='%H:%M:%S.%f')
    df_NavAltitude['GPS_Time'] = pd.to_datetime(df_NavAltitude['GPS_Time'], format='%H:%M:%S.%f')
    df_BarAltitude['GPS_Time'] = pd.to_datetime(df_BarAltitude['GPS_Time'], format='%H:%M:%S.%f')
    df_NavSatInfo['GPS_Time'] = pd.to_datetime(df_NavSatInfo['GPS_Time'], format='%H:%M:%S.%f')
    df_NavPrecision['GPS_Time'] = pd.to_datetime(df_NavSatInfo['GPS_Time'], format='%H:%M:%S.%f')

    # Нормируем высоту NMEA
    first_altitude = df_NMEA['Altitude'].iloc[0]
    df_NMEA['Altitude'] = df_NMEA['Altitude'].apply(lambda x: x - first_altitude)

    # Нормируем высоту NAV-POSLLH
    first_altitude = df_NavAltitude['NavAltitude'].iloc[0]
    df_NavAltitude['NavAltitude'] = df_NavAltitude['NavAltitude'].apply(lambda x: x - first_altitude)

    # Нормируем высоту барометра
    first_altitude = df_BarAltitude['BarAltitude'].iloc[0]
    df_BarAltitude['BarAltitude'] = df_BarAltitude['BarAltitude'].apply(lambda x: x - first_altitude)

    fig = plt.figure(figsize=(14, 18))

    # Строим графики высоты NMEA + Altitude barometr
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.plot(df_NavAltitude['GPS_Time'], df_NavAltitude['NavAltitude'], marker='o', markersize=1, color='g',
             label='NavAltitude')
    ax1.plot(df_BarAltitude['GPS_Time'], df_BarAltitude['BarAltitude'].astype(float), marker='o', markersize=1,
             color='b', label='barometr_Altitude')

    # Устанавливаем названия осей и засечки для первого графика
    ax1.set_ylabel('Altitude, m', fontsize=12)
    ax1.grid(True, linestyle=':')
    ax1.set_title(arg, fontsize=18)  # наименование графика
    ax1.legend(loc="upper left")

    # строим графики статусов GNSS NAVauto + NMEA
    ax2 = fig.add_subplot(4, 1, 2)
    ax2.plot(df_NavSatInfo['GPS_Time'], df_NavSatInfo['NSI_Status'], marker='o', markersize=4, color='g',
             label='NAVauto_Status_NSI')
    ax2.plot(df_NavSatInfo['GPS_Time'], df_NavSatInfo['NavSatInfo'], marker='o', markersize=4, color='r',
             label='NAVauto_Status_RTK')
    ax2.plot(df_NMEA['GPS_Time'], df_NMEA['Status'], marker='o', markersize=4, color='b', label='NMEA_status')

    # Устанавливаем названия осей и засечки для второго графика
    ax2.set_ylabel('Status NMEA', fontsize=12)
    ax2.grid(True, linestyle=':')
    ax2.legend(loc="upper left")

    # строим графики NAV_Precission
    ax3 = fig.add_subplot(4, 1, 3)
    ax3.plot(df_NavPrecision['GPS_Time'], df_NavPrecision['vAccuracy'], marker='o', markersize=4, color='g',
             label='vAccuracy')
    ax3.plot(df_NavPrecision['GPS_Time'], df_NavPrecision['hAccuracy'], marker='o', markersize=4, color='r',
             label='hAccuracy')

    # Устанавливаем названия осей и засечки для третьего графика
    ax3.set_ylabel('Precision, mm', fontsize=12)
    ax3.grid(True, linestyle=':')
    ax3.legend(loc="upper left")

    # строим графики статусов RMC NMEA
    ax4 = fig.add_subplot(4, 1, 4)
    ax4.plot(df_RMC_NMEA['GPS_Time'], df_RMC_NMEA['status'], marker='o', markersize=4, color='g', label='RMC_status')
    ax4.plot(df_RMC_NMEA['GPS_Time'], df_RMC_NMEA['mode_indicator'], marker='o', markersize=4, color='r',
             label='mode_indicator')
    ax4.plot(df_RMC_NMEA['GPS_Time'], df_RMC_NMEA['nav_status'], marker='o', markersize=4, color='b',
             label='nav_status')

    # Устанавливаем названия осей и засечки для второго графика
    ax4.set_xlabel('Time', fontsize=12)
    ax4.set_ylabel('Status RMC', fontsize=12)
    ax4.grid(True, linestyle=':')
    ax4.legend(loc="upper left")

    # Показываем графики
    plt.savefig(arg, dpi=500)
    plt.show()