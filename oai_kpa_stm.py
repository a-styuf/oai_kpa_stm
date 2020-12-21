import json

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import time
import os
import re
import oia_kpa_stm_data
import oai_kpa_stm_widget_qt


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
        # отслеживание состояния окна
        self.state = 0

        # # Изменяемая часть окна # #
        self.moduleSerialNumberLEdit.setText(self.cfg["core"]["serial_num"])
        # Часть под правку: здесь вы инициализируете необходимые компоненты
        self.module = oia_kpa_stm_data.OaiKpaSTM(serial_num=self.cfg["core"]["serial_num"])
        # the table for stm_channels data visualisation
        self.stm_color_map = {0: "darkturquoise", 1: "darkseagreen", 2: "lightcoral"}
        self.stm_table_column, self.stm_table_row = 4, 8
        self.table_values = [[{"voltage": 0.0, "color": "gray"}for i in range(self.stm_table_row)]
                             for j in range(self.stm_table_column)]
        # Таймер для создания всевдопотока для обновления GUI и сохранения данных в лог
        self.data_update_timer = QtCore.QTimer()
        self.data_update_timer.timeout.connect(self.update_data)
        self.data_update_timer.start(500)
        # Кнопки для управления модулем
        self.singleReadPushButton.clicked.connect(self.fill_table_data_from_stm_data)
        self.cycleReadPushButton.clicked.connect(self.cycle_reading)
        self.cycle_reading_flag = False
        self.cycleReadPushButton.setStyleSheet('QLineEdit {background-color: %s;}' % "lightgray")


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

    def connection_state_check(self):
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
        self.statusLineEdit.setText(str(string))
        self.statusLineEdit.setStyleSheet('QLineEdit {background-color: %s;}' % color)

    def connect(self):
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
        self.module.disconnect()
        self.connection_state_check()
        pass

    def reconnect(self):
        self.disconnect()
        self.connect()
        self.connection_state_check()
        pass

    def update_data(self):
        #
        if self.cycle_reading_flag:
            self.fill_table_data_from_stm_data()
        pass

    def cycle_reading(self):
        if self.cycle_reading_flag:
            self.cycle_reading_flag = False
            color = "lightgray"
        else:
            self.cycle_reading_flag = True
            color = "darkseagreen"
        self.cycleReadPushButton.setStyleSheet('QPushButton {background-color: %s;}' % color)
        pass

    def fill_table_data_from_stm_data(self):
        try:
            if self.module.state == 1:
                for column in range(self.stm_table_column):
                    for row in range(self.stm_table_row):
                        adc_num, ch_num = column // 2, row + self.stm_table_row*(column % 2)
                        value, state = self.module.get_channel_values(adc_num, ch_num)
                        self.__fill_single_socket(self.stmTableWidget, row, 2*column+1, value,
                                                  color=self.stm_color_map.get(state, "white"))
                        name = self.cfg["user"]["channels"][str(adc_num*16 + ch_num)]
                        self.__fill_single_socket(self.stmTableWidget, row, 2*column, name,
                                                  color="white")
            else:
                pass
        except Exception as error:
            print("fill_table_data ", error)

    @staticmethod
    def __fill_single_socket(table, row, column, value, color=None):
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

    def closeEvent(self, event):
        self.save_cfg()
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)
    w = ClientGUIWindow(uniq_name="oai_kpa_stm", widget='False')
    w.show()
    sys.exit(app.exec_())
