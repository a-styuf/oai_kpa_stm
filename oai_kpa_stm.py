from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import time
import os
import re
import oia_kpa_stm_data
import oai_kpa_stm_widget


class ClientGUIWindow(QtWidgets.QWidget, oai_kpa_stm_widget.Ui_Form):
    def __init__(self, *args, **kwargs):
        # # Стандартная часть окна # #
        # обязательная часть для запуска виджета
        super().__init__()
        self.setupUi(self)
        # достаем неименованные переменные из *args
        # достаем именованные переменные из **kwargs
        self.serial_number = kwargs.get('serial_num', '20713699424D')
        self.widget_mode = kwargs.get('widget', True)
        # отслеживание состояния окна
        self.state = 0
        # # Изменяемая часть окна # #
        self.moduleSerialNumberLEdit.setText(self.serial_number)
        # Часть под правку: здесь вы инициализируете необходимые компоненты
        self.module = oia_kpa_stm_data.OaiKpaSTM(serial_num=self.serial_number)
        # the table for stm_channels data visualisation
        self.stm_color_map = {0: "darkturquoise", 1: "darkseagreen", 2: "lightcoral"}
        self.stm_table_column, self.stm_table_row = 4, 8
        self.table_values = [[{"voltage": 0.0, "color": "gray"}for i in range(self.stm_table_row)]
                             for j in range(self.stm_table_column)]
        #
        self.data_update_timer = QtCore.QTimer()
        self.data_update_timer.timeout.connect(self.update_data)
        self.data_update_timer.start(1000)
        #
        self.singleReadPushButton.clicked.connect(self.fill_table_data_from_stm_data)
        self.cycleReadPushButton.clicked.connect(self.cycle_reading)
        self.cycle_reading_flag = False
        self.cycleReadPushButton.setStyleSheet('QLineEdit {background-color: %s;}' % "lightgray")
        # описываем элементы стандартного окна
        self.connectionPButton.clicked.connect(self.reconnect)

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
            self.serial_number = serial_number
        else:
            serial_number = self.serial_number
            self.moduleSerialNumberLEdit.setText(self.serial_number)
        self.module.connect(serial_num=serial_number)
        self.connection_state_check()
        pass

    def disconnect(self):
        self.module.disconnect()
        self.connection_state_check()
        pass

    def reconnect(self, serial_num=None):
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
                        self.__fill_single_socket(self.stmTableWidget, row, column, value,
                                                  color=self.stm_color_map.get(state, "white"))
            else:
                pass
        except Exception as error:
            print("fill_table_data ", error)

    @staticmethod
    def __fill_single_socket(table, row, column, value, color=None):
        table_item = QtWidgets.QTableWidgetItem("%.3f V" % value)
        table_item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if color:
            table_item.setBackground(QtGui.QColor(color))
        table.setItem(row, column, table_item)
        pass

    def closeEvent(self, event):
        #
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    app = QtWidgets.QApplication(sys.argv)
    w = ClientGUIWindow(widget='False')
    w.show()
    sys.exit(app.exec_())
