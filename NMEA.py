import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time
import re
import os
import sys
import pynmea2
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.dates import SecondLocator

nameFile = sys.argv[1]  # for example 'test.ubx'
systemName = sys.argv[2]  # for example 'GPS'
IDsystem = sys.argv[3]  # for example 'L1'

nameFile_int, nameFile_ext = os.path.splitext(nameFile) # name for example test, and extension name for example '.ubx'

def create_dir_if_not_exists(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except FileExistsError:
            print('error folder' + directory)
            pass

create_dir_if_not_exists('Result_SNR')
create_dir_if_not_exists('Result_CSV')


data = {}
new_Data = {}
all_sat = {}
all_sat2 = {}
all_satElevation = {}
all_satElevation2 = {}
altitudeGGA = {}
dictRMC = {}
dictTXT = {}

inUse_sat_GPS = []
inUse_sat_Glonass = []
inUse_sat_BeiDou = []
inUse_sat_Galileo = []
PossibleSatInSystem = []
listTimeGGA = []

SYSTEMS = {
    'GPS': {
        'satellite_system': '$GPGSV',
        'gsa_id_system': '1',
        'possible_sat_in_system': list(range(1,33)),
        'in_use': inUse_sat_GPS
    },
    'Glonass': {
        'satellite_system': '$GLGSV',
        'gsa_id_system': '2',
        'possible_sat_in_system': list(range(65, 97)) + list(range(1, 25)),
        'in_use': inUse_sat_Glonass
    },
    'BeiDou': {
        'satellite_system': ['$GBGSV', '$BDGSV'],
        'gsa_id_system': '4',
        'possible_sat_in_system': list(range(1, 64)),
        'in_use': inUse_sat_BeiDou
    },
    'Galileo': {
        'satellite_system': '$GAGSV',
        'gsa_id_system': '3',
        'possible_sat_in_system': list(range(101, 137)) + list(range(1, 37)),
        'in_use': inUse_sat_Galileo
    }
}
possibleNMEA = ['$GPGGA', '$GPGSA', '$GPGGA', '$GNGSA', '$GPGSV', '$GLGSV', '$BDGSV', '$GBGSV', '$GAGSV', '$GNRMC', '$GNGGA', '$GNTXT']

# значение elevation, значения ниже этого в рассчете не участует
MinElevation = 10
# значение SNR, значения ниже этого в рассчете не участуют
minSNR = 20
# значение частоты выдачи сообщений в Герц

numsecEr = 0
flag_GSA = 0
flag_RMC = 0
flag_GGA = 0
flag_GSV = 0
flag_TXT = 0

nSat = 0
countGGA = 0
normstring = 0
countErrorChk = 0
countMess = 0
countChk = 0
averageSNR = 0
countSNR1 = 0


# Проверка входных аргументов. Пример "ally_2J_channel_gnss_126.dat Glonass L2"
try:
    system = SYSTEMS.get(systemName)
    all_sat_chosen, all_satElevation_chosen = (all_sat, all_satElevation) if IDsystem == 'L1' else (all_sat2, all_satElevation2)

    if not system or IDsystem not in ['L1', 'L2']:
        raise KeyError

    satelliteSystem = system['satellite_system']
    GSA_idSystem = system['gsa_id_system']
    inUse_sat_sys = system['in_use']
    PossibleSatInSystem = system['possible_sat_in_system']
except KeyError:
    print('Naming error!')
    print('Please choose from among the following:')
    print('GPS, Glonass, BeiDou, Galileo')
    print('L1 or L2')


# ф-я заполнение словаря all_sat, включающее L1, L2 и др
def SatSnr(snr_dict, lineSat, lineSnr):
    satN = int(newLine[lineSat].strip())
    snrN = newLine[lineSnr].strip()
    if snrN == '':
        value = None
    else:
        value = int(snrN)
    snr_dict.setdefault(satN, {})[time] = value
    return satN, value


# ф-я заполнение словаря satElevation, включающее L1, L2 и др
def SatElevation(elevation_dict, lineSat, lineElev):
    satN = int(newLine[lineSat].strip())
    elevN = newLine[lineElev].strip()
    if elevN == '':
        value = None
    else:
        value = int(elevN)
    elevation_dict.setdefault(satN, {})[time] = value
    return satN, value


# функция парсера сообщений GSV вывод SNR с учетом сообщений GSA (только используемые спутники)
def parserGSV_inUse(line_from_file, inUse_sat_sys):
    satElevation = all_satElevation if line_from_file[-3] == '1' else all_satElevation2
    satSnr = all_sat if line_from_file[-3] == '1' else all_sat2
    if line_from_file[5] != "*":
        for i in range(4, 20, 4):
            if line_from_file.index('*') > i + 3:
                if len(str(line_from_file[i])) < 3 and int(line_from_file[i]) in inUse_sat_sys and int(line_from_file[i]) in PossibleSatInSystem:
                    SatElevation(satElevation, i, i + 1)
                    SatSnr(satSnr, i, i + 3)
    return


# функция парсера сообщений GSV вывод SNR (все видимые спутники)
def parserGSV(line_from_file):
    satElevation = all_satElevation if line_from_file[-3] == '1' else all_satElevation2
    satSnr = all_sat if line_from_file[-3] == '1' else all_sat2
    if line_from_file[5] != "*":
        for i in range(4, 20, 4):
            if line_from_file.index('*') > i + 3:
                if line_from_file[i] != '' and len(str(line_from_file[i])) < 3 and int(line_from_file[i]) in PossibleSatInSystem:
                    SatElevation(satElevation, i, i + 1)
                    SatSnr(satSnr, i, i + 3)
    return


def parserRMC(line_from_file, msg):
    time1 = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
    formatted_output1 = time1.strftime('%H:%M:%S.%f')
    velocity = round(1.852 / 3.6 * float(check_argument(msg.spd_over_grnd)), 2)
    dictRMC[formatted_output1] = msg.status, msg.mode_indicator, msg.nav_status, velocity
    return


def parserGGA(line_from_file, msg):
    time = datetime.strptime(str(line_from_file[1].strip()), '%H''%M''%S.%f') + timedelta(seconds=18)
    listTimeGGA.append(line_from_file[1])
    formatted_output = time.strftime('%H:%M:%S.%f')
    altitudeGGA[formatted_output] = float(check_argument(msg.altitude)), float(
        check_argument(msg.age_gps_data)), int(msg.gps_qual)
    return time


def parserGSA(line_from_file):
    for i in range(3, len(line_from_file) - 6):
        if line_from_file[i] != '':
            inUse_sat_sys.append(int(line_from_file[i]))
    return

def parserTXT(line_from_file, time):
    check_argument(str(line_from_file))
    dictTXT[time.strftime('%H:%M:%S.%f')] = line_from_file[1:-2] # без контрольной суммы и маски сообщения
    return

# функция проверка чексуммы сообщений NMEA
def chksum_nmea(sentence):
    # This is a string, will need to convert it to hex for
    # proper comparsion below
    global countErrorChk, countChk
    normstring = ",".join(sentence)
    if sentence[-2] != '*':
        countErrorChk += 1
        return False

    cksum = sentence[-1]
    if len(cksum) != 3:
        countErrorChk += 1
        return False
    # String slicing: Grabs all the characters
    # between '$' and '*' and nukes any lingering
    # newline or CRLF
    chksumdata = re.sub("(\n|\r\n)", "", normstring[normstring.find("$") + 1:normstring.find("*") - 1])
    # Initializing our first XOR value
    csum = 0

    # For each char in chksumdata, XOR against the previous
    # XOR'd char.  The final XOR of the last char will be our
    # checksum to verify against the checksum we sliced off
    # the NMEA sentence

    for c in chksumdata:
        # XOR'ing value of csum against the next char in line
        # and storing the new XOR value in csum
        csum ^= ord(c)
    try:
        hex(int(cksum.lower(), 16))
    except:
        countErrorChk += 1
        return False

    # Do we have a validated sentence?
    if hex(csum) == hex(int(cksum.lower(), 16)):
        countChk += 1
        return True
    countErrorChk += 1
    return False


# функция вывода данных в список для записи в файл
def average(dataDict):
    list_Average = []
    list_count_Average = []
    list_Sat = []

    for numerOfSat, values in dataDict.items():
        clean_values = [int(v) for v in values.values() if v is not None and v != '']
        if clean_values:
            avg = float(round(sum(clean_values) / len(clean_values), 1))
            list_Average.append(avg)
            list_count_Average.append(len(clean_values))
            list_Sat.append(numerOfSat)

    return list_Average, list_count_Average, list_Sat


def check_argument(arg):
    global numsecEr
    default_value = -1  # или любое другое значение по умолчанию
    if not arg:
        numsecEr += 1
        return default_value
    try:
        return float(arg)
    except ValueError:
        numsecEr += 1
        return default_value

# Base перебор сообщений из файла
with open(nameFile, encoding="CP866") as inf2:
    for line in inf2:
        sym = -1
        for i in set(possibleNMEA):
            start_index = line.find(i)
            if start_index == -1:
                continue
            split_line = line[start_index:].split(',')
            if len(split_line) < 2 or split_line[1] == '':
                countErrorChk += 1
                break
            try:
                newLine = line[start_index::].replace('*', ',*,').split(',')
                msg = pynmea2.parse(line[start_index:].strip())
                if '$GNGGA' in newLine and newLine[1] != '' and chksum_nmea(newLine):
                    flag_GGA = 1
                    countGGA += 1
                    inUse_sat_sys = []
                    time = parserGGA(newLine, msg)
                    break
                elif '$GNGSA' in newLine and countGGA >= 1 and (newLine[2] == '2' or newLine[2] == '3') \
                        and newLine[-3] == GSA_idSystem and chksum_nmea(newLine):
                    flag_GSA = 1
                    parserGSA(newLine)
                    break
                elif newLine[0] in satelliteSystem and countGGA >= 1 and chksum_nmea(newLine):
                    if flag_GSA == 1:
                        parserGSV_inUse(newLine, inUse_sat_sys)
                    else:
                        flag_GSV = 1
                        parserGSV(newLine)
                    break
                elif '$GNRMC' in newLine and countGGA >= 1:
                    flag_RMC = 1
                    parserRMC(newLine, msg)
                    break
                elif '$GNTXT' in newLine and countGGA >= 1:
                    flag_TXT = 1
                    parserTXT(newLine, time)
            except pynmea2.ParseError:
                countErrorChk += 1
                continue

if flag_GGA != 0:
    '''
    # Подсчет кол-ва сообщений, прошедших проверку  cheksumm
    print('Number of messages:', end=' ')
    print(countChk)
    print('Number of error chksum:', end=' ')
    print(countErrorChk)
    print('Number of skip packet:', end=' ')
    print(numsecEr)
    print('Number of GGA messages:', end=' ')
    print(countGGA)
    print()
   '''
    # еще один подсчет времени по сообщениям GGA
    last = datetime.strptime(listTimeGGA[-1], '%H''%M''%S.%f')
    first = datetime.strptime(listTimeGGA[0], '%H''%M''%S.%f')
    time_of_flight = int((last - first).total_seconds())
    print('DifTime from first and last GGA:', end=' ')
    print(time_of_flight, 'sec')

    df = pd.DataFrame(list(altitudeGGA.items()), columns=["GPS_Time", "Values"])
    df[["Altitude", "rtkAGE", "Status"]] = pd.DataFrame(df.Values.tolist(), index=df.index)
    df.drop(["Values"], axis=1, inplace=True)
    df.to_csv(f'Result_CSV/{nameFile_int}_GGA.csv', index=False, escapechar="\\")


if flag_RMC != 0:
    df2 = pd.DataFrame(list(dictRMC.items()), columns=["GPS_Time", "Values"])
    df2[["status", "mode_indicator", "nav_status", "Speed"]] = pd.DataFrame(df2.Values.tolist(), index=df2.index)
    df2.drop(["Values"], axis=1, inplace=True)
    df2.to_csv(f'Result_CSV/{nameFile_int}_RMC.csv', index=False, escapechar="\\")

if flag_TXT != 0:
    df3 = pd.DataFrame(list(dictTXT.items()), columns=["GPS_Time", "Values"])
    values_df = pd.DataFrame(df3['Values'].tolist())
    df3.drop(columns=['Values'], inplace=True)
    df3 = df3.join(values_df)
    df3.to_csv(f'Result_CSV/{nameFile_int}_TXT.csv', index=False, escapechar="\\")

if flag_GSA != 0 or flag_GSV != 0:
    p = average(all_sat_chosen)
    m = average(all_satElevation_chosen)
    for i in range(len(p[0])):
        if p[1][i] > ((last - first).total_seconds() * 0.5) and p[0][i] > minSNR:
            averageSNR += p[0][i]
            countSNR1 += 1
        else:
            print('Sat', p[2][i], 'CountValue', p[1][i], 'CountSec', round((last - first).total_seconds()), '\n',
                  'Check log! Many missing values!')
            continue
    print()
    print('average SNR: ', end='')
    if countSNR1 != 0:
        print(round((averageSNR / countSNR1), 1))
        print('number of sat average SNR: ', end='')
        print(countSNR1)
    print()
    Average = 0
    schet = 0
    gh = 0

    # дозапись осреденных в файл test.txt - для скрипта
    with open('Result_SNR/test.txt', 'a') as f1:
        f1.write(nameFile_int)
        f1.write('_')
        f1.write(systemName)
        f1.write('_')
        f1.write(IDsystem)
        f1.write(' ')
        # f1.write(str(round((Average / schet), 1)))
        f1.write(str(round((averageSNR / countSNR1), 1)))
        f1.write(' ')
        f1.write(str(gh))
        f1.write(' ')
        f1.write(str(countGGA))  # number of GGA messages
        f1.write(' ')
        f1.write(str(countErrorChk))  # ErrMes
        f1.write(' ')
        f1.write(str(round((last - first).total_seconds())))  # DifTime from first and last GGA
        f1.write('\n')

    df3 = pd.DataFrame(all_sat_chosen)
    #df3 = df3.fillna(0).astype(int)
    df3.index = df3.index.to_series().apply(lambda x: x.to_pydatetime().time())
    df3.to_csv('Result_CSV/' + nameFile_int + '_' + systemName + '_' + IDsystem + '_SNR.csv', index=True)

    # вывод графика и сохранение в jpeg
    result = all_sat_chosen.values()
    # вывод и сохранение графика в формате jpeg
    fig, ax = plt.subplots(figsize=(12, 8))

    for k in result:
        k = {key: value for (key, value) in k.items() if value}
        myList = sorted(k.items())
        if myList:
            x, y = zip(*myList)
            ax.plot(x, y, marker='o', markersize=2)
    
    interval_time_of_flight = time_of_flight//8
    # Formatter для отображения времени  
    time_format = mdates.DateFormatter('%H:%M:%S')
    # Locator для определения интервала 
    locator = SecondLocator(interval=interval_time_of_flight)
    ax.xaxis.set_major_locator(locator) # Задаем интервал
    ax.xaxis.set_major_formatter(time_format)
    
    ax.set_xlabel('Time', fontsize=14)
    ax.set_ylabel('SNR, dBHz', fontsize=14)
    ax.text(0.01, 0.98, 'average SNR:', fontsize=14, transform=ax.transAxes, verticalalignment='top')
    ax.text(0.01, 0.94, f'{round((averageSNR / countSNR1), 1)} dBHz', fontsize=14, transform=ax.transAxes, verticalalignment='top')
    ax.set_title(nameFile + ", " + systemName + '_' + IDsystem, fontsize=14)
    ax.set_ylim(10, 60)
    ax.grid(color='black', linestyle='--', linewidth=0.2)
    ax.legend([], [],loc="upper left", frameon=False)
    ax.legend(all_sat_chosen.keys(), loc='upper right')
    
    nameFileSaved = nameFile_int + '_' + systemName + '_' + IDsystem + '.png'
    plt.savefig('Result_SNR/' + nameFileSaved, dpi=100)
    #plt.show()
    plt.close()

    
