import os
import subprocess
import glob
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from shlex import quote
import logging
from typing import Optional, Tuple, Dict, Any, List

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BinParser:
    """Класс для парсинга бинарных файлов и обработки CSV данных"""

    def __init__(self, bin_file: str):
        self.bin_file = bin_file
        self.arg = bin_file[:-4]
        self.coefficients: Optional[np.ndarray] = None
        self.polynomial: Optional[np.poly1d] = None
        self.numsecEr = 0

        # Создание директории Result_CSV если не существует
        if not os.path.exists('Result_CSV'):
            os.makedirs('Result_CSV')

    def parser(self) -> bool:
        """Основной метод парсинга бинарного файла"""
        # Генерация имен выходных файлов (сохранены оригинальные имена)
        csv_file_navaltitude = quote(self.arg + "_NavAltitude.csv")
        csv_file_baraltitude = quote(self.arg + "_BarAltitude.csv")
        csv_file_time = quote(self.arg + "_TimeDelta.csv")
        csv_file_NavSatInfo = quote(self.arg + "_NavSatInfo.csv")
        csv_file_NavPrecision = quote(self.arg + "_NavPrecision.csv")
        csv_file_Rssi = quote(self.arg + "_Rssi.csv")
        csv_file_LedBoardData = quote(self.arg + "_LedBoardData.csv")
        csv_file_IntPowerStatus = quote(self.arg + "_IntPowerStatus.csv")
        csv_file_NavVelocity = quote(self.arg + "_NavVelocity.csv")
        csv_file_EventLog = quote(self.arg + "_EventLog.csv")
        csv_file_UavMode = quote(self.arg + "_UavMode.csv")
        csv_file_Orientation = quote(self.arg + "_Orientation.csv")
        csv_file_Motor = quote(self.arg + "_Motor.csv")
        csv_file_RawAccelGyroData = quote(self.arg + "_RawAccelGyroData.csv")
        csv_file_ExtPowerStatus = quote(self.arg + "_ExtPowerStatus.csv")
        csv_file_PyroBoardState = quote(self.arg + "_PyroBoardState.csv")
        ubxFile = quote(self.arg + ".dat")
        binFile_quoted = quote(self.bin_file)

        # Строим команду (сохранена оригинальная структура)
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
            return False

        # Проверяем успешность выполнения второй команды
        result = subprocess.run(
            f"./parser --raw_data {binFile_quoted}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        try:
            # Удаление временных файлов (сохранены оригинальные имена)
            os.remove(self.arg + "_flight_0.gscl")
            os.remove(self.arg + "_flight_0.params")
            os.remove(self.arg + "_channel_lua_125.dat")
            os.remove(self.arg + "_channel_passports_124.dat")
            os.remove(self.arg + "_channel_telemetry_123.dat")
            os.rename(self.arg + "_channel_gnss_126.dat", ubxFile)
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
            return True
        else:
            print("Ошибка выполнения скрипта!")
            return False

    def parser_time(self, csv_file_time: str) -> Tuple[Optional[np.ndarray], Optional[np.poly1d]]:
        """функция линейной аппроксимации TimeDelta"""
        try:
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
        except Exception as e:
            print(f"Error in parser_time: {e}")
            return None, None

    def convert_time(self, value: float, coefficients: np.ndarray, polynomial: np.poly1d) -> str:
        """Функция конвертации времени из TimeDelta"""
        y_approx = polynomial(value) / 1000000 + value
        gps_start_date = datetime(1980, 1, 6, 0, 0, 0)
        utc_time = gps_start_date + timedelta(seconds=float(y_approx))
        formatted_output = utc_time.strftime('%H:%M:%S.%f')
        return formatted_output

    def process_nav_altitude(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка NavAltitude.csv"""
        try:
            csv_file_navaltitude = self.arg + "_NavAltitude.csv"
            df = pd.read_csv(csv_file_navaltitude, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(
                columns={0: 'GPS_Time', 2: 'NavLongitude', 3: 'NavLatitude', 4: 'NavAltitude', 1: 'Drone_Time'})
            df.to_csv(csv_file_navaltitude, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_navaltitude)
            print('No NavAltitude')
            return False

    def process_bar_altitude(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка BarAltitude.csv"""
        try:
            csv_file_baraltitude = self.arg + "_BarAltitude.csv"
            df = pd.read_csv(csv_file_baraltitude, header=None, sep=' ', skiprows=2)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 2: 'BarAltitude', 1: 'Drone_Time'})
            df['BarAltitude'] = df['BarAltitude'].astype(float)
            df['BarAltitude'] = df['BarAltitude'].ewm(alpha=0.1).mean()
            df.to_csv(csv_file_baraltitude, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_baraltitude)
            print('No BarAltitude')
            return False

    def process_nav_sat_info(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка NavSatInfo.csv"""
        try:
            csv_file_NavSatInfo = self.arg + "_NavSatInfo.csv"
            df = pd.read_csv(csv_file_NavSatInfo, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1, 3, 4, 5, 6, 7, 8, 9]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 2: 'NSI_Status', 10: 'NavSatInfo', 1: 'Drone_Time'})
            df.to_csv(csv_file_NavSatInfo, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_NavSatInfo)
            print('No NavSatInfo')
            return False

    def process_nav_precision(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка NavPrecision.csv"""
        try:
            csv_file_NavPrecision = self.arg + "_NavPrecision.csv"
            df = pd.read_csv(csv_file_NavPrecision, header=None, sep=' ', skiprows=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(
                columns={0: 'GPS_Time', 2: 'PDOP', 3: 'hAccuracy', 4: 'vAccuracy', 5: 'rtk_age', 1: 'Drone_Time'})
            df['rtk_age'] = df['rtk_age'] / 1000
            df.to_csv(csv_file_NavPrecision, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_NavPrecision)
            print('No NavPrecision')
            return False

    def process_rssi(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка Rssi.csv"""
        try:
            csv_file_Rssi = self.arg + "_Rssi.csv"
            df = pd.read_csv(csv_file_Rssi, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1, 3, 4]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 2: 'Rssi', 1: 'Drone_Time'})
            df.to_csv(csv_file_Rssi, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_Rssi)
            print('No Rssi')
            return False

    def process_led_board_data(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка LedBoardData.csv"""
        try:
            csv_file_LedBoardData = self.arg + "_LedBoardData.csv"
            df = pd.read_csv(csv_file_LedBoardData, header=None, sep=' ', skiprows=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 2: 'Temp_Driver', 3: 'Temp_Led', 4: 'Current', 1: 'Drone_Time'})
            df.to_csv(csv_file_LedBoardData, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_LedBoardData)
            print('No LedBoardData')
            return False

    def process_int_power_status(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка IntPowerStatus.csv"""
        try:
            csv_file_IntPowerStatus = self.arg + "_IntPowerStatus.csv"
            df = pd.read_csv(csv_file_IntPowerStatus, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1, 2]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 3: 'Vbat', 4: 'Percent', 1: 'Drone_Time'})
            df.to_csv(csv_file_IntPowerStatus, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_IntPowerStatus)
            print('No IntPowerStatus')
            return False

    def process_ext_power_status(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка ExtPowerStatus.csv"""
        try:
            csv_file_ExtPowerStatus = self.arg + "_ExtPowerStatus.csv"
            df = pd.read_csv(csv_file_ExtPowerStatus, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1, 2]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 3: 'Vbat', 4: 'Percent', 1: 'Drone_Time'})
            df.to_csv(csv_file_ExtPowerStatus, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_ExtPowerStatus)
            print('No ExtPowerStatus')
            return False

    def process_nav_velocity(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка NavVelocity.csv"""
        try:
            csv_file_NavVelocity = self.arg + "_NavVelocity.csv"
            df = pd.read_csv(csv_file_NavVelocity, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df[5] = round((df[2] ** 2 + df[3] ** 2 + df[4] ** 2) ** (0.5), 2)
            df = df.rename(
                columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'Velocity1', 3: 'Velocity2', 4: 'Velocity3', 5: 'Velocity'})
            df.to_csv(csv_file_NavVelocity, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_NavVelocity)
            print('No NavVelocity')
            return False

    def process_event_log(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка EventLog.csv"""
        try:
            csv_file_EventLog = self.arg + "_EventLog.csv"
            df = pd.read_csv(csv_file_EventLog, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'EventLog'})
            df.to_csv(csv_file_EventLog, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_EventLog)
            print('No EventLog')
            return False

    def process_uav_mode(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка UavMode.csv"""
        try:
            csv_file_UavMode = self.arg + "_UavMode.csv"
            df = pd.read_csv(csv_file_UavMode, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'UavMode'})
            df.to_csv(csv_file_UavMode, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_UavMode)
            print('No UavMode')
            return False

    def process_orientation(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка Orientation.csv"""
        try:
            csv_file_Orientation = self.arg + "_Orientation.csv"
            df = pd.read_csv(csv_file_Orientation, header=None, sep=' ', skiprows=1)
            df = df.drop(df.columns[[1]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'Roll', 3: 'Pitch', 4: 'Yav'})
            df.to_csv(csv_file_Orientation, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_Orientation)
            print('No Orientation')
            return False

    def process_motor(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка Motor.csv"""
        try:
            csv_file_Motor = self.arg + "_Motor.csv"
            df = pd.read_csv(csv_file_Motor, header=None, sep=' ', skiprows=10)
            df = df.drop(df.columns[[1, 3]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'MotorID', 4: 'Voltage', 5: 'Current', 6: 'RPM',
                                    7: 'ErrorCount', 8: 'RestartCount'})
            unique_motor_ids = df['MotorID'].unique()
            for motor_number in unique_motor_ids:
                df_Motor = df[df['MotorID'] == motor_number]
                df_Motor.to_csv(self.arg + '_' + f'Motor_{motor_number}.csv', index=False)
            os.remove(csv_file_Motor)
            return True
        except Exception as e:
            os.remove(csv_file_Motor)
            print('No Motor')
            return False

    def process_raw_accel_gyro_data(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка RawAccelGyroData.csv"""
        try:
            csv_file_RawAccelGyroData = self.arg + "_RawAccelGyroData.csv"
            df = pd.read_csv(csv_file_RawAccelGyroData, header=None, sep=' ', skiprows=10)
            df = df.drop(df.columns[[1, 5]], axis=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(
                columns={0: 'GPS_Time', 1: 'Drone_Time', 2: 'accel_X', 3: 'accel_Y', 4: 'accel_Z', 6: 'gyro_X',
                         7: 'gyro_Y', 8: 'gyro_Z'})
            df.to_csv(csv_file_RawAccelGyroData, index=False)
            return True
        except Exception as e:
            os.remove(csv_file_RawAccelGyroData)
            print('No RawAccelGyroData')
            return False

    def process_pyro_board_state(self, coefficients: np.ndarray, polynomial: np.poly1d) -> bool:
        """Обработка PyroBoardState.csv"""
        try:
            csv_file_PyroBoardState = self.arg + "_PyroBoardState.csv"
            df = pd.read_csv(csv_file_PyroBoardState, header=None, sep=' ', skiprows=1)
            df[1] = df[0].copy()
            df[0] = df[0].apply(lambda x: self.convert_time(x, coefficients, polynomial))
            df = df.rename(columns={0: 'GPS_Time', 2: 'channel_1', 3: 'channel_2', 4: 'channel_3', 5: 'channel_4',
                                    1: 'Drone_Time'})
            df.to_csv(csv_file_PyroBoardState, index=False)
            return True
        except Exception as e:
            print('No PyroBoardState')
            os.remove(csv_file_PyroBoardState)
            return False

    def move_csv_files_to_result(self):
        """Перемещение CSV файлов в папку Result_CSV"""
        for csvfile in glob.glob('*.csv'):
            if os.path.getsize(csvfile) > 0:
                os.rename(csvfile, 'Result_CSV/' + csvfile)
            else:
                os.remove(csvfile)

    def process_all(self):
        """Основной метод обработки всех данных"""
        print(self.arg)

        # Парсинг бинарного файла
        if not self.parser():
            return False

        # Обработка TimeDelta
        try:
            csv_file_time = self.arg + "_TimeDelta.csv"
            self.coefficients, self.polynomial = self.parser_time(csv_file_time)
            if self.coefficients is None or self.polynomial is None:
                print('No TimeDelta data')
                return False
        except Exception as e:
            print('No TimeDelta')
            return False

        # Обработка всех CSV файлов
        processing_methods = [
            self.process_nav_altitude,
            self.process_bar_altitude,
            self.process_nav_sat_info,
            self.process_nav_precision,
            self.process_rssi,
            self.process_led_board_data,
            self.process_int_power_status,
            self.process_ext_power_status,
            self.process_nav_velocity,
            self.process_event_log,
            self.process_uav_mode,
            self.process_orientation,
            self.process_motor,
            self.process_raw_accel_gyro_data,
            self.process_pyro_board_state
        ]

        for method in processing_methods:
            method(self.coefficients, self.polynomial)

        # Перемещение файлов в Result_CSV
        self.move_csv_files_to_result()

        return True


def main():
    """Основная функция"""
    files = glob.glob('*.bin')
    for bin_file in files:
        parser = BinParser(bin_file)
        parser.process_all()


if __name__ == "__main__":
    main()