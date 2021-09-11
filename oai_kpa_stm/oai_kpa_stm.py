# -*- coding: utf-8 -*-

# модули GUI
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
# стандартные модули для работы
import time
import os
import re
import json
# модули ОАИ_КПА
try:
    from . import oai_kpa_stm_widget_qt
    from . import oia_kpa_stm_data
except Exception as ex:
    import oai_kpa_stm_widget_qt
    import oia_kpa_stm_data


class ClientGUIWindow(QtWidgets.QWidget, oai_kpa_stm_widget_qt.Ui_Form):
    def __init__(self, *args, **kwargs):
        # # Стандартная часть окна # #
        # обязательная часть для запуска Qt-виджета
        super().__init__()
        self.setupUi(self)
        # создание и обработка словаря настройки (здесь же обрабатывается параметры **kwargs)
        self.uniq_name = kwargs.get("uniq_name", 'oai_kpa_stm_un')
        # настройки по умолчанию
        # настройки не для изменения (одинаковые для каждого типа плат)
        self.core_cfg = {'serial_num': '20713699424D',
                         'widget': True}
        # настройки для вашего модуля (разные для каждого типа плат)
        self.channels_default_parameters = {num: "АЦП %d К %d" % (num//16, num%16)
                                            for num in range(32)}
        self.user_cfg = {"channels": self.channels_default_parameters}
        self.default_cfg = {'core': self.core_cfg,
                            'user': self.user_cfg
                            }
        #
        self.loaded_cfg = self.load_cfg()
        self.cfg = self.cfg_process(self.loaded_cfg, kwargs)
        # скрываем ненужные элементы
        if self.cfg["core"]["widget"] is str(True):
            self.connectionPButton.hide()
        # описываем элементы стандартного окна
        self.connectionPButton.clicked.connect(self.reconnect)
        # переменные для создание лога
        self.log_file_title = self.generate_log_title()
        self.log_file_data = ["0" for i in range(len(self.log_file_title))]
        self.log_file = None
        self.recreate_log_files()
        # отслеживание состояния окна
        self.state = 0
        # настройки отображения и сохранения в лог
        self.gui_update_time_ms = 1000
        self.log_update_time_ms = 1000
        # Таймер для создания псевдопотока для обновления GUI
        self.data_update_timer = QtCore.QTimer()
        self.data_update_timer.timeout.connect(self.update_gui)
        self.data_update_timer.start(self.gui_update_time_ms)
        # Таймер для создания псевдопотока для сохранения данных в лог
        self.log_update_timer = QtCore.QTimer()
        self.log_update_timer.timeout.connect(self.log_write)
        self.log_update_timer.start(self.log_update_time_ms)
        # # Изменяемая часть окна # #
        self.moduleSerialNumberLEdit.setText(self.cfg["core"]["serial_num"])
        # Часть под правку: здесь вы инициализируете необходимые компоненты
        self.module = oia_kpa_stm_data.OaiKpaSTM(serial_num=self.cfg["core"]["serial_num"])
        # the table for stm_channels data visualisation
        self.stm_color_map = {0: "darkturquoise", 1: "darkseagreen", 2: "lightcoral"}
        self.stm_table_column, self.stm_table_row = 4, 8
        self.table_values = [[{"voltage": 0.0, "color": "gray"}for i in range(self.stm_table_row)]
                             for j in range(self.stm_table_column)]

    def connection_state_check(self):
        """
        The useful method to generate correct status string with color
        """
        if self.module.state == -2:
            self.set_status_string(string="Ошибка подключения", color="lightcoral")
        elif self.module.state == -1:
            self.set_status_string(string="Ошибка подключения", color="orangered")
        elif self.module.state == 0:
            self.set_status_string(string="Необходимо подключение", color="white")
        elif self.module.state == 1:
            self.set_status_string(string="Подключение успешно", color="darkseagreen")
        else:
            self.set_status_string(string="Подключение успешно", color="white")
        pass

    def set_status_string(self, string="Нет информации", color="white"):
        """
        setting string and color to gui output status-line
        :param string: string to GUI-output
        :param color: background color
        """
        self.statusLineEdit.setText(str(string))
        self.statusLineEdit.setStyleSheet('QLineEdit {background-color: %s;}' % color)

    def connect(self):
        """
        connection to kpa-module
        :return: nothing
        """
        serial_number = self.moduleSerialNumberLEdit.text()
        if re.findall(r"[0-9a-fA-F]{8,12}", serial_number):
            self.cfg["core"]["serial_num"] = serial_number
        else:
            serial_number = self.serial_number
            self.moduleSerialNumberLEdit.setText(self.cfg["core"]["serial_num"])
        self.module.connect(serial_num=serial_number)
        self.connection_state_check()
        #
        self.save_cfg()
        pass

    def disconnect(self):
        """
        disconnect from kpa_module, if connection is established; in other cases do nothing
        :return: nothing
        """
        self.module.disconnect()
        self.connection_state_check()
        pass

    def reconnect(self):
        """
        reconnect module
        :return: nothing
        """
        self.disconnect()
        self.connect()
        self.connection_state_check()
        pass

    def update_gui(self):
        """
        the function, that update gui data output parts (table, etc). Run each <gui_update_time_ms>.
        :return: nothing
        """
        self.fill_table_data_from_stm_data()
        pass

    def fill_table_data_from_stm_data(self):
        """
        filling the stm-table
        :return:
        """
        try:
            if self.module.state == 1:
                value_list, state_list = self.module.get_channels_values()
                for column in range(self.stm_table_column):
                    for row in range(self.stm_table_row):
                        adc_num, ch_num = column // 2, row + self.stm_table_row*(column % 2)
                        # print(adc_num, ch_num, column, row)
                        # value, state = self.module.get_channel_values(adc_num, ch_num)
                        value, state = value_list[adc_num*16 + ch_num], state_list[adc_num*16 + ch_num]
                        self.__fill_single_socket(self.stmTableWidget, row, 2*column+1, value,
                                                  color=self.stm_color_map.get(state, "white"))
                        name = self.cfg["user"]["channels"][str(adc_num*16 + ch_num)]
                        self.__fill_single_socket(self.stmTableWidget, row, 2*column, name,
                                                  color="white")
            else:
                pass
        except Exception as error:
            # print("fill_table_data ", error)
            pass

    @staticmethod
    def __fill_single_socket(table, row, column, value, color=None):
        """
        fill the socket of table by value and color
        :param table: the table for filling
        :param row: the table row of item for filling
        :param column: the table column of item for filling
        :param value: value to put in table socket
        :param color: color of table item
        :return: nothing
        """
        if type(value) == str:
            table_item = QtWidgets.QTableWidgetItem(value)
        elif type(value) == float:
            table_item = QtWidgets.QTableWidgetItem("%.3f V" % value)
        else:
            table_item = QtWidgets.QTableWidgetItem("%s" % value)
        table_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if color:
            table_item.setBackground(QtGui.QColor(color))
        table.setItem(row, column, table_item)
        pass

    # работа с файлом конфигурации
    @staticmethod
    def cfg_process(default_cfg, new_cfg):
        """
        Process default and new cfg-s and forms actual cfg
        :param default_cfg: default parameters set
        :param new_cfg: cfg to update
        :return: actual_cfg
        """
        cfg = default_cfg
        for key, value in new_cfg.items():
            for c_key, c_value in default_cfg["core"].items():
                if c_key == key:
                    cfg["core"][key] = value
            for c_key, c_value in default_cfg["user"].items():
                if c_key == key:
                    cfg["user"][key] = value
        return cfg

    def save_cfg(self):
        try:
            os.mkdir("cfg")
        except OSError as error:
            pass
        #
        with open("cfg\\" + self.uniq_name + ".json", 'w', encoding="utf-8") as cfg_file:
            json.dump(self.cfg, cfg_file, sort_keys=True, indent=4, ensure_ascii=False)

    def save_default_cfg(self):
        try:
            os.mkdir("cfg")
        except OSError as error:
            pass
        #
        with open("cfg\\" + self.uniq_name + ".json", 'w', encoding="utf-8") as cfg_file:
            json.dump(self.default_cfg, cfg_file, sort_keys=True, indent=4, ensure_ascii=False)

    def load_cfg(self):
        try:
            with open("cfg\\" + self.uniq_name + ".json", 'r', encoding="utf-8") as cfg_file:
                loaded_cfg = json.load(cfg_file)
        except FileNotFoundError:
            loaded_cfg = self.default_cfg
        return loaded_cfg

    # работа с log-файлом
    @staticmethod
    def create_log_file(file=None, dir_name="log", sub_dir="log", sub_sub_dir=True, prefix="", extension=".csv"):
        """
        log-file creation
        :param file: if log-file already created, it will be closed
        :param dir_name: the folder, where logs will be stored
        :param sub_dir: the postfix for time_date (%Y_%m_%d_<sub_dir>) sub_dir_name
        :param sub_sub_dir: if True in sub_dir the log-files will be placed in additional folder (%Y_%m_%d_%H-%M-%S_<sub_dir>)
        :param prefix: the file-name prefix ("%Y_%m_%d %H-%M-%S <prefix> <extension>)
        :param extension: the file-name extension ("%Y_%m_%d %H-%M-%S <prefix> <extension>)
        :return: lof_file handle
        """
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d", time.localtime()) + " " + sub_dir
        if sub_sub_dir:
            sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                                   time.localtime()) + sub_dir
        else:
            sub_sub_dir_name = sub_dir_name
        try:
            os.makedirs(sub_sub_dir_name)
        except (OSError, AttributeError) as error:
            print(error)
            pass
        try:
            if file:
                file.close()
        except (OSError, NameError, AttributeError) as error:
            print(error)
            pass
        file_name = sub_sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                            time.localtime()) + prefix + " " + extension
        file = open(file_name, 'a', encoding="utf-8")
        return file

    @staticmethod
    def close_log_file(file=None):
        """
        closing lo-file, if it possible; in other cases does nothing
        :param file: file to close
        """
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                print(error)
            finally:
                file = None
        pass

    def recreate_log_files(self):
        """
        log-file recreation
        """
        # перезапуск лог файла
        self.log_file = self.create_log_file(file=self.log_file, dir_name="log", sub_dir=self.uniq_name,
                                             sub_sub_dir=False, prefix=self.uniq_name, extension=".csv")
        self.log_file.write(self.log_file_title)
        pass

    def generate_log_title(self):
        """
        log-file title list generation
        :return: title list for log-file
        """
        # обязательная часть - время в формате с.мс
        log_title = ["Time, s"]
        # список данных, генерируемых модулем
        data_title_list = [self.cfg["user"]["channels"].get(str(i), str(i)) for i in range(32)]
        #
        log_title.extend(data_title_list)
        return u";".join(log_title) + "\n"

    def generate_log_data(self):
        """
        log-file data list generation
        :return: data list for log-file
        """
        # обязательная часть - время в формате с.мс
        log_title = [u"%.3f" % time.perf_counter()]
        # список данных, генерируемых модулем
        data_title_list = [u"%.3f" % value for value in self.module.get_channels_values()[0]]
        #
        log_title.extend(data_title_list)
        return ";".join(log_title) + '\n'

    def log_write(self):
        """
        function, witch rerun every log_update_time_ms, to write data to log
        :return: nothing
        """
        log_data = self.generate_log_data()
        if log_data:
            self.log_file.write(log_data)
        pass

    # обработка события закрытия окна
    def closeEvent(self, event):
        self.save_cfg()
        pass