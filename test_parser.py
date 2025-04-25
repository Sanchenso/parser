import os
import subprocess
import glob
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from shlex import quote
numsecEr = 0

if not os.path.exists('Result_CSV'):
    os.makedirs('Result_CSV')


def parser(binFile):
    arg = binFile[:-4]
    # Генерация имен выходных файлов
    csv_file_navaltitude = quote(arg + "_NavAltitude.csv")
    csv_file_baraltitude = quote(arg + "_BarAltitude.csv")
    csv_file_time = quote(arg + "_TimeDelta.csv")
    csv_file_NavSatInfo = quote(arg + "_NavSatInfo.csv")
    csv_file_NavPrecision = quote(arg + "_NavPrecision.csv")
    csv_file_Rssi = quote(arg + "_Rssi.csv")
    csv_file_LedBoardData = quote(arg + "_LedBoardData.csv")
    csv_file_IntPowerStatus = quote(arg + "_IntPowerStatus.csv")
    csv_file_NavVelocity = quote(arg + "_NavVelocity.csv")
    csv_file_EventLog = quote(arg + "_EventLog.csv")
    csv_file_UavMode = quote(arg + "_UavMode.csv")
    csv_file_Orientation = quote(arg + "_Orientation.csv")
    csv_file_Motor = quote(arg + "_Motor.csv")
    csv_file_RawAccelGyroData = quote(arg + "_RawAccelGyroData.csv")
    csv_file_ExtPowerStatus = quote(arg + "_ExtPowerStatus.csv")
    csv_file_PyroBoardState = quote(arg + "_PyroBoardState.csv")
    ubxFile = quote(arg + ".dat")
    binFile_quoted = quote(binFile)

    # Строим команду
    cmd = (
        f'bash -c "./parser --print_entries {binFile_quoted} | tee '
        f'>(rg NavPosition > {csv_file_navaltitude}) '
        f'>(rg TimeDelta > {csv_file_time}) '
        f'>(rg Altitude > {csv_file_baraltitude}) '
        f'>(rg NavSatInfo > {csv_file_NavSatInfo}) '
        f'>(rg NavPrecision > {csv_file_NavPrecision}) '
        f'>(rg Rssi > {csv_file_Rssi}) '
        f'>(rg LedBoardData > {csv_file_LedBoardData}) '
        f'>(rg IntPowerStatus > {csv_file_IntPowerStatus}) '
        f'>(rg ExtPowerStatus > {csv_file_ExtPowerStatus}) '
        f'>(rg NavVelocity > {csv_file_NavVelocity}) '
        f'>(rg EventLog > {csv_file_EventLog}) '
        f'>(rg UavMode > {csv_file_UavMode}) '
        f'>(rg Orientation > {csv_file_Orientation}) '
        f'>(rg Motor > {csv_file_Motor}) '
        f'>(rg RawAccelGyroData > {csv_file_RawAccelGyroData}) '
        f'>(rg PyroBoardState > {csv_file_PyroBoardState}) '
        f'>/dev/null"'
    )

    # Выполняем команду
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Проверяем и выводим результат
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        print(f"Error Output: {result.stderr.decode()}")
        return

    # Проверяем успешность выполнения второй команды
    result = subprocess.run(
        f"./parser --raw_data {binFile_quoted}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    try:
        os.remove(arg + "_flight_0.gscl")
        os.remove(arg + "_flight_0.params")
        os.remove(arg + "_channel_lua_125.dat")
        os.remove(arg + "_channel_passports_124.dat")
        os.remove(arg + "_channel_telemetry_123.dat")
        os.rename(arg + "_channel_gnss_126.dat", ubxFile)
    except FileNotFoundError as e:
        print(f"Error while trying to remove or rename a file: {e}")
    except OSError as e:
        print(f"OS error occurred: {e}")

    # Проверяем выполнение последней команды
    if result.returncode == 0:
        # Получаем строку с информацией о времени
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
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time',2:'NavLongitude',3:'NavLatitude', 4: 'NavAltitude', 1: 'Drone_Time'})
        df_NavAltitude = df
        df.to_csv(csv_file_navaltitude, index=False)
    except:
        os.remove(csv_file_navaltitude)
        print('No NavAltitude')

    try:
        csv_file_baraltitude = arg + "_BarAltitude.csv"
        df = pd.read_csv(csv_file_baraltitude, header=None, sep=' ', skiprows=2)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'BarAltitude', 1: 'Drone_Time'})
        #fig, ax = plt.subplots()
        df['BarAltitude'] = df['BarAltitude'].astype(float)
        #ax.plot(df['Drone_Time'], df['BarAltitude'])
        df['BarAltitude'] = df['BarAltitude'].ewm(alpha=0.1).mean()
        #ax.plot(df['Drone_Time'], df['BarAltitude'])
        #plt.savefig('Result_BAR/' + arg + '_bar', dpi=500)
        #plt.close()
        df_BarAltitude = df
        df.to_csv(csv_file_baraltitude, index=False)
    except:
        os.remove(csv_file_baraltitude)
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
        os.remove(csv_file_NavSatInfo)
        print('No NavSatInfo')

    try:
        csv_file_NavPrecision = arg + "_NavPrecision.csv"
        df = pd.read_csv(csv_file_NavPrecision, header=None, sep=' ', skiprows=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'PDOP', 3: 'hAccuracy', 4: 'vAccuracy', 5: 'rtk_age', 1: 'Drone_Time'})
        df['rtk_age'] = df['rtk_age']/1000
        df_NavPrecision = df
        df.to_csv(csv_file_NavPrecision, index=False)
    except:
        os.remove(csv_file_NavPrecision)
        print('No NavPrecision')

    try:
        csv_file_Rssi = arg + "_Rssi.csv"
        df = pd.read_csv(csv_file_Rssi, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 3, 4]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'Rssi', 1: 'Drone_Time'})
        df_Rssi = df
        df.to_csv(csv_file_Rssi, index=False)
    except:
        os.remove(csv_file_Rssi)
        print('No Rssi')

    try:
        csv_file_LedBoardData = arg + "_LedBoardData.csv"
        df = pd.read_csv(csv_file_LedBoardData, header=None, sep=' ', skiprows=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'Temp_Driver', 3: 'Temp_Led', 4: 'Current', 1: 'Drone_Time'})
        df_LedBoardData = df
        df.to_csv(csv_file_LedBoardData, index=False)
    except:
        os.remove(csv_file_LedBoardData)
        print('No LedBoardData')


    try:
        csv_file_IntPowerStatus = arg + "_IntPowerStatus.csv"
        df = pd.read_csv(csv_file_IntPowerStatus, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 2]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 3: 'Vbat', 4: 'Percent', 1: 'Drone_Time'})
        df_IntPowerStatus = df
        df.to_csv(csv_file_IntPowerStatus, index=False)
    except:
        os.remove(csv_file_IntPowerStatus)
        print('No IntPowerStatus')
        
    try:
        csv_file_ExtPowerStatus = arg + "_ExtPowerStatus.csv"
        df = pd.read_csv(csv_file_ExtPowerStatus, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1, 2]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 3: 'Vbat', 4: 'Percent', 1: 'Drone_Time'})
        df_ExtPowerStatus = df
        df.to_csv(csv_file_ExtPowerStatus, index=False)
    except:
        os.remove(csv_file_ExtPowerStatus)
        print('No ExtPowerStatus')        

    try:
        csv_file_NavVelocity = arg + "_NavVelocity.csv"
        df = pd.read_csv(csv_file_NavVelocity, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df[5] = round((df[2]**2 + df[3]**2 + df[4]**2)**(0.5),2)
        df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'Velocity1', 3: 'Velocity2', 4: 'Velocity3', 5: 'Velocity'})
        df_csv_file_NavVelocity = df
        df.to_csv(csv_file_NavVelocity, index=False)
    except:
        os.remove(csv_file_NavVelocity)
        print('No NavVelocity')

    try:
        csv_file_EventLog = arg + "_EventLog.csv"
        df = pd.read_csv(csv_file_EventLog, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time',  1: 'Drone_Time', 2: 'EventLog'})
        df_csv_file_EventLog = df
        df.to_csv(csv_file_EventLog, index=False)
    except:
        os.remove(csv_file_EventLog)
        print('No EventLog')  
    
    try:
        csv_file_UavMode = arg + "_UavMode.csv"
        df = pd.read_csv(csv_file_UavMode, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time',  1: 'Drone_Time', 2: 'UavMode'})
        df_csv_file_UavMode = df
        df.to_csv(csv_file_UavMode, index=False)
    except:
        os.remove(csv_file_UavMode)
        print('No UavMode')    

    try:
        csv_file_Orientation = arg + "_Orientation.csv"
        df = pd.read_csv(csv_file_Orientation, header=None, sep=' ', skiprows=1)
        df = df.drop(df.columns[[1]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'Roll', 3: 'Pitch', 4: 'Yav'})
        df_csv_file_Orientation = df
        df.to_csv(csv_file_Orientation, index=False)
    except:
        os.remove(csv_file_Orientation)
        print('No Orientation')           
    
    try:
        csv_file_Motor = arg + "_Motor.csv"
        df = pd.read_csv(csv_file_Motor, header=None, sep=' ', skiprows=10)
        df = df.drop(df.columns[[1, 3]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'MotorID', 4: 'Voltage', 5: 'Current', 6: 'RPM', 7: 'ErrorCount', 8: 'RestartCount'})
        unique_motor_ids = df['MotorID'].unique()
        for motor_number in unique_motor_ids:
            df_Motor = df[df['MotorID'] == motor_number]
            df_Motor.to_csv(arg + '_' + f'Motor_{motor_number}.csv', index=False)
        os.remove(csv_file_Motor)
    except:
        os.remove(csv_file_Motor)
        print('No Motor')  
    
    try:
        csv_file_RawAccelGyroData = arg + "_RawAccelGyroData.csv"
        df = pd.read_csv(csv_file_RawAccelGyroData, header=None, sep=' ', skiprows=10)
        df = df.drop(df.columns[[1, 5]], axis=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'accel_X', 3: 'accel_Y', 4: 'accel_Z', 6: 'gyro_X', 7: 'gyro_Y', 8: 'gyro_Z'})
        df_csv_file_RawAccelGyroData = df
        df.to_csv(csv_file_RawAccelGyroData, index=False)
    except:
        os.remove(csv_file_RawAccelGyroData)
        print('No RawAccelGyroData')   

    try:
        csv_file_PyroBoardState = arg + "_PyroBoardState.csv"
        df = pd.read_csv(csv_file_PyroBoardState, header=None, sep=' ', skiprows=1)
        df[1] = df[0].copy()
        df[0] = df[0].apply(lambda x: convert_time(x, coefficients, polynomial))
        df = df.rename(columns={0: 'GPS_Time', 2: 'channel_1', 3: 'channel_2', 4: 'channel_3', 5: 'channel_4', 1: 'Drone_Time'})
        df_csv_file_PyroBoardState = df
        df.to_csv(csv_file_PyroBoardState, index=False)
    except:
        print('No PyroBoardState')
        os.remove(csv_file_PyroBoardState)
    
    for csvfile in glob.glob('*.csv'):
        if os.path.getsize(csvfile) > 0:
            os.rename(csvfile, 'Result_CSV/' + csvfile)
        else:
            os.remove(csvfile)
