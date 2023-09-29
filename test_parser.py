import os
import subprocess
import glob
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pynmea2
import matplotlib.pyplot as plt
numsecEr = 0

if not os.path.exists('Result_CSV'):
    os.makedirs('Result_CSV')
if not os.path.exists('Result_BAR'):
    os.makedirs('Result_BAR')


def parser(binFile):
    arg = binFile[:-4]
    csv_file_navaltitude = arg + "_NavAltitude.csv"
    csv_file_baraltitude = arg + "_BarAltitude.csv"
    csv_file_time = arg + "_TimeDelta.csv"
    csv_file_NavSatInfo = arg + "_NavSatInfo.csv"
    csv_file_NavPrecision = arg + "_NavPrecision.csv"
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
        None

    # проверяем успешность выполнения скрипта
    if result.returncode == 0:
        # получаем строку с информацией о времени
        output_lines = result.stdout.decode().split('\n')
        print('Start', output_lines[1].strip()[34:55])
        print('End  ', output_lines[1].strip()[67:-6])
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


data = []
files = glob.glob('*.bin')
for binFile in files:
    arg = binFile[:-4]
    print(arg)
    parser(binFile)

    try:
        csv_file_time = arg + "_TimeDelta.csv"
        coefficients, polynomial = parser_time(csv_file_time)
    except:
        print('No TimeDelta')

    try:
        csv_file_navaltitude = arg + "_NavAltitude.csv"
        df = pd.read_csv(csv_file_navaltitude, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 2, 3]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 4: 'NavAltitude', 1: 'Drone_Time'})
        df_NavAltitude = df
        df.to_csv(csv_file_navaltitude, index=False)
    except:
        print('No NavAltitude')

    try:
        csv_file_baraltitude = arg + "_BarAltitude.csv"
        df = pd.read_csv(csv_file_baraltitude, header=None, sep=' ', skiprows=2)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'BarAltitude', 1: 'Drone_Time'})
        fig, ax = plt.subplots()
        df['BarAltitude'] = df['BarAltitude'].astype(float)
        ax.plot(df['Drone_Time'], df['BarAltitude'])
        df['BarAltitude'] = df['BarAltitude'].ewm(alpha=0.1).mean()
        ax.plot(df['Drone_Time'], df['BarAltitude'])
        plt.savefig('Result_BAR/' + arg + '_bar', dpi=500)
        #plt.show()
        df_BarAltitude = df
        df.to_csv(csv_file_baraltitude, index=False)
    except:
        print('No BarAltitude')

    try:
        csv_file_NavSatInfo = arg + "_NavSatInfo.csv"
        df = pd.read_csv(csv_file_NavSatInfo, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 3, 4, 5, 6, 7, 8, 9]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'NSI_Status', 10: 'NavSatInfo', 1: 'Drone_Time'})
        df_NavSatInfo = df
        df.to_csv(csv_file_NavSatInfo, index=False)
    except:
        print('No NavSatInfo')

    try:
        csv_file_NavPrecision = arg + "_NavPrecision.csv"
        df = pd.read_csv(csv_file_NavPrecision, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 5]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'PDOP', 3: 'vAccuracy', 4: 'hAccuracy', 1: 'Drone_Time'})
        df_NavPrecision = df
        df.to_csv(csv_file_NavPrecision, index=False)
    except:
        print('No NavPrecision')

    for csvfile in glob.glob('*.csv'):
        os.rename(csvfile, 'Result_CSV/' + csvfile)

