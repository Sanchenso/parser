import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta, datetime
import matplotlib.ticker as ticker
import logging
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PlotParserResult:
    """Класс для построения графиков из результатов парсинга"""
    
    def __init__(self, expansion: str = '.bin'):
        self.path = "Result_CSV"
        self.expansion = expansion
        self.files_in_path = os.listdir(self.path)
        
        # Создание директории Result_Picture если не существует
        if not os.path.exists('Result_Picture'):
            os.makedirs('Result_Picture')
    
    @staticmethod
    def parse_multiple_formats(date_str: str) -> datetime:
        """Определение функции для парсинга нескольких форматов даты и времени"""
        formats = ["%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", 
                  "%Y/%m/%d %H:%M:%S", "%H:%M:%S.%f"] 
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        print(f"Не удалось преобразовать: {date_str}")
        return pd.NaT

    def process_binfile(self, binfile: str):
        """Обработка одного бинарного файла и построение графиков"""
        print(binfile)
        prefix = binfile[:-4]
        files_with_prefix = [file for file in self.files_in_path if file.startswith(prefix)]
        
        # Инициализация DataFrame (сохранены оригинальные имена)
        dataframes = []
        dfGGA = pd.DataFrame()
        dfGPSL1 = pd.DataFrame()
        dfBeiDouL1 = pd.DataFrame()
        dfAltitude = pd.DataFrame()
        dfNavVelocity = pd.DataFrame()
        dfPrecision = pd.DataFrame()
        flagRMC = 0
        
        # Чтение и обработка CSV файлов
        for i in files_with_prefix:
            if '_GGA.csv' in i:
                dfGGA = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfGGA['GPS_Time'] = dfGGA['GPS_Time'].apply(self.parse_multiple_formats)
                first_altitude = dfGGA['Altitude'].iloc[0]
                dfGGA['Altitude'] = dfGGA['Altitude'].apply(lambda x: x - first_altitude)
                if not dfGGA.empty:
                    dataframes.append(dfGGA)
                    
            if '_GPS_L1CA_L1_SNR.csv' in i:
                dfGPSL1 = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfGPSL1['GPS_Time'] = dfGPSL1['GPS_Time'].apply(self.parse_multiple_formats)
                if not dfGPSL1.empty:
                    dataframes.append(dfGPSL1)
                    
            if 'BeiDou_B1I_L1_SNR.csv' in i:
                dfBeiDouL1 = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfBeiDouL1['GPS_Time'] = dfBeiDouL1['GPS_Time'].apply(self.parse_multiple_formats)
                if not dfBeiDouL1.empty:
                    dataframes.append(dfBeiDouL1)
                    
            if '_BarAltitude.csv' in i and os.path.getsize(os.path.join(self.path, i)) > 100:
                dfAltitude = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfAltitude['GPS_Time'] = dfAltitude['GPS_Time'].apply(self.parse_multiple_formats)
                first_altitude = dfAltitude['BarAltitude'].iloc[0]
                dfAltitude['BarAltitude'] = dfAltitude['BarAltitude'].apply(lambda x: x - first_altitude)
                if not dfAltitude.empty:
                    dataframes.append(dfAltitude)
                    
            if '_RMC.csv' in i:
                flagRMC = 1
                dfRMC = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfRMC['GPS_Time'] = dfRMC['GPS_Time'].apply(self.parse_multiple_formats)
                dfRMC['mode_indicator'] = dfRMC['mode_indicator'].fillna('')
                
            if '_NavPrecision.csv' in i:
                dfPrecision = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfPrecision['GPS_Time'] = dfPrecision['GPS_Time'].apply(self.parse_multiple_formats)
                dfPrecision['hAccuracy'] = dfPrecision['hAccuracy'] / 1000
                dfPrecision['vAccuracy'] = dfPrecision['vAccuracy'] / 1000
                
            if '_NavSatInfo.csv' in i:
                dfNavSatInfo = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfNavSatInfo['GPS_Time'] = dfNavSatInfo['GPS_Time'].apply(self.parse_multiple_formats)
                
            if '_NavVelocity.csv' in i:
                dfNavVelocity = pd.read_csv(os.path.join(self.path, i), header=0, sep=',', skiprows=0)
                dfNavVelocity['GPS_Time'] = dfNavVelocity['GPS_Time'].apply(self.parse_multiple_formats)
        
        # Определение временного диапазона
        if dataframes:
            for df in dataframes:
                if not df.empty:
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
            min_time = min(df.iloc[:, 0].min() for df in dataframes) - timedelta(seconds=5)
            max_time = max(df.iloc[:, 0].max() for df in dataframes) + timedelta(seconds=5)
            print(min_time.strftime("%H:%M:%S"), max_time.strftime("%H:%M:%S"))
        else:
            print('no dfAltitude')
            return
        
        # Построение графиков
        fig = plt.figure(figsize=(20, 10))
        fig.suptitle(binfile[:-4], x=0.5, y=0.95, verticalalignment='top')
        time_format = mdates.DateFormatter('%H:%M:%S')
        
        # График 1: SNR
        ax1 = fig.add_subplot(3, 2, 1)
        ax1.set_title('SNR GPS L1, NMEA GSV', fontsize=9)
        
        for column in dfGPSL1.columns[1:]:
            ax1.scatter(dfGPSL1['GPS_Time'], dfGPSL1[column], s=2)
            ax1.plot(dfGPSL1['GPS_Time'], dfGPSL1[column], linewidth=0.2)
            
        if not dfGPSL1.empty:
            sumSNR_gps = dfGPSL1.iloc[:, 1:].sum().sum()
            countSNR_gps = dfGPSL1.iloc[:, 1:].count().sum()
            avgSNR_gps = round(float(sumSNR_gps) / float(countSNR_gps), 1)
            ax1.text(0.01, 0.98, f'     GPS L1: {avgSNR_gps} dBHz', fontsize=10, 
                    transform=ax1.transAxes, verticalalignment='top')
                    
        ax1.set_ylim(10, 60)
        ax1.yaxis.set_major_locator(ticker.MultipleLocator(10))
        if not dfAltitude.empty:
            ax1.set_xlim(min_time, max_time)
        ax1.set_ylabel('SNR, dBHz')
        ax1.grid(color='black', linestyle='--', linewidth=0.2)
        ax1.xaxis.set_major_formatter(time_format)
        
        # График 2: RTK age
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
        
        # График 3: Altitude
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
            
        # График 4: Status
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
        
        # График 5: Precision или HDOP
        ax5 = fig.add_subplot(3, 2, 6)
        if not dfPrecision.empty:
            ax5.set_title('Precision, NavAUTO', fontsize=9)
            if not dfAltitude.empty:
                ax5.set_xlim(min_time, max_time)
            ax5.plot(dfPrecision['GPS_Time'], dfPrecision['vAccuracy'], label='vAccuracy')
            ax5.plot(dfPrecision['GPS_Time'], dfPrecision['hAccuracy'], label='hAccuracy')
            ax5.set_ylabel('Precision, m')
            ax5.set_ylim(0, 8)
            ax5.xaxis.set_major_formatter(time_format)
            ax5.grid(color='black', linestyle='--', linewidth=0.2)
            ax5.legend(bbox_to_anchor=(1, 0.75), loc="lower left")
            ax5.set_xlabel('Time')
        elif not dfGGA.empty:
            ax5.set_title('HDOP, NMEA GGA', fontsize=9)
            ax5.plot(dfGGA['GPS_Time'], dfGGA['HDOP'], label='HDOP')
            ax5.set_ylabel('HDOP')
            ax5.xaxis.set_major_formatter(time_format)
            ax5.grid(color='black', linestyle='--', linewidth=0.2)
            ax5.legend(bbox_to_anchor=(1, 1), loc="upper left")
        
        # График 6: Velocity
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
        
        # Сохранение графика
        plt.savefig('Result_Picture/' + binfile[:-4] + '.jpeg', dpi=200)
        plt.close(fig)

    def run(self):
        """Основной метод обработки всех файлов"""
        for binfile in os.listdir():
            if binfile[-4:] == self.expansion:
                self.process_binfile(binfile)


def main():
    """Основная функция"""
    expansion = (sys.argv[1]) if len(sys.argv) > 1 else '.bin'
    plotter = PlotParserResult(expansion)
    plotter.run()


if __name__ == "__main__":
    main()
